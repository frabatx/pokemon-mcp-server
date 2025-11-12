from connectors.neo4j_connector import Neo4jConnector

from tools.get_pokemon_types import get_pokemon_types
from tools.get_pokemon_evolutions import get_pokemon_evolutions

'''
Script to test the graph queries without MCP framework.
'''

def example_basic_usage():
    """Basic synchronous usage example"""
    print("=== Basic Synchronous Usage ===")
    
    try:
        # Create connector (uses environment variables by default)
        neo4j_connector = Neo4jConnector()
        
        # Connect to the databases
        neo4j_connector.connect()
        
        # Test connection
        if not neo4j_connector.test_connection():
            print("❌ Cannot connect to Neo4j")
            return
        
        print("✅ Connected to Neo4j successfully")
        
        # Example 1: Count all Pokemon
        result = neo4j_connector.execute_query("MATCH (p:Pokemon) RETURN count(p) as total")
        if result.records:
            total = result.records[0]['total']
            print(f"📊 Total Pokemon in database: {total}")
        
        # Example 2: Get first 5 Pokemon names
        result = neo4j_connector.execute_query("MATCH (p:Pokemon) RETURN p.name as name LIMIT 5")
        print(f"🎮 First 5 Pokemon:")
        for record in result.records:
            print(f"  - {record['name']}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        neo4j_connector.close()
        
    
if __name__ == "__main__":
    # Simple test
    import asyncio
    from connectors.neo4j_connector import Neo4jConnector

    async def test():
        connector = Neo4jConnector()
        
        pokemon_names = ["Pikachu", "Charizard", "Bulbasaur", "pippo"]
        for pokemon_name in pokemon_names:
            result = await get_pokemon_evolutions({"name": pokemon_name}, connector)
            for content in result:
                print(content.text)
       
    asyncio.run(test())