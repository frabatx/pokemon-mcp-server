from mcp.types import TextContent
from .register import register_biography, ToolArguments, BiographiesDict, ToolResult

@register_biography("search_biography")
async def search_biography(
    arguments: ToolArguments,  # Usa i type alias
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