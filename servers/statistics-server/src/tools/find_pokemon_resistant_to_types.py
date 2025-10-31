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
    """
    resist_types = arguments.get("resist_types", [])
    max_multiplier = arguments.get("max_multiplier", 0.5)
    limit = arguments.get("limit", 20)

    if not resist_types:
        return [
            TextContent(
                type="text", text="❌ Please specify at least one type to resist."
            )
        ]

    # Normalizza tipi
    resist_types_lower = [t.lower() for t in resist_types]

    # Verifica che le colonne esistano
    missing_cols = []
    for poke_type in resist_types_lower:
        col = f"against_{poke_type}"
        if col not in df.columns:
            missing_cols.append(poke_type)

    if missing_cols:
        return [
            TextContent(
                type="text", text=f"❌ Invalid types: {', '.join(missing_cols)}"
            )
        ]

    # Filtra Pokemon che resistono a TUTTI i tipi
    filtered_df = df.copy()

    for poke_type in resist_types_lower:
        col = f"against_{poke_type}"
        filtered_df = filtered_df[filtered_df[col] <= max_multiplier]

    if filtered_df.empty:
        types_str = ", ".join([t.capitalize() for t in resist_types_lower])
        return [
            TextContent(
                type="text",
                text=f"❌ No Pokemon found that resist all of: {types_str} (with multiplier <= {max_multiplier})",
            )
        ]

    # Calcola resistance score (media dei multipliers - più basso = meglio)
    resistance_scores = []
    for idx, row in filtered_df.iterrows():
        multipliers = [row[f"against_{t}"] for t in resist_types_lower]
        avg_multiplier = sum(multipliers) / len(multipliers)
        resistance_scores.append(avg_multiplier)

    filtered_df["resistance_score"] = resistance_scores
    filtered_df = filtered_df.sort_values("resistance_score").head(limit)

    # Formatta output
    types_str = ", ".join([t.capitalize() for t in resist_types_lower])

    result_lines = [
        f"## Pokemon Resistant to {types_str}",
        f"\n**Criteria**: All types must have damage multiplier <= {max_multiplier}",
        f"**Found**: {len(filtered_df)} Pokemon\n",
    ]

    for idx, row in filtered_df.iterrows():
        pokemon_types = row["type1"].capitalize()
        if pd.notna(row.get("type2")):
            pokemon_types += f"/{row['type2'].capitalize()}"

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
            f"  - BST: {int(row['base_total'])}\n"
        )

    return [TextContent(type="text", text="\n".join(result_lines))]
