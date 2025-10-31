"""
Tool: calculate_bst_distribution

Calcola la distribuzione dei Base Stat Total (BST) in fasce predefinite.

Questo tool:
- Divide il dataset in bins di BST (es: 0-250, 251-350, etc)
- Conta Pokemon in ogni fascia
- Calcola percentuali
- Fornisce mean e median del dataset

NON fa:
- Interpretazioni sulla power creep tra generazioni (lavoro LLM)
- Valutazioni su cosa è "competitivo"
- Suggerimenti su quale BST target per il team

Input:
    bin_size: Ampiezza delle fasce (default 100)
    include_legendaries: Se includere i legendary (default true)

Output:
    Istogramma delle distribuzioni BST con count e percentuali
"""

from mcp.types import TextContent
import pandas as pd
from .register import register_tool, ToolNames, ToolArguments, ToolResult


@register_tool(
    name=ToolNames.CALCULATE_BST_DISTRIBUTION,
    description=(
        "Calculate the distribution of Base Stat Total (BST) across all Pokemon in bins. "
        "Returns histogram data with counts and percentages for each BST range."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "bin_size": {
                "type": "integer",
                "description": "Width of each bin (default 100, e.g., 0-100, 101-200...)",
                "default": 100,
            },
            "include_legendaries": {
                "type": "boolean",
                "description": "Include legendary Pokemon in distribution",
                "default": True,
            },
        },
    },
)
async def calculate_bst_distribution(
    arguments: ToolArguments, df: pd.DataFrame
) -> ToolResult:
    """
    Calcola distribuzione BST.
    """
    bin_size = arguments.get("bin_size", 100)
    include_legendaries = arguments.get("include_legendaries", True)

    # Filtra dataset
    filtered_df = df.copy()
    if not include_legendaries:
        filtered_df = filtered_df[filtered_df["is_legendary"] == 0]

    if filtered_df.empty:
        return [TextContent(type="text", text="❌ No Pokemon found matching criteria.")]

    # Calcola bins
    min_bst = int(filtered_df["base_total"].min())
    max_bst = int(filtered_df["base_total"].max())

    bins = list(range(0, max_bst + bin_size, bin_size))
    filtered_df["bst_bin"] = pd.cut(
        filtered_df["base_total"], bins=bins, include_lowest=True, right=True
    )

    # Conta per bin
    distribution = (
        filtered_df.groupby("bst_bin", observed=False).size().reset_index(name="count")
    )
    total_pokemon = len(filtered_df)

    distribution["percentage"] = (distribution["count"] / total_pokemon * 100).round(1)

    # Calcola mean e median
    mean_bst = filtered_df["base_total"].mean()
    median_bst = filtered_df["base_total"].median()

    # Formatta output
    dist_lines = []
    for _, row in distribution.iterrows():
        if row["count"] > 0:  # Solo bins non vuoti
            bin_range = str(row["bst_bin"])
            dist_lines.append(
                f"**{bin_range}**: {int(row['count'])} Pokemon ({row['percentage']}%)"
            )

    legendary_note = (
        "" if include_legendaries else "\n*Note: Legendary Pokemon excluded*"
    )

    result_text = f"""
## Base Stat Total Distribution
**Total Pokemon Analyzed**: {total_pokemon}
**Mean BST**: {mean_bst:.1f}
**Median BST**: {median_bst:.1f}
**Range**: {min_bst} - {max_bst}
{legendary_note}

### Distribution (bin size: {bin_size})

{chr(10).join(dist_lines)}
    """

    return [TextContent(type="text", text=result_text)]
