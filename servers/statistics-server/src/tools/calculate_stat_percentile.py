"""
Tool: calculate_stat_percentile

Calcola in che percentile si trova un Pokemon per una statistica specifica
rispetto a tutti gli altri Pokemon nel dataset.

Questo tool:
- Ordina tutti i Pokemon per la stat specificata
- Calcola il percentile esatto (0-100)
- Determina il rank assoluto
- Mostra Pokemon immediatamente sopra e sotto in classifica

NON fa:
- Valutazioni qualitative ("è veloce" vs "è lento" - lavoro LLM)
- Suggerimenti su come usare il Pokemon
- Confronti contestuali con meta-game

Input:
    pokemon_name: Nome del Pokemon da analizzare
    stat: Nome della statistica (hp, attack, defense, sp_attack, sp_defense, speed, base_total)

Output:
    Percentile, rank, valore della stat, Pokemon vicini in classifica
"""

from mcp.types import TextContent
import pandas as pd
from .register import register_tool, ToolNames, ToolArguments, ToolResult


@register_tool(
    name=ToolNames.CALCULATE_STAT_PERCENTILE,
    description=(
        "Calculate what percentile a Pokemon falls into for a specific stat compared to all Pokemon. "
        "Returns exact percentile (0-100), absolute rank, stat value, and nearby Pokemon in rankings."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "pokemon_name": {
                "type": "string",
                "description": "Name of the Pokemon to analyze (e.g., 'Pikachu')",
            },
            "stat": {
                "type": "string",
                "description": "Stat to analyze",
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
        },
        "required": ["pokemon_name", "stat"],
    },
)
async def calculate_stat_percentile(
    arguments: ToolArguments, df: pd.DataFrame
) -> ToolResult:
    """
    Calcola percentile di un Pokemon per una stat specifica.
    """
    pokemon_name = arguments.get("pokemon_name", "")
    stat = arguments.get("stat", "base_total")

    # Trova Pokemon
    pokemon_name_lower = pokemon_name.lower()
    pokemon_row = df[df["name"].str.lower() == pokemon_name_lower]

    if pokemon_row.empty:
        return [
            TextContent(
                type="text", text=f"❌ Pokemon '{pokemon_name}' not found in dataset."
            )
        ]

    if stat not in df.columns:
        return [
            TextContent(
                type="text",
                text=f"❌ Stat '{stat}' not found. Valid stats: hp, attack, defense, sp_attack, sp_defense, speed, base_total",
            )
        ]

    pokemon_row = pokemon_row.iloc[0]
    stat_value = int(pokemon_row[stat])

    # Ordina tutti i Pokemon per questa stat
    sorted_df = df.sort_values(by=stat, ascending=False).reset_index(drop=True)

    # Trova rank del Pokemon
    rank = sorted_df[sorted_df["name"] == pokemon_row["name"]].index[0] + 1
    total_pokemon = len(sorted_df)

    # Calcola percentile (quanti Pokemon ha battuto)
    percentile = ((total_pokemon - rank) / total_pokemon) * 100

    # Trova Pokemon vicini in classifica
    pokemon_index = rank - 1

    # 3 sopra
    higher_pokemon = []
    for i in range(max(0, pokemon_index - 3), pokemon_index):
        row = sorted_df.iloc[i]
        higher_pokemon.append(f"{row['name']} ({int(row[stat])})")

    # 3 sotto
    lower_pokemon = []
    for i in range(pokemon_index + 1, min(total_pokemon, pokemon_index + 4)):
        row = sorted_df.iloc[i]
        lower_pokemon.append(f"{row['name']} ({int(row[stat])})")

    # Formatta output
    result_text = f"""
    ## Stat Percentile Analysis: {pokemon_row['name']}

    ### {stat.replace('_', ' ').title()} Statistics

    **Value**: {stat_value}
    **Rank**: #{rank} out of {total_pokemon}
    **Percentile**: {percentile:.1f}th percentile

    *This Pokemon's {stat.replace('_', ' ')} is higher than {percentile:.1f}% of all Pokemon.*

    ### Nearby Rankings

    **Higher {stat.replace('_', ' ')} (ranked above)**:
    {chr(10).join([f"  - {p}" for p in higher_pokemon]) if higher_pokemon else "  *None (this is #1!)*"}

    **Lower {stat.replace('_', ' ')} (ranked below)**:
    {chr(10).join([f"  - {p}" for p in lower_pokemon]) if lower_pokemon else "  *None (this is last)*"}
    """

    return [TextContent(type="text", text=result_text)]
