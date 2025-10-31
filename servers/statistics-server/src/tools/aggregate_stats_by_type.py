"""
Tool: aggregate_stats_by_type

Calcola statistiche aggregate (media, mediana, max, min) per un tipo specifico.

Questo tool:
- Filtra Pokemon per tipo (type1 OR type2, o solo type1)
- Calcola mean, median, max, min per tutte le stats
- Identifica il Pokemon più forte (max base_total) del tipo
- Conta numero totale Pokemon del tipo

NON fa:
- Interpretazioni qualitative ("i Dragon sono forti" - lavoro LLM)
- Confronti tra tipi (questo è un altro tool potenziale)
- Suggerimenti strategici

Input:
    pokemon_type: Nome del tipo da analizzare
    primary_only: Se true, considera solo type1, altrimenti type1 OR type2

Output:
    Statistiche aggregate complete per il tipo
"""

from mcp.types import TextContent
import pandas as pd
from .register import register_tool, ToolNames, ToolArguments, ToolResult


@register_tool(
    name=ToolNames.AGGREGATE_STATS_BY_TYPE,
    description=(
        "Calculate aggregate statistics (mean, median, max, min) for all base stats of a specific type. "
        "Can filter by primary type only or include secondary types."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "pokemon_type": {
                "type": "string",
                "description": "Type to analyze (e.g., 'dragon', 'fire')",
            },
            "primary_only": {
                "type": "boolean",
                "description": "If true, only consider type1. If false, include type1 OR type2.",
                "default": False,
            },
        },
        "required": ["pokemon_type"],
    },
)
async def aggregate_stats_by_type(
    arguments: ToolArguments, df: pd.DataFrame
) -> ToolResult:
    """
    Calcola statistiche aggregate per un tipo.
    """
    pokemon_type = arguments.get("pokemon_type", "").lower()
    primary_only = arguments.get("primary_only", False)

    # Filtra Pokemon per tipo
    if primary_only:
        filtered_df = df[df["type1"].str.lower() == pokemon_type].copy()
    else:
        filtered_df = df[
            (df["type1"].str.lower() == pokemon_type)
            | (df["type2"].str.lower() == pokemon_type)
        ].copy()

    if filtered_df.empty:
        return [
            TextContent(
                type="text", text=f"❌ No Pokemon found with type '{pokemon_type}'."
            )
        ]

    # Stats da analizzare
    stats = [
        "hp",
        "attack",
        "defense",
        "sp_attack",
        "sp_defense",
        "speed",
        "base_total",
    ]

    # Calcola aggregazioni
    aggregations = {}
    for stat in stats:
        aggregations[stat] = {
            "mean": filtered_df[stat].mean(),
            "median": filtered_df[stat].median(),
            "max": filtered_df[stat].max(),
            "min": filtered_df[stat].min(),
        }

    # Trova Pokemon più forte
    strongest = filtered_df.loc[filtered_df["base_total"].idxmax()]

    # Formatta output
    stat_lines = []
    for stat in stats:
        agg = aggregations[stat]
        stat_lines.append(
            f"**{stat.replace('_', ' ').title()}**:\n"
            f"  - Mean: {agg['mean']:.1f}\n"
            f"  - Median: {agg['median']:.1f}\n"
            f"  - Max: {int(agg['max'])}\n"
            f"  - Min: {int(agg['min'])}"
        )

    type_filter = "type1" if primary_only else "type1 OR type2"

    result_text = f"""
## Aggregate Statistics for {pokemon_type.capitalize()} Type

**Filter**: {type_filter}
**Total Pokemon**: {len(filtered_df)}

### Stat Aggregations

{chr(10).join(stat_lines)}

### Strongest {pokemon_type.capitalize()}-type Pokemon

**{strongest['name']}** (#{int(strongest['pokedex_number'])})
- Base Total: {int(strongest['base_total'])}
- Type: {strongest['type1'].capitalize()}{f"/{strongest['type2'].capitalize()}" if pd.notna(strongest.get('type2')) else ""}
    """

    return [TextContent(type="text", text=result_text)]
