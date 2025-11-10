"""
Tool: find_pokemon_resistant_to_types

Query inversa: trova Pokemon che resistono a una lista di tipi specificati.

Questo tool:
- Filtra Pokemon che resistono a TUTTI i tipi nella lista
- Legge colonne against_{type}
- Considera "resistente" = multiplier <= 0.5
- Ordina per "resistance score" (media dei multipliers)

NON fa:
- Suggerimenti su quale Pokemon usare per il team (lavoro LLM)
- Analisi di movepool o abilities
- Team building completo

Input:
    resist_types: Lista di tipi a cui deve resistere (AND logic)
    min_resistance: Threshold per considerare "resistente" (default 0.5)
    limit: Numero risultati

Output:
    Pokemon che resistono a TUTTI i tipi specificati
"""

from mcp.types import TextContent
import pandas as pd
from .register import register_tool, ToolNames, ToolArguments, ToolResult
from utils.pokemon_helper import (
    format_types,
    safe_int,
    tool_error,
    tool_empty_result,
    calculate_resistance_scores_vectorized,
)


@register_tool(
    name=ToolNames.FIND_POKEMON_RESISTANT_TO_TYPES,
    description=(
        "Find Pokemon that resist specific types (damage multiplier <= threshold). "
        "Uses AND logic: Pokemon must resist ALL specified types. Returns Pokemon sorted "
        "by average resistance score."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "resist_types": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of types the Pokemon must resist (e.g., ['fire', 'ice'])",
                "minItems": 1,
            },
            "max_multiplier": {
                "type": "number",
                "description": "Maximum damage multiplier to consider 'resistant' (default 0.5)",
                "default": 0.5,
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 20,
            },
        },
        "required": ["resist_types"],
    },
)
async def find_pokemon_resistant_to_types(
    arguments: ToolArguments, df: pd.DataFrame
) -> ToolResult:
    """
    Trova Pokemon resistenti a tipi specifici.
    OTTIMIZZATO: usa boolean mask e calcoli vettorizzati invece di loop.
    """
    resist_types = arguments.get("resist_types", [])
    max_multiplier = arguments.get("max_multiplier", 0.5)
    limit = arguments.get("limit", 20)

    if not resist_types:
        return tool_error("Please specify at least one type to resist.")

    # Normalizza tipi
    resist_types_lower = [t.lower() for t in resist_types]

    # Verifica che le colonne esistano
    type_cols = [f"against_{t}" for t in resist_types_lower]
    missing_cols = [
        t for t, col in zip(resist_types_lower, type_cols) if col not in df.columns
    ]

    if missing_cols:
        return tool_error(f"Invalid types: {', '.join(missing_cols)}")

    # OTTIMIZZAZIONE: usa boolean mask invece di filtering sequenziale
    mask = pd.Series(True, index=df.index)
    for col in type_cols:
        mask &= df[col] <= max_multiplier

    filtered_df = df[mask].copy()

    if filtered_df.empty:
        types_str = ", ".join([t.capitalize() for t in resist_types_lower])
        return tool_empty_result(
            f"Pokemon resistant to all of: {types_str} (with multiplier <= {max_multiplier})"
        )

    # OTTIMIZZAZIONE: calcola resistance scores in modo vettorizzato
    filtered_df["resistance_score"] = calculate_resistance_scores_vectorized(
        filtered_df, type_cols
    )

    # Ordina e limita risultati
    filtered_df = filtered_df.sort_values("resistance_score").head(limit)

    # Formatta output
    types_str = ", ".join([t.capitalize() for t in resist_types_lower])

    result_lines = [
        f"## Pokemon Resistant to {types_str}",
        f"\n**Criteria**: All types must have damage multiplier <= {max_multiplier}",
        f"**Found**: {len(filtered_df)} Pokemon\n",
    ]

    # OTTIMIZZAZIONE: usa to_dict('records') invece di iterrows
    for row in filtered_df.to_dict("records"):
        pokemon_types = format_types(row["type1"], row.get("type2"))

        # Mostra multipliers per ogni tipo
        resistances = []
        for t in resist_types_lower:
            mult = row[f"against_{t}"]
            resistances.append(f"{t.capitalize()} {mult}x")

        resistances_str = ", ".join(resistances)

        result_lines.append(
            f"**{row['name']}** ({pokemon_types})\n"
            f"  - Resistances: {resistances_str}\n"
            f"  - Avg Multiplier: {row['resistance_score']:.2f}\n"
            f"  - BST: {safe_int(row['base_total'])}\n"
        )

    return [TextContent(type="text", text="\n".join(result_lines))]
