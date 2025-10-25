"""
Registry system per i tool MCP
"""
from functools import wraps
from typing import Any, Callable, Awaitable

from mcp.types import TextContent

type ToolArguments = dict[str, Any]
type BiographiesDict = dict[str, dict[str, str]]
type ToolResult = list[TextContent]
type ToolFn = Callable[..., Awaitable[ToolResult]]

tool_registry: dict[str, ToolFn] = {}

def register_biography(tool_name: str) -> Callable[[ToolFn], ToolFn]:
    """
    Decorator per registrare un tool nel registry.

    Usage:
        @register_biography("search_biography")
        async def search_biography(arguments: dict, bios: dict):
            ...
    """
    def decorator(fn: ToolFn) -> ToolFn:
        @wraps(fn)
        async def wrapper(*args, **kwargs) -> ToolResult:
            return await fn(*args, **kwargs)

        # Registra nel dizionario globale
        tool_registry[tool_name] = wrapper
        return wrapper

    return decorator


