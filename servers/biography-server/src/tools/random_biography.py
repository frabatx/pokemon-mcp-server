import random
from mcp.types import TextContent
from .register import register_biography, BiographiesDict, ToolResult

@register_biography("get_random_biography")  # ← Decorator!
async def get_random_biography(bios: BiographiesDict) -> ToolResult:
    """Restituisce un Pokemon casuale."""
    bio = random.choice(list(bios.values()))
    result = f"Random Pokemon: **{bio['name']}**\n\n{bio['bio']}"
    return [TextContent(type="text", text=result)]