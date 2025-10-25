import random
from mcp.types import TextContent
from .register import (
    register_tool,
    ToolNames,
    BiographiesDict,
    ToolResult
)


@register_tool(
    name=ToolNames.GET_RANDOM_BIOGRAPHY,
    description="Returns a random Pokemon biography. "
                "Useful to discover new Pokemon.",
    input_schema={
        "type": "object",
        "properties": {}
    }
)
async def get_random_biography(bios: BiographiesDict) -> ToolResult:
    """Restituisce un Pokemon casuale."""
    bio = random.choice(list(bios.values()))
    result = f"Random Pokemon: **{bio['name']}**\n\n{bio['bio']}"
    return [TextContent(type="text", text=result)]