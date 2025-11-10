# servers/statistics-server/src/tools/filter_pokemon_multi_criteria.py

"""
Tool: filter_pokemon_multi_criteria

Query builder complesso per filtrare Pokemon con criteri multipli combinati (AND logic).

Questo tool:
- Applica filtri su: types, stats (min/max), generation, legendary status,
  capture rate, abilities, weight, height
- Combina TUTTI i filtri con logica AND
- Ordina risultati per qualsiasi colonna
- Limita numero risultati

TUTTI I FILTRI SONO OPZIONALI - specifica solo quelli che ti interessano!

NON fa:
- Suggerimenti su quali Pokemon scegliere (lavoro LLM)
- Valutazioni strategiche
- Team building advice

Input:
    Filtri disponibili (tutti opzionali):
    - type1, type2: Filtra per tipi
    - min_hp, max_hp: Range HP
    - min_attack, max_attack: Range Attack
    - min_defense, max_defense: Range Defense
    - min_sp_attack, max_sp_attack: Range Special Attack
    - min_sp_defense, max_sp_defense: Range Special Defense
    - min_speed, max_speed: Range Speed
    - min_base_total, max_base_total: Range Base Stat Total
    - min_weight_kg, max_weight_kg: Range peso
    - min_height_m, max_height_m: Range altezza
    - generation: Numero generazione (1-9)
    - is_legendary: true/false
    - min_capture_rate: Minimo capture rate
    - abilities: Lista abilities (match almeno una)
    - sort_by: Colonna per ordinamento
    - ascending: Ordine crescente/decrescente
    - limit: Numero max risultati

Output:
    Lista Pokemon che matchano TUTTI i criteri specificati
"""

from mcp.types import TextContent
import pandas as pd
from .register import register_tool, ToolNames, ToolArguments, ToolResult
from utils.pokemon_helper import (
    parse_abilities,
    format_types,
    safe_int,
    tool_empty_result,
)


