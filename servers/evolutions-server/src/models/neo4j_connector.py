from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class QueryResult:
    """Represents the result of a Neo4j query"""
    records: List[Dict[str, Any]]
    summary: Optional[Dict[str, Any]] = None
    keys: Optional[List[str]] = None
    
    @property
    def count(self) -> int:
        """Number of records returned"""
        return len(self.records)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            'records': self.records,
            'count': self.count,
            'keys': self.keys,
            'summary': self.summary
        }