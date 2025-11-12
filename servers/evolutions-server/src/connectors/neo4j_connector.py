import os
import logging
from typing import Any, Dict, Optional

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, ClientError, TransientError

from models.config import Neo4jConfig
from models.neo4j_connector import QueryResult

logger = logging.getLogger(__name__)


class Neo4jConnector:
    """
    Neo4j Database Connector
    
    Provides methods to execute Cypher queries and return formatted results.
    Supports both synchronous and asynchronous operations.
    """
    
    def __init__(self, config: Optional[Neo4jConfig] = None):
        """
        Initialize Neo4j connector
        
        Args:
            config: Neo4j configuration. If None, loads from environment variables.
        """
        
        self.config = config or self._load_config_from_env()
        self.driver = None
        self.async_driver = None
        
    @staticmethod
    def _load_config_from_env() -> Neo4jConfig:
        """Load Neo4j configuration from environment variables"""
        return Neo4jConfig(
            uri=os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
            username=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "your_secure_password_here"),
            database=os.getenv("NEO4J_DATABASE", "neo4j"),
            max_connection_lifetime=os.getenv("NEO4J_MAX_CONNECTION_LIFETIME", 60),
            max_connection_pool_size=os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", 50),
            connection_timeout=os.getenv("NEO4J_CONNECTION_TIMEOUT", 30),
            max_retry_time=os.getenv("NEO4J_MAX_RETRY_TIME", 120)
        )
    
    def connect(self) -> None:
        """Establish connection to Neo4j database"""
        print(f"Creating driver for {self.config.uri} with user {self.config.username}")
        try:
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password),
                max_connection_lifetime=self.config.max_connection_lifetime,
                max_connection_pool_size=self.config.max_connection_pool_size,
                connection_timeout=self.config.connection_timeout
            )
                
            print(f"Created.")
            
        except ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable: {e}")
            raise ConnectionError(f"Cannot connect to Neo4j at {self.config.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def execute_query(
        self, 
        query: str, 
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> QueryResult:
        """
        Execute a Cypher query synchronously
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            database: Database name (uses default if None)
            
        Returns:
            QueryResult with records and metadata
        """
        if not self.driver:
            self.connect()
        
        db_name = database or self.config.database
        
        try:
            with self.driver.session(database=db_name) as session:
                result = session.run(query, parameters or {})
                records = []
                keys = result.keys()
                
                for record in result:
                    record_dict = {}
                    for key in keys:
                        value = record[key]
                        # Convert Neo4j types to Python types
                        record_dict[key] = self._convert_neo4j_types(value)
                    records.append(record_dict)
                
                summary = {
                    'query_type': result.consume().query_type,
                }
                
                return QueryResult(
                    records=records,
                    keys=keys,
                    summary=summary
                )
                
        except ClientError as e:
            logger.error(f"Cypher query error: {e}")
            raise ValueError(f"Invalid Cypher query: {e}")
        except TransientError as e:
            logger.warning(f"Transient error, retrying: {e}")
            # Could implement retry logic here
            raise
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
        
    
    def _convert_neo4j_types(self, value: Any) -> Any:
        """Convert Neo4j specific types to Python native types"""
        if hasattr(value, '__neo4j_type__'):
            # Node or Relationship
            if hasattr(value, '_properties'):
                result = dict(value._properties)
                if hasattr(value, 'labels'):
                    result['__labels__'] = list(value.labels)
                if hasattr(value, 'type'):
                    result['__type__'] = value.type
                if hasattr(value, 'id'):
                    result['__id__'] = value.id
                return result
        elif isinstance(value, (list, tuple)):
            return [self._convert_neo4j_types(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._convert_neo4j_types(v) for k, v in value.items()}
        
        return value
    
    def test_connection(self) -> bool:
        """Test if connection to Neo4j is working"""
        try:
            result = self.execute_query("RETURN 'Connection OK' as status")
            return len(result.records) > 0
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def close(self) -> None:
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j driver closed")
            
neo4j_connector = Neo4jConnector()
