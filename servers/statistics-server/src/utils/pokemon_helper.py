"""
Utility functions condivise per tutti i tool Statistics.
Parsing, validazione, formattazione, calcoli comuni.
"""

import ast
from typing import Optional
import pandas as pd


# ============================================================================
# POKEMON LOOKUP & VALIDATION
# ============================================================================


def find_pokemon(df: pd.DataFrame, name: str) -> Optional[pd.Series]:
    """
    Cerca un Pokemon per nome nel DataFrame.

    Args:
        df: DataFrame con i dati Pokemon
        name: Nome del Pokemon (case-insensitive)

    Returns:
        Serie pandas con i dati del Pokemon, o None se non trovato
    """
    matches = df[df["name_lower"] == name.lower()]

    if matches.empty:
        return None

    return matches.iloc[0]


def validate_stat_name(stat: str) -> tuple[bool, str]:
    """
    Valida se uno stat name è valido.

    Returns:
        (is_valid: bool, normalized_name: str)
    """
    valid_stats = {
        "hp": "hp",
        "attack": "attack",
        "atk": "attack",
        "defense": "defense",
        "def": "defense",
        "sp_attack": "sp_attack",
        "spatk": "sp_attack",
        "special_attack": "sp_attack",
        "sp_defense": "sp_defense",
        "spdef": "sp_defense",
        "special_defense": "sp_defense",
        "speed": "speed",
        "spe": "speed",
        "base_total": "base_total",
        "total": "base_total",
        "bst": "base_total",
    }

    normalized = stat.lower().replace(" ", "_")

    if normalized in valid_stats:
        return True, valid_stats[normalized]

    return False, stat


# ============================================================================
# PARSING & DATA EXTRACTION
# ============================================================================


def parse_abilities(abilities_str: str) -> list[str]:
    """
    Parse abilities string da formato lista Python.

    Args:
        abilities_str: String tipo "['Overgrow', 'Chlorophyll']"

    Returns:
        Lista di abilities

    Examples:
        >>> parse_abilities("['Overgrow', 'Chlorophyll']")
        ['Overgrow', 'Chlorophyll']
    """
    if pd.isna(abilities_str):
        return []

    try:
        return ast.literal_eval(abilities_str)
    except (ValueError, SyntaxError):
        # Fallback: split by comma
        return [a.strip().strip("'\"[]") for a in str(abilities_str).split(",")]


def get_type_matchups(pokemon: pd.Series) -> dict[str, list[str]]:
    """
    Estrae i type matchups significativi (diversi da 1.0).

    Args:
        pokemon: Serie pandas con i dati del Pokemon

    Returns:
        Dict con chiavi 'weaknesses', 'resistances', 'immunities'
    """
    matchups = {"weaknesses": [], "resistances": [], "immunities": []}

    # Tutti i tipi Pokemon
    types = [
        "bug",
        "dark",
        "dragon",
        "electric",
        "fairy",
        "fight",
        "fire",
        "flying",
        "ghost",
        "grass",
        "ground",
        "ice",
        "normal",
        "poison",
        "psychic",
        "rock",
        "steel",
        "water",
    ]

    for type_name in types:
        col_name = f"against_{type_name}"
        if col_name in pokemon.index:
            multiplier = pokemon[col_name]

            if multiplier == 0:
                matchups["immunities"].append(type_name.title())
            elif multiplier == 4:
                matchups["weaknesses"].append(f"{type_name.title()} (x4)")
            elif multiplier == 2:
                matchups["weaknesses"].append(f"{type_name.title()} (x2)")
            elif multiplier == 0.25:
                matchups["resistances"].append(f"{type_name.title()} (x0.25)")
            elif multiplier == 0.5:
                matchups["resistances"].append(f"{type_name.title()} (x0.5)")

    return matchups


# ============================================================================
# FORMATTING
# ============================================================================


def format_types(type1: str, type2: Optional[str]) -> str:
    """
    Formatta i tipi Pokemon in modo consistente.

    Examples:
        >>> format_types("grass", "poison")
        "Grass / Poison"
        >>> format_types("fire", None)
        "Fire"
    """
    result = type1.title()
    if pd.notna(type2) and type2:
        result += f" / {type2.title()}"
    return result


def format_gender_ratio(percentage_male: float) -> str:
    """
    Formatta il gender ratio in modo leggibile.

    Examples:
        >>> format_gender_ratio(88.1)
        "88.1% Male / 11.9% Female"
        >>> format_gender_ratio(None)
        "Genderless"
    """
    if pd.isna(percentage_male):
        return "Genderless"

    male = percentage_male
    female = 100 - percentage_male

    if male == 100:
        return "Male only"
    elif male == 0:
        return "Female only"
    else:
        return f"{male:.1f}% Male / {female:.1f}% Female"


