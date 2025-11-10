"""
Tool: get_pokemon_by_ability

Filtra Pokemon che hanno una specifica ability.

Questo tool:
- Parse della colonna 'abilities' (formato stringa Python list)
- Cerca ability con match case-insensitive
- Ordina per base_total

NON fa:
- Spiegazioni su cosa fa l'ability (lavoro LLM con knowledge base)
- Suggerimenti strategici sull'uso dell'ability
- Team building

Input:
    ability: Nome dell'ability da cercare (case-insensitive)

Output:
    Lista Pokemon che hanno quell'ability
"""

from mcp.types import TextContent
import pandas as pd
from .register import register_tool, ToolNames, ToolArguments, ToolResult
from utils.pokemon_helper import (
    parse_abilities,
    format_types,
    safe_int,
    tool_error,
    tool_empty_result,
)


@register_tool(
    name=ToolNames.GET_POKEMON_BY_ABILITY,
    description=(
        "Filter Pokemon by a specific ability. Parses the 'abilities' column and returns "
        "all Pokemon that have the specified ability (case-insensitive match)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "ability": {
                "type": "string",
                "description": "Name of the ability to search for (e.g., 'Levitate', 'Blaze')",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 50,
            },
        },
        "required": ["ability"],
    },
)
async def get_pokemon_by_ability(
    arguments: ToolArguments, df: pd.DataFrame
) -> ToolResult:
    """
    Trova Pokemon con una specifica ability.
    """
    ability = arguments.get("ability", "").strip()
    limit = arguments.get("limit", 50)

    if not ability:
        return tool_error("Please specify an ability name.")

    ability_lower = ability.lower()

    # Filtra Pokemon con l'ability
    def has_ability(abilities_str):
        pokemon_abilities = parse_abilities(abilities_str)
        return any(a.lower() == ability_lower for a in pokemon_abilities)

    filtered_df = df[df["abilities"].apply(has_ability)].copy()

    if filtered_df.empty:
        return tool_empty_result(f"ability '{ability}'")

    # Ordina per base_total
    filtered_df = filtered_df.sort_values(by="base_total", ascending=False).head(limit)

    # Formatta output usando shared utilities e operazioni vettorizzate
    result_lines = [
        f"## Pokemon with Ability: {ability}",
        f"\n**Found {len(filtered_df)} Pokemon**:\n",
    ]

    # Usa to_dict('records') invece di iterrows per performance migliori
    for row in filtered_df.to_dict("records"):
        types_str = format_types(row["type1"], row.get("type2"))
        all_abilities = parse_abilities(row["abilities"])
        abilities_str = ", ".join(all_abilities)

        result_lines.append(
            f"**{row['name']}** (#{safe_int(row['pokedex_number'])})\n"
            f"  - Type: {types_str}\n"
            f"  - Abilities: {abilities_str}\n"
            f"  - BST: {safe_int(row['base_total'])}"
            f"{' | Legendary' if row['is_legendary'] == 1 else ''}\n"
        )

    return [TextContent(type="text", text="\n".join(result_lines))]
