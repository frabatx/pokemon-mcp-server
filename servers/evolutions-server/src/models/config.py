from dataclasses import dataclass

@dataclass
class Neo4jConfig:
    """Neo4j connection configuration"""
    uri: str = "neo4j://localhost:7687" #TODO: Remove default values
    username: str = "neo4j" #TODO: Remove default values
    password: str = "your_secure_password_here" #TODO: Remove default values
    database: str = "neo4j" #TODO: Remove default values
    max_connection_lifetime: int = 3600
    max_connection_pool_size: int = 50
    connection_timeout: float = 30.0
    max_retry_time: float = 30.0
