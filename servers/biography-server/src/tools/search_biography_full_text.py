from mcp.types import TextContent
from .register import (
    register_tool,
    ToolNames,
    ToolArguments,
    BiographiesDict,
    ToolResult
)


@register_tool(
    name=ToolNames.SEARCH_BIOGRAPHY_FULLTEXT,
    description="Full-text search in Pokemon biographies. "
                "Useful to find Pokemon with specific characteristics.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search text (e.g., 'electric type', 'evolves')"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 5
            }
        },
        "required": ["query"]
    }
)
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