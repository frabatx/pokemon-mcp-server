"""
Tool: get_pokemon_by_stat_range

Query per filtrare Pokemon che hanno una statistica specifica in un range di valori.

Questo tool:
- Filtra Pokemon con stat >= min_value (obbligatorio)
- Opzionalmente filtra anche con stat <= max_value
- Ordina per la stat specificata
- Limita numero risultati

NON fa:
- Suggerimenti su quali Pokemon scegliere per il team
- Analisi meta-game
- Valutazioni strategiche

Input:
    stat_name: Nome della statistica da filtrare
    min_value: Valore minimo (incluso)
    max_value: Valore massimo (incluso, opzionale)
    limit: Numero massimo risultati (default 20)

Output:
    Lista Pokemon ordinati che matchano i criteri
"""

from mcp.types import TextContent
import pandas as pd
from .register import register_tool, ToolNames, ToolArguments, ToolResult


@register_tool(
    name=ToolNames.GET_POKEMON_BY_STAT_RANGE,
    description=(
        "Filter Pokemon by a specific stat within a value range. Returns Pokemon with "
        "stat_name >= min_value (and optionally <= max_value), sorted by that stat."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "stat_name": {
                "type": "string",
                "description": "Stat to filter by",
                "enum": [
                    "hp",
                    "attack",
                    "defense",
                    "sp_attack",
                    "sp_defense",
                    "speed",
                    "base_total",
                ],
            },
            "min_value": {
                "type": "integer",
                "description": "Minimum value (inclusive)",
            },
            "max_value": {
                "type": "integer",
                "description": "Maximum value (inclusive, optional)",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 20,
            },
        },
        "required": ["stat_name", "min_value"],
    },
)
async def get_pokemon_by_stat_range(
    arguments: ToolArguments, df: pd.DataFrame
) -> ToolResult:
    """
    Filtra Pokemon per range di stat.
    """
    stat_name = arguments.get("stat_name", "base_total")
    min_value = arguments.get("min_value")
    max_value = arguments.get("max_value")
    limit = arguments.get("limit", 20)

    if stat_name not in df.columns:
        return [TextContent(type="text", text=f"❌ Stat '{stat_name}' not found.")]

    # Filtra
    filtered_df = df[df[stat_name] >= min_value].copy()

    if max_value is not None:
        filtered_df = filtered_df[filtered_df[stat_name] <= max_value]

    if filtered_df.empty:
        range_str = f">= {min_value}"
        if max_value:
            range_str = f"{min_value}-{max_value}"
        return [
            TextContent(
                type="text", text=f"❌ No Pokemon found with {stat_name} {range_str}."
            )
        ]

    # Ordina per stat (decrescente)
    filtered_df = filtered_df.sort_values(by=stat_name, ascending=False).head(limit)

    # Formatta output
    range_str = f">= {min_value}"
    if max_value:
        range_str = f"between {min_value} and {max_value}"

    result_lines = [
        f"## Pokemon with {stat_name.replace('_', ' ').title()} {range_str}",
        f"\n**Found {len(filtered_df)} Pokemon** (showing top {limit}):\n",
    ]

    for idx, row in filtered_df.iterrows():
        types_str = row["type1"].capitalize()
        if pd.notna(row.get("type2")):
            types_str += f"/{row['type2'].capitalize()}"

        result_lines.append(
            f"**{row['name']}** (#{int(row['pokedex_number'])})\n"
            f"  - {stat_name.replace('_', ' ').title()}: **{int(row[stat_name])}**\n"
            f"  - Type: {types_str} | BST: {int(row['base_total'])}"
            f"{' | Legendary' if row['is_legendary'] == 1 else ''}\n"
        )

    return [TextContent(type="text", text="\n".join(result_lines))]
