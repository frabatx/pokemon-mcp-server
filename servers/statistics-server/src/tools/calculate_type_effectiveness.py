"""
Tool: calculate_type_effectiveness

Calcola il moltiplicatore di danno esatto quando un Pokemon con determinati tipi
attacca un Pokemon difensore specifico.

Questo tool:
- Legge le colonne 'against_*' del DataFrame per il difensore
- Calcola l'effectiveness per ogni tipo dell'attaccante
- Restituisce i moltiplicatori precisi (0x, 0.25x, 0.5x, 1x, 2x, 4x)

NON fa:
- Suggerimenti strategici (lavoro dell'LLM)
- Calcoli di danno completi (questo richiede mosse, livelli, etc)
- Team building advice

Input:
    attacker_types: Lista di 1-2 tipi dell'attaccante (es: ["fire", "flying"])
    defender_name: Nome del Pokemon difensore

Output:
    JSON con effectiveness per ogni tipo, moltiplicatore combinato, e verdict
"""

from mcp.types import TextContent
import pandas as pd
from .register import register_tool, ToolNames, ToolArguments, ToolResult


def get_type_effectiveness(defender_row: pd.Series, attacker_type: str) -> float:
    """
    Legge l'effectiveness dal DataFrame usando la colonna against_{type}.

    Args:
        defender_row: Riga del DataFrame del difensore
        attacker_type: Tipo dell'attacco (es: "fire")

    Returns:
        Moltiplicatore di danno (0, 0.25, 0.5, 1.0, 2.0, 4.0)
    """
    column_name = f"against_{attacker_type}"
    if column_name in defender_row.index:
        return float(defender_row[column_name])
    return 1.0  # Default neutral se colonna non esiste


@register_tool(
    name=ToolNames.CALCULATE_TYPE_EFFECTIVENESS,
    description=(
        "Calculate type effectiveness multipliers when specific attacker types hit a defender Pokemon. "
        "Returns precise damage multipliers (0x, 0.25x, 0.5x, 1x, 2x, 4x) by reading the 'against_*' "
        "columns from the CSV data."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "attacker_types": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of 1-2 attacker types (e.g., ['fire', 'flying'])",
                "minItems": 1,
                "maxItems": 2,
            },
            "defender_name": {
                "type": "string",
                "description": "Name of the defending Pokemon (e.g., 'Venusaur')",
            },
        },
        "required": ["attacker_types", "defender_name"],
    },
)
async def calculate_type_effectiveness(
    arguments: ToolArguments, df: pd.DataFrame
) -> ToolResult:
    """
    Calcola type effectiveness tra attaccante e difensore.
    """
    attacker_types = arguments.get("attacker_types", [])
    defender_name = arguments.get("defender_name", "")

    # Normalizza nome difensore (case-insensitive)
    defender_name_lower = defender_name.lower()
    defender_row = df[df["name"].str.lower() == defender_name_lower]

    if defender_row.empty:
        return [
            TextContent(
                type="text", text=f"❌ Pokemon '{defender_name}' not found in dataset."
            )
        ]

    defender_row = defender_row.iloc[0]

    # Estrai tipi difensore
    defender_types = [defender_row["type1"]]
    if pd.notna(defender_row.get("type2")):
        defender_types.append(defender_row["type2"])

    # Calcola effectiveness per ogni tipo attaccante
    effectiveness_results = {}
    for att_type in attacker_types:
        multiplier = get_type_effectiveness(defender_row, att_type.lower())
        effectiveness_results[att_type] = multiplier

    # Determina verdict basato sui moltiplicatori
    max_multiplier = max(effectiveness_results.values())
    if max_multiplier == 0:
        verdict = "immune"
    elif max_multiplier >= 2.0:
        verdict = "super_effective"
    elif max_multiplier < 1.0:
        verdict = "not_very_effective"
    else:
        verdict = "neutral"

    # Formatta output
    effectiveness_lines = "\n".join(
        [
            f"  - **{atype.capitalize()}**: {mult}x"
            for atype, mult in effectiveness_results.items()
        ]
    )

    result_text = f"""
## Type Effectiveness Calculation

**Defender**: {defender_row['name']} ({'/'.join(defender_types).capitalize()})

**Attacker Types**:
{effectiveness_lines}

**Verdict**: {verdict.replace('_', ' ').title()}

---
*Note: These multipliers are read directly from the 'against_*' columns in the dataset.*
"""

    return [TextContent(type="text", text=result_text)]
