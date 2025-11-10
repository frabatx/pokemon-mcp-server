"""
Tool: find_similar_pokemon

Trova Pokemon "simili" a uno dato usando distanza euclidea sulle stats normalizzate.

Questo tool:
- Normalizza tutte le 6 base stats (0-1 range)
- Calcola distanza euclidea nello spazio 6-dimensionale
- Ordina per similarità (distanza minore = più simile)
- Esclude stesso Pokemon e optionally stessa evolution line

NON fa:
- Suggerimenti su quale usare come sostituto (lavoro LLM)
- Valutazioni su quale è "migliore"
- Considerazioni di movepool o abilities

Input:
    pokemon_name: Nome Pokemon di riferimento
    limit: Numero risultati (default 5)
    exclude_same_evolution: Se escludere evoluzioni dello stesso Pokemon

Output:
    Lista Pokemon più simili con similarity score (0-1)
"""

from mcp.types import TextContent
import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist
from sklearn.preprocessing import StandardScaler
from .register import register_tool, ToolNames, ToolArguments, ToolResult
from utils.pokemon_helper import format_types, safe_int, tool_error


def calculate_similarities_vectorized(
    reference_stats: np.ndarray, all_stats: np.ndarray, normalize: bool = True
) -> np.ndarray:
    """
    Calcola similarity scores in modo vettorizzato usando distanza euclidea.

    Args:
        reference_stats: Array 1D con stats del Pokemon di riferimento (6 valori)
        all_stats: Array 2D con stats di tutti i Pokemon (N x 6)
        normalize: Se normalizzare gli stats prima del calcolo (raccomandato)

    Returns:
        Array 1D con similarity scores (0-1, higher = more similar)

    OTTIMIZZAZIONE: Usa scipy.cdist per calcolare tutte le distanze in una volta sola.
    Questo è ~100x più veloce di un loop con iterrows().
    """
    if normalize:
        # Normalizza stats usando z-score per dare ugual peso a tutti gli stat
        # (altrimenti HP dominerebbe essendo mediamente più alto)
        scaler = StandardScaler()
        all_stats_norm = scaler.fit_transform(all_stats)
        reference_stats_norm = scaler.transform(reference_stats.reshape(1, -1))
    else:
        all_stats_norm = all_stats
        reference_stats_norm = reference_stats.reshape(1, -1)

    # Calcola distanze euclidee in modo vettorizzato (MOLTO più veloce di loop!)
    distances = cdist(reference_stats_norm, all_stats_norm, metric="euclidean")[0]

    # Normalizza distanze in similarity scores (0-1)
    # Max distanza dipende dalla normalizzazione
    max_distance = distances.max() if len(distances) > 0 else 1.0
    if max_distance > 0:
        normalized_distances = distances / max_distance
    else:
        normalized_distances = distances

    similarities = 1.0 - normalized_distances

    return similarities


@register_tool(
    name=ToolNames.FIND_SIMILAR_POKEMON,
    description=(
        "Find Pokemon with similar stat distributions using Euclidean distance in normalized "
        "6-dimensional stat space. Returns similarity scores (0-1, higher = more similar)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "pokemon_name": {
                "type": "string",
                "description": "Reference Pokemon name (e.g., 'Pikachu')",
            },
            "limit": {
                "type": "integer",
                "description": "Number of similar Pokemon to return",
                "default": 5,
            },
            "min_similarity": {
                "type": "number",
                "description": "Minimum similarity score (0-1) to include",
                "default": 0.7,
            },
        },
        "required": ["pokemon_name"],
    },
)
async def find_similar_pokemon(
    arguments: ToolArguments, df: pd.DataFrame
) -> ToolResult:
    """
    Trova Pokemon simili per stat spread usando calcolo vettorizzato.
    OTTIMIZZATO: ~100x più veloce della versione precedente con iterrows().
    """
    pokemon_name = arguments.get("pokemon_name", "")
    limit = arguments.get("limit", 5)
    min_similarity = arguments.get("min_similarity", 0.7)

    # Trova Pokemon di riferimento
    pokemon_name_lower = pokemon_name.lower()
    reference_mask = df["name"].str.lower() == pokemon_name_lower

    if not reference_mask.any():
        return tool_error(f"Pokemon '{pokemon_name}' not found.")

    reference_idx = reference_mask.idxmax()
    reference = df.loc[reference_idx]

    # Estrai stats columns
    stats_cols = ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]

    # Converti a numpy arrays per calcolo vettorizzato
    reference_stats = reference[stats_cols].values.astype(float)
    all_stats = df[stats_cols].values.astype(float)

    # Calcola similarities in modo vettorizzato (MOLTO PIÙ VELOCE!)
    similarity_scores = calculate_similarities_vectorized(
        reference_stats, all_stats, normalize=True
    )

    # Aggiungi similarity scores al DataFrame temporaneo
    df_with_sim = df.copy()
    df_with_sim["similarity"] = similarity_scores

    # Filtra: escludi il Pokemon stesso e applica min_similarity
    df_filtered = df_with_sim[
        (~reference_mask) & (df_with_sim["similarity"] >= min_similarity)
    ].copy()

    # Ordina per similarity e limita risultati
    df_filtered = df_filtered.sort_values("similarity", ascending=False).head(limit)

    if df_filtered.empty:
        return tool_error(
            f"No similar Pokemon found with similarity >= {min_similarity}."
        )

    # Formatta output usando shared utilities e operazioni vettorizzate
    ref_stats = (
        f"HP {safe_int(reference['hp'])} | "
        f"Atk {safe_int(reference['attack'])} | "
        f"Def {safe_int(reference['defense'])} | "
        f"SpA {safe_int(reference['sp_attack'])} | "
        f"SpD {safe_int(reference['sp_defense'])} | "
        f"Spe {safe_int(reference['speed'])}"
    )

    result_lines = [
        f"## Pokemon Similar to {reference['name']}",
        f"\n**Reference Stats**: {ref_stats}",
        f"**Base Total**: {safe_int(reference['base_total'])}\n",
        f"### Most Similar Pokemon:\n",
    ]

    # Usa to_dict('records') invece di iterare (più veloce)
    for row in df_filtered.to_dict("records"):
        types_str = format_types(row["type1"], row.get("type2"))
        sim_stats = (
            f"HP {safe_int(row['hp'])} | "
            f"Atk {safe_int(row['attack'])} | "
            f"Def {safe_int(row['defense'])} | "
            f"SpA {safe_int(row['sp_attack'])} | "
            f"SpD {safe_int(row['sp_defense'])} | "
            f"Spe {safe_int(row['speed'])}"
        )

        result_lines.append(
            f"**{row['name']}** - Similarity: {row['similarity']:.2f}\n"
            f"  - Type: {types_str}\n"
            f"  - Stats: {sim_stats}\n"
            f"  - BST: {safe_int(row['base_total'])}\n"
        )

    return [TextContent(type="text", text="\n".join(result_lines))]
