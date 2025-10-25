from mcp.types import TextContent
from .register import (
    register_tool,
    ToolNames,
    ToolArguments,
    BiographiesDict,
    ToolResult
)


@register_tool(
    name=ToolNames.SEARCH_BIOGRAPHY,
    description="Search for a Pokemon biography by name. "
                "Returns detailed information about biology, habitat and characteristics.",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Pokemon name (e.g., 'Pikachu', 'Charizard')"
            }
        },
        "required": ["name"]
    }
)
async def search_biography(
    arguments: ToolArguments,
    bios: BiographiesDict
) -> ToolResult:
    """Cerca la biografia di un Pokemon per nome."""
    pokemon_name = arguments.get("name", "").lower()

    if pokemon_name not in bios:
        return [TextContent(
            type="text",
            text=f"Pokemon '{arguments.get('name')}' not found. "
                 f"Use 'list_all_pokemon' to see available Pokemon."
        )]

    bio = bios[pokemon_name]
    result = f"**{bio['name']}**\n\n{bio['bio']}"

    return [TextContent(type="text", text=result)]