from mcp.types import TextContent
from .register import register_biography, BiographiesDict, ToolResult

@register_biography("list_all_pokemon")  # ← Decorator!
async def list_all_pokemon(bios: BiographiesDict) -> ToolResult:
    """Lista tutti i Pokemon disponibili."""
    pokemon_list = sorted([bio['name'] for bio in bios.values()])
    result = f"List of {len(pokemon_list)} Pokemon:\n\n"
    result += ", ".join(pokemon_list)
    return [TextContent(type="text", text=result)]

