import inspect
from enum import StrEnum
import json
import asyncio
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from tools.register import tool_registry

BIOGRAPHIES_PATH = Path(__file__).parent.parent.parent.parent / 'data' / 'biographies.json'


def load_biographies() -> dict:
    """Carica il file biographies.json e lo converte in un dizionario."""
    try:
        with open(BIOGRAPHIES_PATH, 'r', encoding='utf-8') as f:
            bios_list = json.load(f)
        return {bio['name'].lower(): bio for bio in bios_list}
    except FileNotFoundError:
        print(f"[ERROR] File {BIOGRAPHIES_PATH} not found!", file=sys.stderr)
        return {}
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON: {e}", file=sys.stderr)
        return {}


# Carica dati globalmente
BIOGRAPHIES = load_biographies()
print(f"[OK] Loaded {len(BIOGRAPHIES)} biographies", file=sys.stderr)

# Server definition
server = Server("pokemon-biography-server")


class biography_tools(StrEnum):
    """Enum con i nomi dei tool."""
    SEARCH_BIOGRAPHY = "search_biography"
    SEARCH_BIOGRAPHY_FULLTEXT = "search_biography_fulltext"
    GET_RANDOM_BIOGRAPHY = "get_random_biography"
    LIST_ALL_POKEMON = "list_all_pokemon"


# Tool Definition
@server.list_tools()
async def list_tools() -> list[Tool]:
    """Lista tutti i tool disponibili nel server."""
    return [
        Tool(
            name=biography_tools.SEARCH_BIOGRAPHY,
            description="Search for a Pokemon biography by name. "
                        "Returns detailed information about biology, habitat and characteristics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Pokemon name (e.g., 'Pikachu', 'Charizard')"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name=biography_tools.SEARCH_BIOGRAPHY_FULLTEXT,
            description="Full-text search in Pokemon biographies. "
                        "Useful to find Pokemon with specific characteristics.",
            inputSchema={
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
        ),
        Tool(
            name=biography_tools.GET_RANDOM_BIOGRAPHY,
            description="Returns a random Pokemon biography. "
                        "Useful to discover new Pokemon.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name=biography_tools.LIST_ALL_POKEMON,
            description="Returns the complete list of all 809 available Pokemon.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(
        name: str,  # ← MCP passa solo name e arguments!
        arguments: dict  # ← Non biographies!
) -> list[TextContent]:
    """
    Gestisce le chiamate ai tool tramite il registry.

    IMPORTANTE: MCP passa solo name e arguments.
    BIOGRAPHIES è una variabile globale che passiamo noi alle funzioni tool.
    """
    if name not in tool_registry:
        return [TextContent(
            type="text",
            text=f"Tool '{name}' not recognised"
        )]

    # richiamo il tool associato al name giusto grazie al registry pattern
    func = tool_registry[name]

    # Introspection per capire quanti parametri accetta la funzione
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())

    if len(params) == 1:
        # Tool che accetta solo biographies (es: list_all, random)
        return await func(BIOGRAPHIES)
    else:
        # Tool che accetta arguments + biographies (es: search)
        return await func(arguments, BIOGRAPHIES)


async def main():
    print("[START] Pokemon Biography MCP Server", file=sys.stderr)
    print(f"[DATA] Loaded from: {BIOGRAPHIES_PATH}", file=sys.stderr)
    print(f"[INFO] Pokemon available: {len(BIOGRAPHIES)}", file=sys.stderr)
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