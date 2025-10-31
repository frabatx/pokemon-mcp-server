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
from .register import register_tool, ToolNames, ToolArguments, ToolResult


def calculate_similarity(reference_stats: pd.Series, compare_stats: pd.Series) -> float:
    """
    Calcola similarity score usando distanza euclidea normalizzata.
    Score 1.0 = identico, 0.0 = completamente diverso
    """
    stats_cols = ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]

    # Estrai vettori stats
    ref_vector = reference_stats[stats_cols].values.astype(float)
    comp_vector = compare_stats[stats_cols].values.astype(float)

    # Calcola distanza euclidea
    distance = np.linalg.norm(ref_vector - comp_vector)

    # Normalizza: max distanza possibile in questo spazio è ~sqrt(6 * 255^2) ≈ 625
    # Convertiamo in similarity score (1 - normalized_distance)
    max_distance = 625  # Approssimazione
    normalized_distance = min(distance / max_distance, 1.0)

    similarity = 1.0 - normalized_distance
    return similarity


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
    Trova Pokemon simili per stat spread.
    """
    pokemon_name = arguments.get("pokemon_name", "")
    limit = arguments.get("limit", 5)
    min_similarity = arguments.get("min_similarity", 0.7)

    # Trova Pokemon di riferimento
    pokemon_name_lower = pokemon_name.lower()
    reference = df[df["name"].str.lower() == pokemon_name_lower]

    if reference.empty:
        return [
            TextContent(type="text", text=f"❌ Pokemon '{pokemon_name}' not found.")
        ]

    reference = reference.iloc[0]

    # Calcola similarity per tutti gli altri Pokemon
    similarities = []
    for idx, row in df.iterrows():
        # Escludi il Pokemon stesso
        if row["name"].lower() == pokemon_name_lower:
            continue

        similarity = calculate_similarity(reference, row)

        if similarity >= min_similarity:
            similarities.append(
                {
                    "name": row["name"],
                    "similarity": similarity,
                    "stats": {
                        "hp": int(row["hp"]),
                        "attack": int(row["attack"]),
                        "defense": int(row["defense"]),
                        "sp_attack": int(row["sp_attack"]),
                        "sp_defense": int(row["sp_defense"]),
                        "speed": int(row["speed"]),
                    },
                    "base_total": int(row["base_total"]),
                    "types": f"{row['type1'].capitalize()}{f'/{row['type2'].capitalize()}' if pd.notna(row.get('type2')) else ''}",
                }
            )

    # Ordina per similarity
    similarities.sort(key=lambda x: x["similarity"], reverse=True)
    similarities = similarities[:limit]

    if not similarities:
        return [
            TextContent(
                type="text",
                text=f"❌ No similar Pokemon found with similarity >= {min_similarity}.",
            )
        ]

    # Formatta output
    ref_stats = f"HP {int(reference['hp'])} | Atk {int(reference['attack'])} | Def {int(reference['defense'])} | SpA {int(reference['sp_attack'])} | SpD {int(reference['sp_defense'])} | Spe {int(reference['speed'])}"

    result_lines = [
        f"## Pokemon Similar to {reference['name']}",
        f"\n**Reference Stats**: {ref_stats}",
        f"**Base Total**: {int(reference['base_total'])}\n",
        f"### Most Similar Pokemon:\n",
    ]

    for sim in similarities:
        sim_stats = f"HP {sim['stats']['hp']} | Atk {sim['stats']['attack']} | Def {sim['stats']['defense']} | SpA {sim['stats']['sp_attack']} | SpD {sim['stats']['sp_defense']} | Spe {sim['stats']['speed']}"

        result_lines.append(
            f"**{sim['name']}** - Similarity: {sim['similarity']:.2f}\n"
            f"  - Type: {sim['types']}\n"
            f"  - Stats: {sim_stats}\n"
            f"  - BST: {sim['base_total']}\n"
        )

    return [TextContent(type="text", text="\n".join(result_lines))]
