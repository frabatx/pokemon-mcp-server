"""
Tool: get_resistances_and_weaknesses

Estrae TUTTE le resistenze, debolezze e immunità di un Pokemon specifico
leggendo le 18 colonne 'against_*' dal CSV.

Questo tool:
- Parse tutte le colonne against_{type}
- Categorizza in: immunities (0x), ultra-resistances (0.25x), resistances (0.5x),
  neutral (1x), weaknesses (2x), ultra-weaknesses (4x)
- Restituisce dati strutturati per analisi difensiva

NON fa:
- Suggerimenti su come coprire le debolezze (lavoro LLM)
- Team building
- Matchup strategici

Input:
    pokemon_name: Nome del Pokemon da analizzare

Output:
    Categorizzazione completa di tutte le 18 type matchups
"""

from mcp.types import TextContent
import pandas as pd
from .register import register_tool, ToolNames, ToolArguments, ToolResult

# Tutti i tipi Pokemon possibili
ALL_TYPES = [
    "bug",
    "dark",
    "dragon",
    "electric",
    "fairy",
    "fighting",
    "fire",
    "flying",
    "ghost",
    "grass",
    "ground",
    "ice",
    "normal",
    "poison",
    "psychic",
    "rock",
    "steel",
    "water",
]


def categorize_matchups(pokemon_row: pd.Series) -> dict:
    """
    Categorizza tutti i type matchups in gruppi.

    Returns:
        Dict con chiavi: immunities, ultra_resistances, resistances,
        neutral, weaknesses, ultra_weaknesses
    """
    categories = {
        "immunities": [],  # 0x
        "ultra_resistances": [],  # 0.25x
        "resistances": [],  # 0.5x
        "neutral": [],  # 1x
        "weaknesses": [],  # 2x
        "ultra_weaknesses": [],  # 4x
    }

    for poke_type in ALL_TYPES:
        column = f"against_{poke_type}"
        if column in pokemon_row.index:
            multiplier = float(pokemon_row[column])

            if multiplier == 0:
                categories["immunities"].append(poke_type)
            elif multiplier == 0.25:
                categories["ultra_resistances"].append(poke_type)
            elif multiplier == 0.5:
                categories["resistances"].append(poke_type)
            elif multiplier == 1.0:
                categories["neutral"].append(poke_type)
            elif multiplier == 2.0:
                categories["weaknesses"].append(poke_type)
            elif multiplier >= 4.0:
                categories["ultra_weaknesses"].append(poke_type)

    return categories


@register_tool(
    name=ToolNames.GET_RESISTANCES_AND_WEAKNESSES,
    description=(
        "Extract all type resistances, weaknesses, and immunities for a specific Pokemon "
        "by parsing the 18 'against_*' columns. Returns structured data categorized by "
        "damage multiplier (0x, 0.25x, 0.5x, 1x, 2x, 4x)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "pokemon_name": {
                "type": "string",
                "description": "Name of the Pokemon to analyze (e.g., 'Charizard')",
            }
        },
        "required": ["pokemon_name"],
    },
)
async def get_resistances_and_weaknesses(
    arguments: ToolArguments, df: pd.DataFrame
) -> ToolResult:
    """
    Estrae resistenze e debolezze complete di un Pokemon.
    """
    pokemon_name = arguments.get("pokemon_name", "")

    # Trova Pokemon (case-insensitive)
    pokemon_name_lower = pokemon_name.lower()
    pokemon_row = df[df["name"].str.lower() == pokemon_name_lower]

    if pokemon_row.empty:
        return [
            TextContent(
                type="text", text=f"❌ Pokemon '{pokemon_name}' not found in dataset."
            )
        ]

    pokemon_row = pokemon_row.iloc[0]

    # Estrai tipi
    types = [pokemon_row["type1"]]
    if pd.notna(pokemon_row.get("type2")):
        types.append(pokemon_row["type2"])

    # Categorizza matchups
    matchups = categorize_matchups(pokemon_row)

    # Formatta output
    def format_type_list(type_list: list) -> str:
        if not type_list:
            return "  *None*"
        return "\n".join([f"  - {t.capitalize()}" for t in sorted(type_list)])

    result_text = f"""## Type Matchups for {pokemon_row['name']}

**Types**: {'/'.join([t.capitalize() for t in types])}

### 🛡️ Defensive Profile

**Immunities (0x)**:
{format_type_list(matchups['immunities'])}

**Ultra Resistances (0.25x)**:
{format_type_list(matchups['ultra_resistances'])}

**Resistances (0.5x)**:
{format_type_list(matchups['resistances'])}

**Weaknesses (2x)**:
{format_type_list(matchups['weaknesses'])}

**Ultra Weaknesses (4x)**:
{format_type_list(matchups['ultra_weaknesses'])}

---
**Summary**:
- Total Resistances: {len(matchups['immunities']) + len(matchups['ultra_resistances']) + len(matchups['resistances'])}
- Total Weaknesses: {len(matchups['weaknesses']) + len(matchups['ultra_weaknesses'])}
- Neutral: {len(matchups['neutral'])}
"""

    return [TextContent(type="text", text=result_text)]
