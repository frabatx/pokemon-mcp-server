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
    name=ToolNames.GET_POKEMON_TYPES,
    description="Returns the types of a specific Pokemon",
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
async def get_pokemon_types(arguments: ToolArguments, neo4j_connector: Neo4jConnector) -> ToolResult:
    """Get all types of a specific Pokemon."""
    pokemon_name = arguments.get("name", "")
    
    try:
        # Get the query string
        query = get_query_string(ToolNames.GET_POKEMON_TYPES)
        
        # Execute query
        result = neo4j_connector.execute_query(query, parameters={"name": pokemon_name})
        
        # Concatenate output
        types = [record["type_name"] for record in result.records]
        
        if not types:
            return [TextContent(type="text", text=f"No types found for Pokemon '{pokemon_name}'.")]
        types_str = ", ".join(types)
        
        return [TextContent(type="text", text=f"Types of {pokemon_name}: {types_str}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error retrieving types for '{pokemon_name}': {e}")]

