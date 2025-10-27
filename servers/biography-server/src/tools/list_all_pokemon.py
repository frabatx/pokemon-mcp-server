from mcp.types import TextContent
from .register import (
    register_tool,
    ToolNames,
    BiographiesDict,
    ToolResult
)


@register_tool(
    name=ToolNames.LIST_ALL_POKEMON,
    description="Returns the complete list of all 809 available Pokemon.",
    input_schema={
        "type": "object",
        "properties": {}
    }
)
async def list_all_pokemon(bios: BiographiesDict) -> ToolResult:
    """Lista tutti i Pokemon disponibili."""
    pokemon_list = sorted([bio['name'] for bio in bios.values()])
    result = f"List of {len(pokemon_list)} Pokemon:\n\n"
    result += ", ".join(pokemon_list)
    return [TextContent(type="text", text=result)]