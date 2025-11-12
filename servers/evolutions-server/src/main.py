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

from connectors.neo4j_connector import neo4j_connector

# Server definition
server = Server("pokemon-evolutions-server")

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
    return await call_tool_from_registry(name, arguments, neo4j_connector)


async def main():
    """Avvio del server."""

    print("[START] Pokemon Biography MCP Server", file=sys.stderr)
    print(f"[DB] Created Connector for: {neo4j_connector.config.uri}", file=sys.stderr)
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