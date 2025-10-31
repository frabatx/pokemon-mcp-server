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
import ast
from .register import register_tool, ToolNames, ToolArguments, ToolResult


def parse_abilities_list(abilities_str: str) -> list[str]:
    """Parse stringa abilities che è formato Python list."""
    try:
        return ast.literal_eval(abilities_str)
    except:
        return [abilities_str] if abilities_str else []


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
        return [TextContent(type="text", text="❌ Please specify an ability name.")]

    ability_lower = ability.lower()

    # Filtra Pokemon con l'ability
    def has_ability(abilities_str):
        pokemon_abilities = parse_abilities_list(abilities_str)
        return any(a.lower() == ability_lower for a in pokemon_abilities)

    filtered_df = df[df["abilities"].apply(has_ability)].copy()

    if filtered_df.empty:
        return [
            TextContent(
                type="text", text=f"❌ No Pokemon found with ability '{ability}'."
            )
        ]

    # Ordina per base_total
    filtered_df = filtered_df.sort_values(by="base_total", ascending=False).head(limit)

    # Formatta output
    result_lines = [
        f"## Pokemon with Ability: {ability}",
        f"\n**Found {len(filtered_df)} Pokemon**:\n",
    ]

    for idx, row in filtered_df.iterrows():
        types_str = row["type1"].capitalize()
        if pd.notna(row.get("type2")):
            types_str += f"/{row['type2'].capitalize()}"

        all_abilities = parse_abilities_list(row["abilities"])
        abilities_str = ", ".join(all_abilities)

        result_lines.append(
            f"**{row['name']}** (#{int(row['pokedex_number'])})\n"
            f"  - Type: {types_str}\n"
            f"  - Abilities: {abilities_str}\n"
            f"  - BST: {int(row['base_total'])}"
            f"{' | Legendary' if row['is_legendary'] == 1 else ''}\n"
        )

    return [TextContent(type="text", text="\n".join(result_lines))]
