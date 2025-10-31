"""
Tool: get_top_pokemon_by_stat

Leaderboard semplice: top N Pokemon per una statistica specifica.

Questo tool:
- Ordina Pokemon per stat specificata (decrescente)
- Opzionalmente esclude legendary
- Opzionalmente filtra per generazione
- Mostra rank, nome, valore stat, tipo

NON fa:
- Valutazioni su chi è "migliore" overall (dipende da contesto)
- Suggerimenti strategici
- Comparazioni qualitative

Input:
    stat: Nome statistica per ranking
    limit: Top N Pokemon (default 10)
    exclude_legendaries: Se escludere legendary (default false)
    generation: Opzionalmente filtra per gen specifica

Output:
    Leaderboard con rank, nome, valore, tipo, legendary status
"""

from mcp.types import TextContent
import pandas as pd
from .register import register_tool, ToolNames, ToolArguments, ToolResult


@register_tool(
    name=ToolNames.GET_TOP_POKEMON_BY_STAT,
    description=(
        "Get top N Pokemon ranked by a specific stat. Optionally filter by generation "
        "or exclude legendaries. Returns leaderboard with rank, name, stat value, and type."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "stat": {
                "type": "string",
                "description": "Stat to rank by",
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
            "limit": {
                "type": "integer",
                "description": "Number of top Pokemon to return",
                "default": 10,
            },
            "exclude_legendaries": {
                "type": "boolean",
                "description": "Exclude legendary Pokemon from ranking",
                "default": False,
            },
            "generation": {
                "type": "integer",
                "description": "Filter by specific generation (optional)",
            },
        },
        "required": ["stat"],
    },
)
async def get_top_pokemon_by_stat(
    arguments: ToolArguments, df: pd.DataFrame
) -> ToolResult:
    """
    Ottiene top Pokemon per una stat.
    """
    stat = arguments.get("stat", "base_total")
    limit = arguments.get("limit", 10)
    exclude_legendaries = arguments.get("exclude_legendaries", False)
    generation = arguments.get("generation")

    if stat not in df.columns:
        return [TextContent(type="text", text=f"❌ Stat '{stat}' not found.")]

    # Filtra
    filtered_df = df.copy()

    if exclude_legendaries:
        filtered_df = filtered_df[filtered_df["is_legendary"] == 0]

    if generation is not None:
        filtered_df = filtered_df[filtered_df["generation"] == generation]

    if filtered_df.empty:
        return [TextContent(type="text", text="❌ No Pokemon found matching criteria.")]

    # Ordina e prendi top N
    leaderboard = filtered_df.nlargest(limit, stat).reset_index(drop=True)

    # Formatta output
    filters = []
    if exclude_legendaries:
        filters.append("Non-Legendary only")
    if generation:
        filters.append(f"Generation {generation}")

    filter_str = f" ({', '.join(filters)})" if filters else ""

    result_lines = [
        f"## Top {limit} Pokemon by {stat.replace('_', ' ').title()}{filter_str}\n"
    ]

    for idx, row in leaderboard.iterrows():
        rank = idx + 1
        types_str = row["type1"].capitalize()
        if pd.notna(row.get("type2")):
            types_str += f"/{row['type2'].capitalize()}"

        legendary_badge = " 👑" if row["is_legendary"] == 1 else ""

        result_lines.append(
            f"**#{rank}. {row['name']}**{legendary_badge}\n"
            f"  - {stat.replace('_', ' ').title()}: **{int(row[stat])}**\n"
            f"  - Type: {types_str}\n"
            f"  - BST: {int(row['base_total'])} | Gen {int(row['generation'])}\n"
        )

    return [TextContent(type="text", text="\n".join(result_lines))]