@register_tool(
    name=ToolNames.FILTER_POKEMON_MULTI_CRITERIA,
    description=(
        "Advanced multi-criteria filter for Pokemon. ALL filters are optional - specify only "
        "what you need. Combines filters with AND logic. Available filters: types (type1/type2), "
        "stat ranges (min/max for hp/attack/defense/sp_attack/sp_defense/speed/base_total), "
        "physical attributes (weight_kg, height_m), generation, legendary status, capture_rate, "
        "and abilities. Results can be sorted by any column."
    ),
    input_schema={
        "type": "object",
        "properties": {
            # TYPE FILTERS
            "type1": {
                "type": "string",
                "description": "Filter by primary type (e.g., 'fire', 'water'). Matches type1 field.",
            },
            "type2": {
                "type": "string",
                "description": "Filter by secondary type (e.g., 'flying'). Matches type2 field. Use null or omit for mono-types.",
            },
            # HP FILTERS
            "min_hp": {
                "type": "integer",
                "description": "Minimum HP value (inclusive)",
                "minimum": 1,
            },
            "max_hp": {
                "type": "integer",
                "description": "Maximum HP value (inclusive)",
                "maximum": 255,
            },
            # ATTACK FILTERS
            "min_attack": {
                "type": "integer",
                "description": "Minimum Attack value (inclusive)",
                "minimum": 1,
            },
            "max_attack": {
                "type": "integer",
                "description": "Maximum Attack value (inclusive)",
                "maximum": 255,
            },
            # DEFENSE FILTERS
            "min_defense": {
                "type": "integer",
                "description": "Minimum Defense value (inclusive)",
                "minimum": 1,
            },
            "max_defense": {
                "type": "integer",
                "description": "Maximum Defense value (inclusive)",
                "maximum": 255,
            },
            # SPECIAL ATTACK FILTERS
            "min_sp_attack": {
                "type": "integer",
                "description": "Minimum Special Attack value (inclusive)",
                "minimum": 1,
            },
            "max_sp_attack": {
                "type": "integer",
                "description": "Maximum Special Attack value (inclusive)",
                "maximum": 255,
            },
            # SPECIAL DEFENSE FILTERS
            "min_sp_defense": {
                "type": "integer",
                "description": "Minimum Special Defense value (inclusive)",
                "minimum": 1,
            },
            "max_sp_defense": {
                "type": "integer",
                "description": "Maximum Special Defense value (inclusive)",
                "maximum": 255,
            },
            # SPEED FILTERS
            "min_speed": {
                "type": "integer",
                "description": "Minimum Speed value (inclusive)",
                "minimum": 1,
            },
            "max_speed": {
                "type": "integer",
                "description": "Maximum Speed value (inclusive)",
                "maximum": 255,
            },
            # BASE TOTAL FILTERS
            "min_base_total": {
                "type": "integer",
                "description": "Minimum Base Stat Total (inclusive)",
                "minimum": 1,
            },
            "max_base_total": {
                "type": "integer",
                "description": "Maximum Base Stat Total (inclusive)",
                "maximum": 1000,
            },
            # PHYSICAL ATTRIBUTES
            "min_weight_kg": {
                "type": "number",
                "description": "Minimum weight in kilograms (inclusive)",
            },
            "max_weight_kg": {
                "type": "number",
                "description": "Maximum weight in kilograms (inclusive)",
            },
            "min_height_m": {
                "type": "number",
                "description": "Minimum height in meters (inclusive)",
            },
            "max_height_m": {
                "type": "number",
                "description": "Maximum height in meters (inclusive)",
            },
            # GAME MECHANICS
            "generation": {
                "type": "integer",
                "description": "Filter by generation number (1-9)",
                "minimum": 1,
                "maximum": 9,
            },
            "is_legendary": {
                "type": "boolean",
                "description": "Filter legendary (true) or non-legendary (false) Pokemon",
            },
            "min_capture_rate": {
                "type": "integer",
                "description": "Minimum capture rate (higher = easier to catch, range 3-255)",
                "minimum": 3,
                "maximum": 255,
            },
            # ABILITIES
            "abilities": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter Pokemon with ANY of these abilities (e.g., ['Levitate', 'Blaze'])",
            },
            # SORTING & LIMITING
            "sort_by": {
                "type": "string",
                "description": "Column to sort results by",
                "enum": [
                    "name",
                    "pokedex_number",
                    "base_total",
                    "hp",
                    "attack",
                    "defense",
                    "sp_attack",
                    "sp_defense",
                    "speed",
                    "weight_kg",
                    "height_m",
                    "capture_rate",
                    "base_happiness",
                    "generation",
                ],
                "default": "base_total",
            },
            "ascending": {
                "type": "boolean",
                "description": "Sort order: true = ascending (lowest first), false = descending (highest first)",
                "default": False,
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 20,
                "minimum": 1,
                "maximum": 100,
            },
        },
        # NESSUN campo è required!
        "additionalProperties": False,  # Previene parametri non documentati
    },
)
async def filter_pokemon_multi_criteria(
    arguments: ToolArguments, df: pd.DataFrame
) -> ToolResult:
    """
    Filtra Pokemon con criteri multipli combinati.
    OTTIMIZZATO: usa boolean mask invece di filtering sequenziale per miglior performance.
    """
    # Crea una maschera booleana che parte con tutti True
    mask = pd.Series(True, index=df.index)
    applied_filters = []  # Track quali filtri sono stati applicati

    # FILTRO: Type1
    type1 = arguments.get("type1")
    if type1:
        type1_lower = type1.lower()
        mask &= df["type1"].str.lower() == type1_lower
        applied_filters.append(f"type1={type1.capitalize()}")

    # FILTRO: Type2
    type2 = arguments.get("type2")
    if type2:
        type2_lower = type2.lower()
        mask &= df["type2"].str.lower() == type2_lower
        applied_filters.append(f"type2={type2.capitalize()}")

    # FILTRI: Stats (min/max)
    stat_filters = {
        "hp": ("min_hp", "max_hp"),
        "attack": ("min_attack", "max_attack"),
        "defense": ("min_defense", "max_defense"),
        "sp_attack": ("min_sp_attack", "max_sp_attack"),
        "sp_defense": ("min_sp_defense", "max_sp_defense"),
        "speed": ("min_speed", "max_speed"),
        "base_total": ("min_base_total", "max_base_total"),
    }

    for stat_col, (min_key, max_key) in stat_filters.items():
        min_val = arguments.get(min_key)
        max_val = arguments.get(max_key)

        if min_val is not None:
            mask &= df[stat_col] >= min_val
            applied_filters.append(f"{stat_col}>={min_val}")

        if max_val is not None:
            mask &= df[stat_col] <= max_val
            applied_filters.append(f"{stat_col}<={max_val}")

    # FILTRI: Physical attributes
    min_weight = arguments.get("min_weight_kg")
    if min_weight is not None:
        mask &= df["weight_kg"] >= min_weight
        applied_filters.append(f"weight>={min_weight}kg")

    max_weight = arguments.get("max_weight_kg")
    if max_weight is not None:
        mask &= df["weight_kg"] <= max_weight
        applied_filters.append(f"weight<={max_weight}kg")

    min_height = arguments.get("min_height_m")
    if min_height is not None:
        mask &= df["height_m"] >= min_height
        applied_filters.append(f"height>={min_height}m")

    max_height = arguments.get("max_height_m")
    if max_height is not None:
        mask &= df["height_m"] <= max_height
        applied_filters.append(f"height<={max_height}m")

    # FILTRO: Generation
    generation = arguments.get("generation")
    if generation is not None:
        mask &= df["generation"] == generation
        applied_filters.append(f"gen={generation}")

    # FILTRO: Legendary status
    is_legendary = arguments.get("is_legendary")
    if is_legendary is not None:
        mask &= df["is_legendary"] == (1 if is_legendary else 0)
        applied_filters.append(f"legendary={'Yes' if is_legendary else 'No'}")

    # FILTRO: Capture rate
    min_capture = arguments.get("min_capture_rate")
    if min_capture is not None:
        mask &= df["capture_rate"] >= min_capture
        applied_filters.append(f"capture_rate>={min_capture}")

    # FILTRO: Abilities (questo richiede apply, ma lo facciamo solo una volta)
    abilities_filter = arguments.get("abilities", [])
    if abilities_filter:

        def has_ability(abilities_str, target_abilities):
            pokemon_abilities = parse_abilities(abilities_str)
            return any(
                ability.lower() in [ta.lower() for ta in target_abilities]
                for ability in pokemon_abilities
            )

        mask &= df["abilities"].apply(lambda x: has_ability(x, abilities_filter))
        applied_filters.append(f"abilities={', '.join(abilities_filter)}")

    # Applica la maschera UNA SOLA VOLTA
    filtered_df = df[mask].copy()

    # Verifica risultati
    if filtered_df.empty:
        filters_str = "\n".join([f"  - {f}" for f in applied_filters])
        return [
            TextContent(
                type="text",
                text=f"""❌ No Pokemon found matching all criteria.

**Applied Filters**:
{filters_str if applied_filters else "  - None (no filters specified)"}
""",
            )
        ]

    # Ordinamento
    sort_by = arguments.get("sort_by", "base_total")
    ascending = arguments.get("ascending", False)
    if sort_by in filtered_df.columns:
        filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)

    # Limita risultati
    limit = arguments.get("limit", 20)
    total_found = len(filtered_df)
    filtered_df = filtered_df.head(limit)

    # Formatta output
    filters_str = " & ".join(applied_filters) if applied_filters else "No filters"

    result_lines = [
        f"## Filtered Pokemon",
        f"\n**Filters Applied**: {filters_str}",
        f"**Results**: {total_found} Pokemon found (showing {len(filtered_df)})\n",
    ]

    # Usa to_dict('records') invece di iterrows per performance migliori
    for row in filtered_df.to_dict("records"):
        types_str = format_types(row["type1"], row.get("type2"))
        abilities = parse_abilities(row["abilities"])
        abilities_str = ", ".join(abilities)

        result_lines.append(
            f"**{row['name']}** (#{safe_int(row['pokedex_number'])})\n"
            f"  - Type: {types_str}\n"
            f"  - BST: {safe_int(row['base_total'])}\n"
            f"  - Stats: HP {safe_int(row['hp'])} | Atk {safe_int(row['attack'])} | Def {safe_int(row['defense'])} | "
            f"SpA {safe_int(row['sp_attack'])} | SpD {safe_int(row['sp_defense'])} | Spe {safe_int(row['speed'])}\n"
            f"  - Abilities: {abilities_str}\n"
            f"  - Gen {safe_int(row['generation'])}"
            f"{' | Legendary 👑' if row['is_legendary'] == 1 else ''}"
            f" | Weight {row['weight_kg']:.1f}kg | Height {row['height_m']:.1f}m\n"
        )

    return [TextContent(type="text", text="\n".join(result_lines))]
