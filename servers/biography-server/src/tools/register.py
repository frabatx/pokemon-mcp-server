"""
Registry system avanzato per i tool MCP con metadata.
"""
import inspect
from functools import wraps
from typing import Any, Callable, Awaitable
from dataclasses import dataclass
from enum import StrEnum

from mcp.types import TextContent, Tool

# Type aliases
type ToolArguments = dict[str, Any]
type BiographiesDict = dict[str, dict[str, str]]
type ToolResult = list[TextContent]
type ToolFn = Callable[..., Awaitable[ToolResult]]


class ToolNames(StrEnum):
    """Enum centralizzato con tutti i nomi dei tool."""
    SEARCH_BIOGRAPHY = "search_biography"
    SEARCH_BIOGRAPHY_FULLTEXT = "search_biography_fulltext"
    GET_RANDOM_BIOGRAPHY = "get_random_biography"
    LIST_ALL_POKEMON = "list_all_pokemon"


@dataclass
class ToolMetadata:
    """
    Metadata completi di un tool MCP.
    Contiene tutto ciò che serve per list_tools().
    """
    name: str
    description: str
    input_schema: dict[str, Any]
    # Opzionale: output_schema per validazione
    output_schema: dict[str, Any] | None = None


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
    biographies: BiographiesDict
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
        return await func(biographies)
    else:
        return await func(arguments, biographies)