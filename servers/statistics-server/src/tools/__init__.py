from .register import tool_registry, ToolNames, ToolMetadata, RegisteredTool

# import dei tool - auto-registrazoine tramite decorator
from . import pokemon_stats
from . import aggregate_stats_by_type
from . import calculate_stat_percentile
from . import calculate_type_effectiveness
from . import calculate_bst_distribution
from . import compare_pokemon_head_to_head
from . import filter_pokemon_multi_criteria
from . import find_similar_pokemon
from . import find_pokemon_resistant_to_types
from . import get_extreme_pokemon
from . import get_pokemon_by_ability
from . import get_pokemon_by_generation
from . import get_pokemon_by_stat_range
from . import get_top_pokemon_by_stat
from . import get_pokemon_by_type_combination
from . import get_resistances_and_weaknesses
