"""
Tool: compare_pokemon_head_to_head

Confronto numerico diretto tra due Pokemon specifici, stat per stat.

Questo tool:
- Confronta tutte le 6 base stats
- Calcola differenze numeriche precise
- Determina vincitore per ogni stat
- Calcola type matchups bidirezionali
- Conta "stat wins" totali

NON fa:
- Predizioni di battaglia (troppi fattori: mosse, abilità, items)
- Suggerimenti strategici
- Valutazioni soggettive

Input:
    pokemon1: Nome primo Pokemon
    pokemon2: Nome secondo Pokemon

Output:
    Confronto numerico completo con differenze precise
"""

from mcp.types import TextContent
import pandas as pd
from .register import register_tool, ToolNames, ToolArguments, ToolResult


def get_type_multiplier(attacker_types: list, defender_row: pd.Series) -> float:
    """
    Calcola il migliore moltiplicatore possibile tra i tipi dell'attaccante.
    """
    multipliers = []
    for att_type in attacker_types:
        column = f"against_{att_type.lower()}"
        if column in defender_row.index:
            multipliers.append(float(defender_row[column]))

    return max(multipliers) if multipliers else 1.0


@register_tool(
    name=ToolNames.COMPARE_POKEMON_HEAD_TO_HEAD,
    description=(
        "Direct numerical comparison between two Pokemon. Compares all 6 base stats, "
        "calculates exact differences, determines winner per stat, and analyzes type matchups. "
        "Returns structured data without subjective conclusions."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "pokemon1": {
                "type": "string",
                "description": "Name of first Pokemon (e.g., 'Charizard')",
            },
            "pokemon2": {
                "type": "string",
                "description": "Name of second Pokemon (e.g., 'Blastoise')",
            },
        },
        "required": ["pokemon1", "pokemon2"],
    },
)
async def compare_pokemon_head_to_head(
    arguments: ToolArguments, df: pd.DataFrame
) -> ToolResult:
    """
    Confronta due Pokemon head-to-head.
    """
    name1 = arguments.get("pokemon1", "")
    name2 = arguments.get("pokemon2", "")

    # Trova Pokemon (case-insensitive)
    p1_row = df[df["name"].str.lower() == name1.lower()]
    p2_row = df[df["name"].str.lower() == name2.lower()]

    if p1_row.empty:
        return [TextContent(type="text", text=f"❌ Pokemon '{name1}' not found.")]
    if p2_row.empty:
        return [TextContent(type="text", text=f"❌ Pokemon '{name2}' not found.")]

    p1_row = p1_row.iloc[0]
    p2_row = p2_row.iloc[0]

    # Estrai tipi
    p1_types = [p1_row["type1"]]
    if pd.notna(p1_row.get("type2")):
        p1_types.append(p1_row["type2"])

    p2_types = [p2_row["type1"]]
    if pd.notna(p2_row.get("type2")):
        p2_types.append(p2_row["type2"])

    # Stats da confrontare
    stats = ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]

    # Confronto stat per stat
    stat_comparisons = []
    p1_wins = 0
    p2_wins = 0

    for stat in stats:
        p1_val = int(p1_row[stat])
        p2_val = int(p2_row[stat])
        diff = abs(p1_val - p2_val)

        if p1_val > p2_val:
            winner = p1_row["name"]
            p1_wins += 1
        elif p2_val > p1_val:
            winner = p2_row["name"]
            p2_wins += 1
        else:
            winner = "Tie"

        stat_comparisons.append(
            {
                "stat": stat,
                "p1_val": p1_val,
                "p2_val": p2_val,
                "diff": diff,
                "winner": winner,
            }
        )

    # Type matchups
    p1_vs_p2_mult = get_type_multiplier(p1_types, p2_row)
    p2_vs_p1_mult = get_type_multiplier(p2_types, p1_row)

    # Formatta output
    stat_table = []
    for comp in stat_comparisons:
        winner_marker = "✓" if comp["winner"] != "Tie" else "="
        stat_table.append(
            f"**{comp['stat'].replace('_', ' ').title()}**: "
            f"{comp['p1_val']} vs {comp['p2_val']} "
            f"(Δ{comp['diff']}) {winner_marker} {comp['winner']}"
        )

    result_text = f"""## Head-to-Head: {p1_row['name']} vs {p2_row['name']}

### Base Stats Comparison

{chr(10).join(stat_table)}

**Base Stat Total**: {int(p1_row['base_total'])} vs {int(p2_row['base_total'])}

### Stat Wins
- **{p1_row['name']}**: {p1_wins} stats
- **{p2_row['name']}**: {p2_wins} stats

### Type Matchup

**{p1_row['name']}** ({'/'.join([t.capitalize() for t in p1_types])}) attacking **{p2_row['name']}**:
- Best multiplier: **{p1_vs_p2_mult}x**

**{p2_row['name']}** ({'/'.join([t.capitalize() for t in p2_types])}) attacking **{p1_row['name']}**:
- Best multiplier: **{p2_vs_p1_mult}x**

---
*Note: This is a numerical comparison. Actual battle outcomes depend on moves, abilities, items, and strategy.*
"""

    return [TextContent(type="text", text=result_text)]
