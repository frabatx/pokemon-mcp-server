"""
Tool: get_pokemon_by_type_combination

Query precisa per trovare Pokemon con una specifica combinazione di tipi.

Questo tool:
- Filtra per type1 (obbligatorio)
- Opzionalmente filtra per type2 (null = mono-type)
- Supporta exact_match per type2 (se false, ignora type2)
- Ordina per base_total

NON fa:
- Suggerimenti su quale type combination è migliore
- Analisi meta-game
- Team building advice

Input:
    type1: Tipo primario (obbligatorio)
    type2: Tipo secondario (opzionale, null per mono-type)
    exact_match: Se true, type2 deve matchare esattamente (default true)

Output:
    Lista Pokemon con la type combination specificata
"""

from mcp.types import TextContent
import pandas as pd
from .register import register_tool, ToolNames, ToolArguments, ToolResult
from utils.pokemon_helper import format_types, safe_int, tool_empty_result


@register_tool(
    name=ToolNames.GET_POKEMON_BY_TYPE_COMBINATION,
    description=(
        "Find Pokemon with a specific type combination. Filter by type1 (required) and "
        "optionally type2. Supports exact matching for dual-types or finding all mono-types."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "type1": {"type": "string", "description": "Primary type (e.g., 'fire')"},
            "type2": {
                "type": "string",
                "description": "Secondary type (null for mono-type, e.g., 'flying')",
            },
            "exact_match": {
                "type": "boolean",
                "description": "If true, type2 must match exactly. If false, ignores type2.",
                "default": True,
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 50,
            },
        },
        "required": ["type1"],
    },
)
async def get_pokemon_by_type_combination(
    arguments: ToolArguments, df: pd.DataFrame
) -> ToolResult:
    """
    Trova Pokemon per type combination.
    """
    type1 = arguments.get("type1", "").lower()
    type2 = arguments.get("type2")
    exact_match = arguments.get("exact_match", True)
    limit = arguments.get("limit", 50)

    # Filtra per type1
    filtered_df = df[df["type1"].str.lower() == type1].copy()

    if filtered_df.empty:
        return [
            TextContent(
                type="text", text=f"❌ No Pokemon found with type1 = '{type1}'."
            )
        ]

    # Filtra per type2 se specificato e exact_match
    if exact_match:
        if type2 is None or type2 == "":
            # Cerca mono-type (type2 is null)
            filtered_df = filtered_df[filtered_df["type2"].isna()]
        else:
            # Cerca type2 specifico
            type2_lower = type2.lower()
            filtered_df = filtered_df[filtered_df["type2"].str.lower() == type2_lower]

    if filtered_df.empty:
        type_combo = type1.capitalize()
        if type2:
            type_combo += f"/{type2.capitalize()}"
        else:
            type_combo += " (mono-type)"

        return [
            TextContent(
                type="text",
                text=f"❌ No Pokemon found with type combination: {type_combo}.",
            )
        ]

    # Ordina per base_total
    filtered_df = filtered_df.sort_values(by="base_total", ascending=False).head(limit)

    # Formatta output
    type_combo = type1.capitalize()
    if type2:
        type_combo += f"/{type2.capitalize()}"
    elif exact_match:
        type_combo += " (mono-type)"

    result_lines = [
        f"## Pokemon with Type: {type_combo}",
        f"\n**Found {len(filtered_df)} Pokemon**:\n",
    ]

    # OTTIMIZZAZIONE: usa to_dict('records') invece di iterrows
    for row in filtered_df.to_dict("records"):
        types_str = format_types(row["type1"], row.get("type2"))

        result_lines.append(
            f"**{row['name']}** (#{safe_int(row['pokedex_number'])})\n"
            f"  - Type: {types_str}\n"
            f"  - BST: {safe_int(row['base_total'])} | "
            f"HP {safe_int(row['hp'])} | Atk {safe_int(row['attack'])} | Def {safe_int(row['defense'])} | "
            f"SpA {safe_int(row['sp_attack'])} | SpD {safe_int(row['sp_defense'])} | Spe {safe_int(row['speed'])}"
            f"{' | Legendary' if row['is_legendary'] == 1 else ''}\n"
        )

    return [TextContent(type="text", text="\n".join(result_lines))]
