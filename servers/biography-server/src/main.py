import asyncio
import sys

from mcp import stdio_server
from mcp.server import Server
from mcp.types import Tool, TextContent

# Import del registry avanzato
from tools.register import (
    get_all_tools,
    call_tool_from_registry,
    tool_registry
)

from utils.load_data import BIOGRAPHIES_PATH, BIOGRAPHIES

# Server definition
server = Server("pokemon-biography-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    Tutto viene dal registry.
    """
    return get_all_tools()


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Tutto delegato al registry.
    """
    return await call_tool_from_registry(name, arguments, BIOGRAPHIES)


async def main():
    """Avvio del server."""

    print("[START] Pokemon Biography MCP Server", file=sys.stderr)
    print(f"[DATA] Loaded from: {BIOGRAPHIES_PATH}", file=sys.stderr)
    print(f"[INFO] Registered tools: {list(tool_registry.keys())}", file=sys.stderr)
    print("[READY] Server listening on stdio\n", file=sys.stderr)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())