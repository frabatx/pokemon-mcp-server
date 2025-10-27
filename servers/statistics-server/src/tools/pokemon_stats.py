"""
Tool per ottenere le statistiche complete di un Pokemon.
"""

from mcp.types import TextContent
from .register import (
    register_tool,
    ToolNames,
    ToolArguments,
    StatsDataFrame,
    ToolResult,
)
from utils.pokemon_helper import (
    find_pokemon,
    parse_abilities,
    get_type_matchups,
    format_types,
    format_gender_ratio,
    get_all_stats,
)


@register_tool(
    name=ToolNames.GET_POKEMON_STATS,
    description="Get complete combat statistics and detailed information for a Pokemon. "
    "Includes base stats, type matchups, physical characteristics, breeding info and more.",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Pokemon name (e.g., 'Pikachu', 'Charizard')",
            },
            "detailed": {
                "type": "boolean",
                "description": "Show detailed type matchups (default: true)",
                "default": True,
            },
        },
        "required": ["name"],
    },
)
async def get_pokemon_stats(arguments: ToolArguments, df: StatsDataFrame) -> ToolResult:
    """Restituisce le statistiche complete di un Pokemon."""
    pokemon_name = arguments.get("name", "")
    show_detailed = arguments.get("detailed", True)

    # Usa utility per lookup
    pokemon = find_pokemon(df, pokemon_name)

    if pokemon is None:
        return [
            TextContent(
                type="text",
                text=f"Pokemon '{pokemon_name}' not found in database.\n"
                f"Make sure the name is spelled correctly.",
            )
        ]

    # === COSTRUZIONE OUTPUT ===
    result = []

    # HEADER
    result.append(f"# {pokemon['name']}")
    result.append(f"*{pokemon['classfication']}*")
    result.append(f"Japanese: {pokemon['japanese_name']}")
    result.append("")

    # BASIC INFO
    result.append("## Basic Information")
    result.append(f"- **Pokedex Number**: #{pokemon['pokedex_number']}")
    result.append(f"- **Generation**: {int(pokemon['generation'])}")
    result.append(f"- **Legendary**: {'Yes' if pokemon['is_legendary'] else 'No'}")
    result.append("")

    # TYPES (usa utility)
    result.append("## Type")
    result.append(f"- {format_types(pokemon['type1'], pokemon['type2'])}")
    result.append("")

    # ABILITIES (usa utility)
    result.append("## Abilities")
    abilities = parse_abilities(pokemon["abilities"])
    for ability in abilities:
        result.append(f"- {ability}")
    result.append("")

    # BASE STATS (usa utility)
    result.append("## Base Stats")
    stats = get_all_stats(pokemon)
    for stat_name, value in stats.items():
        display_name = stat_name.replace("_", " ").title()
        if stat_name == "base_total":
            result.append(f"- **{display_name}**: **{value}**")
        else:
            result.append(f"- **{display_name}**: {value}")
    result.append("")

    # TYPE MATCHUPS (usa utility)
    if show_detailed:
        matchups = get_type_matchups(pokemon)

        if any(matchups.values()):
            result.append("## Type Matchups")

            if matchups["immunities"]:
                result.append("**Immune to:**")
                result.append(f"- {', '.join(matchups['immunities'])}")
                result.append("")

            if matchups["weaknesses"]:
                result.append("**Weak against:**")
                result.append(f"- {', '.join(matchups['weaknesses'])}")
                result.append("")

            if matchups["resistances"]:
                result.append("**Resistant to:**")
                result.append(f"- {', '.join(matchups['resistances'])}")
                result.append("")

    # PHYSICAL
    result.append("## Physical Characteristics")
    result.append(
        f"- **Height**: {pokemon['height_m']} m ({pokemon['height_m'] * 3.28084:.2f} ft)"
    )
    result.append(
        f"- **Weight**: {pokemon['weight_kg']} kg ({pokemon['weight_kg'] * 2.20462:.2f} lbs)"
    )
    result.append("")

    result.append("## Breeding & Capture")
    result.append(f"- **Capture Rate**: {pokemon['capture_rate']}")
    result.append(f"- **Base Happiness**: {int(pokemon['base_happiness'])}")
    result.append(f"- **Base Egg Steps**: {int(pokemon['base_egg_steps']):,}")
    result.append(
        f"- **Gender Ratio**: {format_gender_ratio(pokemon['percentage_male'])}"
    )
    result.append(f"- **Experience Growth**: {int(pokemon['experience_growth']):,}")

    return [TextContent(type="text", text="\n".join(result))]
