from mcp.types import TextContent
from .register import (
    register_tool,
    ToolNames,
    ToolResult,
    ToolArguments
)

from connectors.neo4j_connector import Neo4jConnector
from utils.query_loader import get_query_string


@register_tool(
    name=ToolNames.GET_POKEMON_EVOLUTIONS,
    description="Returns the evolutions of a specific Pokemon (excluding the input Pokemon itself)",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Pokemon name (e.g., 'Pikachu', 'Charizard')",
            }
        },
        "required": ["name"],
    },
)
async def get_pokemon_evolutions(arguments: ToolArguments, neo4j_connector: Neo4jConnector) -> ToolResult:
    """Get all evolutions of a specific Pokemon (excluding the input Pokemon itself)."""
    pokemon_name = arguments.get("name", "")
    
    try:
        # Get the query string
        query = get_query_string(ToolNames.GET_POKEMON_EVOLUTIONS)
        
        # Execute query
        result = neo4j_connector.execute_query(query, parameters={"name": pokemon_name})

        # Concatenate output
        evolutions = [record["evolution_name"] for record in result.records]

        if not evolutions:
            return [TextContent(type="text", text=f"No evolutions found for Pokemon '{pokemon_name}'.")]
        evolutions_str = ", ".join(evolutions)

        return [TextContent(type="text", text=f"Evolutions of {pokemon_name}: {evolutions_str}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error retrieving evolutions for '{pokemon_name}': {e}")]

