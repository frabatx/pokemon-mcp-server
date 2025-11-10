"""
Utility functions condivise per tutti i tool Statistics.
Parsing, validazione, formattazione, calcoli comuni.
"""

import ast
from typing import Optional, Any, Union
import pandas as pd
import numpy as np
from mcp.types import TextContent


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


# ============================================================================
# ERROR HANDLING
# ============================================================================


def tool_error(message: str, prefix: str = "❌") -> list[TextContent]:
    """
    Crea un errore standardizzato per un tool.

    Args:
        message: Messaggio di errore
        prefix: Prefisso (default emoji X)

    Returns:
        Lista con TextContent formattato
    """
    return [TextContent(type="text", text=f"{prefix} {message}")]


def tool_validation_error(param: str, expected: str, got: Any) -> list[TextContent]:
    """
    Crea un errore di validazione standardizzato.

    Args:
        param: Nome del parametro
        expected: Tipo o valore atteso
        got: Valore ricevuto

    Returns:
        Lista con TextContent formattato
    """
    return tool_error(
        f"Invalid value for '{param}'. Expected {expected}, got: {got}"
    )


def tool_empty_result(criteria: str) -> list[TextContent]:
    """
    Crea un messaggio standardizzato per risultati vuoti.

    Args:
        criteria: Descrizione dei criteri di ricerca

    Returns:
        Lista con TextContent formattato
    """
    return [TextContent(type="text", text=f"❌ No Pokemon found matching: {criteria}")]


# ============================================================================
# SAFE TYPE CONVERSIONS
# ============================================================================


def safe_int(value: Any, default: int = 0) -> int:
    """
    Converte un valore a int in modo sicuro.

    Args:
        value: Valore da convertire
        default: Valore di default se conversione fallisce

    Returns:
        Intero convertito o default
    """
    if pd.isna(value):
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Converte un valore a float in modo sicuro.

    Args:
        value: Valore da convertire
        default: Valore di default se conversione fallisce

    Returns:
        Float convertito o default
    """
    if pd.isna(value):
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


# ============================================================================
# POKEMON OUTPUT FORMATTING
# ============================================================================


def format_pokemon_list_output(
    df: pd.DataFrame,
    title: str,
    include_abilities: bool = False,
    include_stats: bool = False,
    max_results: Optional[int] = None,
) -> str:
    """
    Formatta una lista di Pokemon in output standardizzato.

    Args:
        df: DataFrame con Pokemon da formattare
        title: Titolo della sezione
        include_abilities: Se includere abilities
        include_stats: Se includere tutti gli stat
        max_results: Numero massimo di risultati da mostrare

    Returns:
        Stringa formattata in Markdown
    """
    if df.empty:
        return f"## {title}\n\n**No Pokemon found**"

    if max_results:
        df = df.head(max_results)

    result_lines = [
        f"## {title}",
        f"\n**Found {len(df)} Pokemon**:\n",
    ]

    # Usa to_dict('records') per performance migliori
    for row in df.to_dict('records'):
        types_str = format_types(row["type1"], row.get("type2"))

        line = (
            f"**{row['name']}** (#{safe_int(row['pokedex_number'])})\n"
            f"  - Type: {types_str}\n"
        )

        if include_abilities:
            abilities = parse_abilities(row.get("abilities", ""))
            line += f"  - Abilities: {', '.join(abilities)}\n"

        if include_stats:
            line += (
                f"  - Stats: HP {safe_int(row['hp'])}, "
                f"Atk {safe_int(row['attack'])}, "
                f"Def {safe_int(row['defense'])}, "
                f"SpA {safe_int(row['sp_attack'])}, "
                f"SpD {safe_int(row['sp_defense'])}, "
                f"Spe {safe_int(row['speed'])}\n"
            )

        line += f"  - BST: {safe_int(row['base_total'])}"

        if row.get("is_legendary") == 1:
            line += " | Legendary"

        result_lines.append(line + "\n")

    return "\n".join(result_lines)


def format_pokemon_detail_output(pokemon: pd.Series) -> str:
    """
    Formatta i dettagli completi di un Pokemon.

    Args:
        pokemon: Serie pandas con dati del Pokemon

    Returns:
        Stringa formattata in Markdown
    """
    abilities = parse_abilities(pokemon.get("abilities", ""))
    types_str = format_types(pokemon["type1"], pokemon.get("type2"))

    lines = [
        f"## {pokemon['name']} (#{safe_int(pokemon['pokedex_number'])})",
        f"\n**Type:** {types_str}",
        f"**Abilities:** {', '.join(abilities)}",
        f"**Generation:** {safe_int(pokemon['generation'])}",
        f"**Legendary:** {'Yes' if pokemon.get('is_legendary') == 1 else 'No'}",
        "\n### Base Stats:",
        f"- HP: {create_stat_bar(safe_int(pokemon['hp']))}",
        f"- Attack: {create_stat_bar(safe_int(pokemon['attack']))}",
        f"- Defense: {create_stat_bar(safe_int(pokemon['defense']))}",
        f"- Sp. Attack: {create_stat_bar(safe_int(pokemon['sp_attack']))}",
        f"- Sp. Defense: {create_stat_bar(safe_int(pokemon['sp_defense']))}",
        f"- Speed: {create_stat_bar(safe_int(pokemon['speed']))}",
        f"\n**Base Stat Total:** {safe_int(pokemon['base_total'])}",
    ]

    return "\n".join(lines)


# ============================================================================
# VECTORIZED OPERATIONS
# ============================================================================


def calculate_resistance_scores_vectorized(
    df: pd.DataFrame, type_columns: list[str]
) -> pd.Series:
    """
    Calcola resistance scores in modo vettorizzato.

    Args:
        df: DataFrame con colonne against_*
        type_columns: Lista di colonne da considerare (es. ['against_fire', 'against_water'])

    Returns:
        Serie con resistance scores (media dei moltiplicatori)
    """
    # Filtra solo le colonne esistenti
    existing_cols = [col for col in type_columns if col in df.columns]

    if not existing_cols:
        return pd.Series(0.0, index=df.index)

    # Calcolo vettorizzato: media dei moltiplicatori
    return df[existing_cols].mean(axis=1)


def format_output_vectorized(df: pd.DataFrame) -> list[str]:
    """
    Formatta output di Pokemon usando operazioni vettorizzate dove possibile.

    Args:
        df: DataFrame con Pokemon

    Returns:
        Lista di stringhe formattate
    """
    # Converti a dict records una sola volta (più efficiente di iterrows)
    records = df.to_dict('records')

    output = []
    for row in records:
        types_str = format_types(row["type1"], row.get("type2"))

        line = (
            f"**{row['name']}** (#{safe_int(row['pokedex_number'])})\n"
            f"  - Type: {types_str}\n"
            f"  - BST: {safe_int(row['base_total'])}"
        )

        if row.get("is_legendary") == 1:
            line += " | Legendary"

        output.append(line)

    return output
