from mcp.types import TextContent
from .register import register_biography, ToolArguments, BiographiesDict, ToolResult

@register_biography("search_biography_fulltext")
async def search_biography_fulltext(
    arguments: ToolArguments,
    bios: BiographiesDict
) -> ToolResult:
    """Ricerca full-text nelle biografie."""
    query = arguments.get("query", "").lower()
    max_results = arguments.get("max_results", 5)

    results = []
    for bio in bios.values():
        if query in bio['bio'].lower():
            results.append(bio)
            if len(results) >= max_results:
                break

    if not results:
        return [TextContent(
            type="text",
            text=f"No results found for query '{arguments.get('query')}'"
        )]

    result_text = f"Found {len(results)} Pokemon:\n\n"
    for bio in results:
        snippet = bio['bio'][:200] + "..."
        result_text += f"**{bio['name']}**\n{snippet}\n\n"

    return [TextContent(type="text", text=result_text)]