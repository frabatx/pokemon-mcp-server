"""
Registry system avanzato per i tool MCP con metadata.
"""
import inspect
from functools import wraps
from typing import Any, Callable, Awaitable
from dataclasses import dataclass
from enum import StrEnum

from mcp.types import TextContent, Tool

from connectors.neo4j_connector import Neo4jConnector

# Type aliases
type ToolArguments = dict[str, Any]
type ToolResult = list[TextContent]
type ToolFn = Callable[..., Awaitable[ToolResult]]


class ToolNames(StrEnum):
    """Enum centralizzato con tutti i nomi dei tool."""
    GET_POKEMON_TYPES = "get_pokemon_types"
    GET_POKEMON_EVOLUTIONS = "get_pokemon_evolutions"


@dataclass
class ToolMetadata:
    """
    Metadata completi di un tool MCP.
    Contiene tutto ciò che serve per list_tools().
    """
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any] | None = None # Opzionale: output_schema per validazione


@dataclass
class RegisteredTool:
    """
    Tool registrato completo di funzione e metadata.
    """
    func: ToolFn
    metadata: ToolMetadata


# Registry globale: name -> RegisteredTool
tool_registry: dict[str, RegisteredTool] = {}


def register_tool(
    name: ToolNames | str,
    description: str,
    input_schema: dict[str, Any],
    output_schema: dict[str, Any] | None = None
) -> Callable[[ToolFn], ToolFn]:
    """
    Decorator per registrare un tool con i suoi metadata.

    Usage:
        @register_tool(
            name=ToolNames.SEARCH_BIOGRAPHY,
            description="Search for a Pokemon biography",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Pokemon name"}
                },
                "required": ["name"]
            }
        )
        async def search_biography(arguments: dict, bios: dict):
            ...

    Args:
        name: Nome del tool (preferibilmente da ToolNames enum)
        description: Descrizione per l'AI
        input_schema: JSON Schema per i parametri di input
        output_schema: JSON Schema opzionale per l'output

    Returns:
        Decorator function
    """
    def decorator(fn: ToolFn) -> ToolFn:
        @wraps(fn)
        async def wrapper(*args, **kwargs) -> ToolResult:
            return await fn(*args, **kwargs)

        # Crea metadata
        metadata = ToolMetadata(
            name=str(name),  # Converte enum a string
            description=description,
            input_schema=input_schema,
            output_schema=output_schema
        )

        # Registra tool completo
        tool_registry[str(name)] = RegisteredTool(
            func=wrapper,
            metadata=metadata
        )

        return wrapper

    return decorator


def get_all_tools() -> list[Tool]:
    """
    Genera la lista di Tool MCP dal registry.
    Da usare direttamente in @server.list_tools().

    Returns:
        Lista di oggetti Tool pronti per MCP
    """
    return [
        Tool(
            name=registered.metadata.name,
            description=registered.metadata.description,
            inputSchema=registered.metadata.input_schema
        )
        for registered in tool_registry.values()
    ]


async def call_tool_from_registry(
    name: str,
    arguments: ToolArguments,
    neo4j_connector: Neo4jConnector
) -> ToolResult:
    """
    Esegue un tool dal registry con dispatch automatico.

    Args:
        name: Nome del tool da chiamare
        arguments: Argomenti da passare al tool
        biographies: Dizionario biografie

    Returns:
        Risultato del tool
    """

    if name not in tool_registry:
        return [TextContent(
            type="text",
            text=f"Tool '{name}' not found"
        )]

    registered = tool_registry[name]
    func = registered.func

    # Le tipologie di tool che sono sviluppate in questo server sono di due tipi,
    # una ha bisogno solo della fonte dati (biographies), mentre altri hanno bisogno di altri argomenti.
    # In questa sezione si utilizza l'introspection per capire quanti parametri ha la funzione chiamata
    # per modificarne la function call con il numero corretto di argomenti.

    sig = inspect.signature(func)
    params = list(sig.parameters.keys())

    if len(params) == 1:
        return await func(neo4j_connector)
    else:
        return await func(arguments, neo4j_connector)