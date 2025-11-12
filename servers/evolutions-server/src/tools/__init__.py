"""
Tools package per Biography Server.
Auto-registrazione di tutti i tool all'import.
"""

# Export del decorator e type aliases
from .register import (
    ToolArguments,
    ToolResult,
    ToolFn,
    tool_registry
)

# Import dei tool - auto-registrazione tramite decorator
from . import get_pokemon_types
from . import get_pokemon_evolutions