def format_stat_value(value: float) -> str:
    """Formatta un valore stat come intero."""
    return str(int(value))


def create_stat_bar(value: int, max_val: int = 255, length: int = 15) -> str:
    """
    Crea una barra visuale per uno stat.

    Args:
        value: Valore dello stat (0-255 tipicamente)
        max_val: Valore massimo per la scala
        length: Lunghezza della barra in caratteri

    Returns:
        Stringa con barra + valore

    Examples:
        >>> create_stat_bar(100, 255, 10)
        "████░░░░░░ 100"
    """
    filled = int((value / max_val) * length)
    bar = "█" * filled + "░" * (length - filled)
    return f"{bar} {value}"


# ============================================================================
# STATISTICS & CALCULATIONS
# ============================================================================


def calculate_stat_rank(df: pd.DataFrame, pokemon: pd.Series, stat: str) -> dict:
    """
    Calcola il rank di un Pokemon per uno specifico stat.

    Returns:
        Dict con 'rank', 'total', 'percentile'
    """
    all_values = df[stat].sort_values(ascending=False)
    rank = (all_values > pokemon[stat]).sum() + 1  # +1 per index 1-based
    total = len(df)
    percentile = ((total - rank) / total) * 100

    return {"rank": rank, "total": total, "percentile": percentile}


def get_stat_rating(value: int, stat_name: str) -> str:
    """
    Valuta uno stat e restituisce un rating descrittivo.

    Returns:
        String tipo "Excellent", "Good", "Average", "Poor"
    """
    # Thresholds diversi per stat diversi
    thresholds = {
        "hp": {"excellent": 100, "good": 80, "average": 60},
        "attack": {"excellent": 120, "good": 90, "average": 65},
        "defense": {"excellent": 120, "good": 90, "average": 65},
        "sp_attack": {"excellent": 120, "good": 90, "average": 65},
        "sp_defense": {"excellent": 120, "good": 90, "average": 65},
        "speed": {"excellent": 110, "good": 80, "average": 50},
        "base_total": {"excellent": 550, "good": 450, "average": 350},
    }

    t = thresholds.get(stat_name, thresholds["attack"])

    if value >= t["excellent"]:
        return "Excellent"
    elif value >= t["good"]:
        return "Good"
    elif value >= t["average"]:
        return "Average"
    else:
        return "Poor"


def compare_stats(p1: pd.Series, p2: pd.Series, stat: str) -> dict:
    """
    Confronta uno stat specifico tra due Pokemon.

    Returns:
        Dict con 'value1', 'value2', 'diff', 'winner'
    """
    v1 = int(p1[stat])
    v2 = int(p2[stat])
    diff = v1 - v2

    winner = None
    if diff > 0:
        winner = p1["name"]
    elif diff < 0:
        winner = p2["name"]

    return {"value1": v1, "value2": v2, "diff": abs(diff), "winner": winner}


# ============================================================================
# BULK OPERATIONS
# ============================================================================


def get_all_stats(pokemon: pd.Series) -> dict[str, int]:
    """
    Estrae tutti gli stat base in un dict pulito.

    Returns:
        Dict con 'hp', 'attack', 'defense', etc.
    """
    return {
        "hp": int(pokemon["hp"]),
        "attack": int(pokemon["attack"]),
        "defense": int(pokemon["defense"]),
        "sp_attack": int(pokemon["sp_attack"]),
        "sp_defense": int(pokemon["sp_defense"]),
        "speed": int(pokemon["speed"]),
        "base_total": int(pokemon["base_total"]),
    }


def filter_by_criteria(
    df: pd.DataFrame,
    type_filter: Optional[str] = None,
    min_total: Optional[int] = None,
    max_total: Optional[int] = None,
    generation: Optional[int] = None,
    legendary_only: bool = False,
) -> pd.DataFrame:
    """
    Filtra il DataFrame secondo vari criteri.
    Utility per tool che hanno bisogno di filtrare Pokemon.
    """
    filtered = df.copy()

    if type_filter:
        type_lower = type_filter.lower()
        filtered = filtered[
            (filtered["type1"].str.lower() == type_lower)
            | (filtered["type2"].str.lower() == type_lower)
        ]

    if min_total:
        filtered = filtered[filtered["base_total"] >= min_total]

    if max_total:
        filtered = filtered[filtered["base_total"] <= max_total]

    if generation:
        filtered = filtered[filtered["generation"] == generation]

    if legendary_only:
        filtered = filtered[filtered["is_legendary"] == 1]

    return filtered
