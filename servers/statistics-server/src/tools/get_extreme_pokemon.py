"""
Tool: get_extreme_pokemon

Trova Pokemon con caratteristiche "estreme" (max o min) per varie metriche.

Questo tool:
- Supporta metriche: weight_kg, height_m, capture_rate, base_happiness, base_egg_steps
- Trova i valori massimi o minimi
- Utile per trivia e curiosità

NON fa:
- Spiegazioni del perché un Pokemon ha certi valori (lavoro LLM)
- Valutazioni strategiche su queste metriche
- Lore o backstory

Input:
    metric: Nome della metrica da analizzare
    extremity: "max" o "min"
    limit: Numero risultati (default 5)

Output:
    Lista Pokemon con valori estremi per la metrica
"""

from mcp.types import TextContent
import pandas as pd
from .register import register_tool, ToolNames, ToolArguments, ToolResult


@register_tool(
    name=ToolNames.GET_EXTREME_POKEMON,
    description=(
        "Find Pokemon with extreme values (maximum or minimum) for physical or game mechanics "
        "attributes like weight, height, capture rate, happiness, or egg steps."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "metric": {
                "type": "string",
                "description": "Metric to analyze",
                "enum": [
                    "weight_kg",
                    "height_m",
                    "capture_rate",
                    "base_happiness",
                    "base_egg_steps",
                ],
            },
            "extremity": {
                "type": "string",
                "description": "Find maximum or minimum values",
                "enum": ["max", "min"],
            },
            "limit": {
                "type": "integer",
                "description": "Number of results to return",
                "default": 5,
            },
        },
        "required": ["metric", "extremity"],
    },
)
async def get_extreme_pokemon(arguments: ToolArguments, df: pd.DataFrame) -> ToolResult:
    """
    Trova Pokemon con valori estremi per una metrica.
    """
    metric = arguments.get("metric", "weight_kg")
    extremity = arguments.get("extremity", "max")
    limit = arguments.get("limit", 5)

    if metric not in df.columns:
        return [TextContent(type="text", text=f"❌ Metric '{metric}' not found.")]

    # Ordina
    ascending = extremity == "min"
    extreme_df = (
        df.nsmallest(limit, metric) if ascending else df.nlargest(limit, metric)
    )

    if extreme_df.empty:
        return [
            TextContent(type="text", text=f"❌ No Pokemon found for metric '{metric}'.")
        ]

    # Determina unità
    units = {
        "weight_kg": "kg",
        "height_m": "m",
        "capture_rate": "",
        "base_happiness": "",
        "base_egg_steps": " steps",
    }
    unit = units.get(metric, "")

    # Formatta output
    extremity_word = (
        "Heaviest"
        if metric == "weight_kg" and extremity == "max"
        else (
            "Lightest"
            if metric == "weight_kg" and extremity == "min"
            else (
                "Tallest"
                if metric == "height_m" and extremity == "max"
                else (
                    "Shortest"
                    if metric == "height_m" and extremity == "min"
                    else f"{'Highest' if extremity == 'max' else 'Lowest'} {metric.replace('_', ' ').title()}"
                )
            )
        )
    )

    result_lines = [f"## {extremity_word} Pokemon\n"]

    for idx, row in extreme_df.iterrows():
        types_str = row["type1"].capitalize()
        if pd.notna(row.get("type2")):
            types_str += f"/{row['type2'].capitalize()}"

        value = row[metric]
        # Formatta valore (gestisci NaN)
        if pd.isna(value):
            value_str = "N/A"
        else:
            value_str = (
                f"{value:.1f}{unit}"
                if isinstance(value, float)
                else f"{int(value)}{unit}"
            )

        result_lines.append(
            f"**{row['name']}** (#{int(row['pokedex_number'])})\n"
            f"  - {metric.replace('_', ' ').title()}: **{value_str}**\n"
            f"  - Type: {types_str}\n"
            f"  - BST: {int(row['base_total'])}\n"
        )

    return [TextContent(type="text", text="\n".join(result_lines))]
