"""
Tools package per Biography Server.
Auto-registrazione di tutti i tool all'import.
"""

# Export del decorator e type aliases
from .register import (
    ToolArguments,
    BiographiesDict,
    ToolResult,
    ToolFn,
    tool_registry
)

# Import dei tool - auto-registrazione tramite decorator
from . import search_biography
from . import search_biography_full_text
from . import random_biography
from . import list_all_pokemon