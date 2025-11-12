import yaml

from pathlib import Path
from typing import Dict, Any
from tools.register import ToolNames


def load_query(tool_name: ToolNames) -> Dict[str, Any]:
    """
    Load a YAML query file based on the tool name enum
    
    Args:
        tool_name: ToolName enum value
        
    Returns:
        Dictionary containing the YAML data
        
    Raises:
        FileNotFoundError: If the YAML file doesn't exist
        ValueError: If the YAML file is invalid
    """
    # Get the queries directory relative to this file
    current_dir = Path(__file__).parent.parent
    queries_dir = current_dir / "tools" / "queries"
    
    yaml_file = queries_dir / f"{tool_name.value}.yaml"
    
    if not yaml_file.exists():
        raise FileNotFoundError(f"Query file not found: {yaml_file}")
    
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data
        
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in file {yaml_file}: {e}")


def get_query_string(tool_name: ToolNames) -> str:
    """
    Get just the Cypher query string from a YAML file
    
    Args:
        tool_name: ToolName enum value
        
    Returns:
        The Cypher query string
    """
    data = load_query(tool_name)
    return data['query']
