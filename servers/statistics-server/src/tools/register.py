"""
Registry system per Statistics MCP Server.
Pattern identico al biography-server ma adattato per DataFrame pandas.
"""

from functools import wraps
from typing import Any, Callable, Awaitable
from dataclasses import dataclass
from enum import StrEnum
import inspect

import pandas as pd
from mcp.types import TextContent, Tool

# Type aliases
type ToolArguments = dict[str, Any]
type StatsDataFrame = pd.DataFrame
type ToolResult = list[TextContent]
type ToolFn = Callable[..., Awaitable[ToolResult]]


class ToolNames(StrEnum):
    GET_POKEMON_STATS = "get_pokemon_stats"
    # Type effectiveness & matchups
    CALCULATE_TYPE_EFFECTIVENESS = "calculate_type_effectiveness"
    GET_RESISTANCES_AND_WEAKNESSES = "get_resistances_and_weaknesses"
    FIND_POKEMON_RESISTANT_TO_TYPES = "find_pokemon_resistant_to_types"

    # Filtering & querying
    FILTER_POKEMON_MULTI_CRITERIA = "filter_pokemon_multi_criteria"
    GET_POKEMON_BY_STAT_RANGE = "get_pokemon_by_stat_range"
    GET_POKEMON_BY_TYPE_COMBINATION = "get_pokemon_by_type_combination"
    GET_POKEMON_BY_ABILITY = "get_pokemon_by_ability"
    GET_POKEMON_BY_GENERATION = "get_pokemon_by_generation"

    # Comparisons & rankings
    COMPARE_POKEMON_HEAD_TO_HEAD = "compare_pokemon_head_to_head"
    FIND_SIMILAR_POKEMON = "find_similar_pokemon"
    GET_TOP_POKEMON_BY_STAT = "get_top_pokemon_by_stat"
    GET_EXTREME_POKEMON = "get_extreme_pokemon"

    # Statistics & aggregations
    CALCULATE_STAT_PERCENTILE = "calculate_stat_percentile"
    AGGREGATE_STATS_BY_TYPE = "aggregate_stats_by_type"
    CALCULATE_BST_DISTRIBUTION = "calculate_bst_distribution"


@dataclass
class ToolMetadata:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass
class RegisteredTool:
    func: ToolFn
    metadata: ToolMetadata


# Registry globale
tool_registry: dict[str, RegisteredTool] = {}


def register_tool(
    name: ToolNames | str, description: str, input_schema: dict[str, Any]
) -> Callable[[ToolFn], ToolFn]:
    """
    Decorator per registrare un tool statistics.
    Usage:
        @register_tool(
            name=ToolNames.GET_POKEMON_STATS,
            description="Get stats for a Pokemon",
            input_schema={...}
        )
        async def get_pokemon_stats(arguments: dict, df: pd.DataFrame):
            ...
    """

    def decorator(fn: ToolFn) -> ToolFn:
        @wraps(fn)
        async def wrapper(*args, **kwargs) -> ToolResult:
            return await fn(*args, **kwargs)

        metadata = ToolMetadata(
            name=str(name), description=description, input_schema=input_schema
        )
        tool_registry[str(name)] = RegisteredTool(func=wrapper, metadata=metadata)
        return wrapper

    return decorator


def get_all_tools() -> list[Tool]:
    """Genera lista Tool MCP dal registry."""
    return [
        Tool(
            name=registered.metadata.name,
            description=registered.metadata.description,
            inputSchema=registered.metadata.input_schema,
        )
        for registered in tool_registry.values()
    ]


async def call_tool_from_registry(
    name: str, arguments: ToolArguments, stats_df: StatsDataFrame
) -> ToolResult:
    """Esegue un tool dal registry."""
    if name not in tool_registry:
        return [TextContent(type="text", text=f"Tool '{name}' not found")]

    registered = tool_registry[name]
    func = registered.func

    # Introspection signature
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())

    # Dispatch intelligente
    if len(params) == 1:
        return await func(stats_df)
    else:
        return await func(arguments, stats_df)
