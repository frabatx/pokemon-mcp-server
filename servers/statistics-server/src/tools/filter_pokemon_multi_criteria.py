"""
Tool: filter_pokemon_multi_criteria

Query builder complesso per filtrare Pokemon con criteri multipli combinati (AND logic).

Questo tool:
- Applica filtri su: types, stats (min/max), generation, legendary status,
  capture rate, abilities, weight, height
- Combina TUTTI i filtri con logica AND
- Ordina risultati per qualsiasi colonna
- Limita numero risultati

NON fa:
- Suggerimenti su quali Pokemon scegliere (lavoro LLM)
- Valutazioni strategiche
- Team building advice

Input:
    Dizionario con tutti i filtri opzionali (types, min_stats, max_stats, etc)

Output:
    Lista Pokemon che matchano TUTTI i criteri specificati
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
    name=ToolNames.FILTER_POKEMON_MULTI_CRITERIA,
    description=(
        "Advanced multi-criteria filter for Pokemon. Combines multiple filters with AND logic "
        "including types, stat ranges, generation, legendary status, abilities, and physical "
        "attributes. Returns Pokemon matching ALL specified criteria."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "types": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter by type (matches type1 OR type2). Can be 1-2 types.",
            },
            "min_stats": {
                "type": "object",
                "description": "Minimum stat values (e.g., {'hp': 70, 'speed': 80})",
            },
            "max_stats": {
                "type": "object",
                "description": "Maximum stat values (e.g., {'weight_kg': 100})",
            },
            "generations": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Filter by generation numbers (e.g., [1, 2])",
            },
            "is_legendary": {
                "type": "boolean",
                "description": "Filter legendary (true) or non-legendary (false)",
            },
            "min_capture_rate": {
                "type": "integer",
                "description": "Minimum capture rate (higher = easier to catch)",
            },
            "abilities": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter Pokemon with any of these abilities",
            },
            "sort_by": {
                "type": "string",
                "description": "Column to sort by (e.g., 'base_total', 'speed')",
                "default": "base_total",
            },
            "ascending": {
                "type": "boolean",
                "description": "Sort order (true = ascending, false = descending)",
                "default": False,
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 20,
            },
        },
    },
)
async def filter_pokemon_multi_criteria(
    arguments: ToolArguments, df: pd.DataFrame
) -> ToolResult:
    """
    Filtra Pokemon con criteri multipli combinati.
    """
    filtered_df = df.copy()

    # FILTRO 1: Types
    types_filter = arguments.get("types", [])
    if types_filter:
        types_lower = [t.lower() for t in types_filter]
        filtered_df = filtered_df[
            filtered_df["type1"].str.lower().isin(types_lower)
            | filtered_df["type2"].str.lower().isin(types_lower)
        ]

    # FILTRO 2: Min stats
    min_stats = arguments.get("min_stats", {})
    for stat, min_val in min_stats.items():
        if stat in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[stat] >= min_val]

    # FILTRO 3: Max stats
    max_stats = arguments.get("max_stats", {})
    for stat, max_val in max_stats.items():
        if stat in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[stat] <= max_val]

    # FILTRO 4: Generations
    generations = arguments.get("generations", [])
    if generations:
        filtered_df = filtered_df[filtered_df["generation"].isin(generations)]

    # FILTRO 5: Legendary status
    is_legendary = arguments.get("is_legendary")
    if is_legendary is not None:
        filtered_df = filtered_df[
            filtered_df["is_legendary"] == (1 if is_legendary else 0)
        ]

    # FILTRO 6: Capture rate
    min_capture = arguments.get("min_capture_rate")
    if min_capture is not None:
        filtered_df = filtered_df[filtered_df["capture_rate"] >= min_capture]

    # FILTRO 7: Abilities
    abilities_filter = arguments.get("abilities", [])
    if abilities_filter:

        def has_ability(abilities_str, target_abilities):
            pokemon_abilities = parse_abilities_list(abilities_str)
            return any(
                ability.lower() in [ta.lower() for ta in target_abilities]
                for ability in pokemon_abilities
            )

        filtered_df = filtered_df[
            filtered_df["abilities"].apply(lambda x: has_ability(x, abilities_filter))
        ]

    # Verifica risultati
    if filtered_df.empty:
        return [
            TextContent(
                type="text", text="❌ No Pokemon found matching all specified criteria."
            )
        ]

    # Ordinamento
    sort_by = arguments.get("sort_by", "base_total")
    ascending = arguments.get("ascending", False)
    if sort_by in filtered_df.columns:
        filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)

    # Limita risultati
    limit = arguments.get("limit", 20)
    filtered_df = filtered_df.head(limit)

    # Formatta output
    result_lines = [f"## Filtered Pokemon ({len(filtered_df)} results)\n"]

    for idx, row in filtered_df.iterrows():
        types_str = row["type1"].capitalize()
        if pd.notna(row.get("type2")):
            types_str += f"/{row['type2'].capitalize()}"

        abilities = parse_abilities_list(row["abilities"])
        abilities_str = ", ".join(abilities)

        result_lines.append(
            f"**{row['name']}** (#{int(row['pokedex_number'])})\n"
            f"  - Type: {types_str}\n"
            f"  - BST: {int(row['base_total'])}\n"
            f"  - Stats: HP {int(row['hp'])} | Atk {int(row['attack'])} | Def {int(row['defense'])} | "
            f"SpA {int(row['sp_attack'])} | SpD {int(row['sp_defense'])} | Spe {int(row['speed'])}\n"
            f"  - Abilities: {abilities_str}\n"
            f"  - Gen {int(row['generation'])}"
            f"{' | Legendary' if row['is_legendary'] == 1 else ''}\n"
        )

    return [TextContent(type="text", text="\n".join(result_lines))]
