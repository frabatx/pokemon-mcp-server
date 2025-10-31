"""
Tool: get_pokemon_by_generation

Filtra Pokemon per generazione con ordinamento opzionale.

Questo tool:
- Filtra Pokemon per numero generazione (1-9)
- Ordina per qualsiasi colonna (default: base_total)
- Supporta ordinamento crescente/decrescente
- Limita numero risultati

NON fa:
- Analisi delle differenze tra generazioni (lavoro LLM)
- Valutazioni su quale generazione è "migliore"
- Nostalgia e opinioni soggettive

Input:
    generation: Numero generazione (1-9)
    sort_by: Colonna per ordinamento (default: base_total)
    ascending: Ordine crescente (true) o decrescente (false)
    limit: Numero massimo risultati

Output:
    Lista Pokemon della generazione specificata, ordinati
"""

from mcp.types import TextContent
import pandas as pd
from .register import register_tool, ToolNames, ToolArguments, ToolResult


@register_tool(
    name=ToolNames.GET_POKEMON_BY_GENERATION,
    description=(
        "Filter Pokemon by generation number with optional sorting. Returns all Pokemon "
        "from the specified generation, sorted by any column."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "generation": {
                "type": "integer",
                "description": "Generation number (1-9)",
                "minimum": 1,
                "maximum": 9,
            },
            "sort_by": {
                "type": "string",
                "description": "Column to sort by (default: base_total)",
                "default": "base_total",
            },
            "ascending": {
                "type": "boolean",
                "description": "Sort in ascending order (true) or descending (false)",
                "default": False,
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 50,
            },
        },
        "required": ["generation"],
    },
)
async def get_pokemon_by_generation(
    arguments: ToolArguments, df: pd.DataFrame
) -> ToolResult:
    """
    Filtra Pokemon per generazione.
    """
    generation = arguments.get("generation")
    sort_by = arguments.get("sort_by", "base_total")
    ascending = arguments.get("ascending", False)
    limit = arguments.get("limit", 50)

    # Filtra per generazione
    filtered_df = df[df["generation"] == generation].copy()

    if filtered_df.empty:
        return [
            TextContent(
                type="text", text=f"❌ No Pokemon found in Generation {generation}."
            )
        ]

    # Ordina
    if sort_by in filtered_df.columns:
        filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)

    total_count = len(filtered_df)
    filtered_df = filtered_df.head(limit)

    # Formatta output
    result_lines = [
        f"## Generation {generation} Pokemon",
        f"\n**Found {total_count} Pokemon** (showing {len(filtered_df)}):\n",
    ]

    for idx, row in filtered_df.iterrows():
        types_str = row["type1"].capitalize()
        if pd.notna(row.get("type2")):
            types_str += f"/{row['type2'].capitalize()}"

        result_lines.append(
            f"**{row['name']}** (#{int(row['pokedex_number'])})\n"
            f"  - Type: {types_str}\n"
            f"  - BST: {int(row['base_total'])} | "
            f"{sort_by.replace('_', ' ').title()}: {int(row[sort_by]) if sort_by in row.index else 'N/A'}"
            f"{' | Legendary' if row['is_legendary'] == 1 else ''}\n"
        )

    return [TextContent(type="text", text="\n".join(result_lines))]
