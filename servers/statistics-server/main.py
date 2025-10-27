"""Pokemon Statistics MCP Server"""

import asyncio
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import del registry
from tools.register import get_all_tools, call_tool_from_registry, tool_registry

# Import dati
from utils.load_data import STATISTICS_PATH, STATISTICS

# Server definition
server = Server("pokemon-statistics-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    Lista tool
    """
    return get_all_tools()


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Logica di chiamata ai tools
    """
    return await call_tool_from_registry(name, arguments, STATISTICS)


async def async_main():
    """Avvio del server."""
    print("[START] Pokemon Statistics MCP Server", file=sys.stderr)
    print(f"[DATA] Loaded from: {STATISTICS_PATH}", file=sys.stderr)
    print(f"[INFO] Pokemon available: {len(STATISTICS)}", file=sys.stderr)
    print(f"[INFO] Registered tools: {list(tool_registry.keys())}", file=sys.stderr)
    print("[READY] Server listening on stdio\n", file=sys.stderr)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


def main():
    """Entry point per uv/pip."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
