from pathlib import Path
import sys
import os
from typing import Optional, Dict
import pandas as pd
import numpy as np

print("[INFO] Initializing statistics data loader...", file=sys.stderr)


def find_data_file() -> Path:
    """
    Cerca il file statistics.csv nella gerarchia del progetto.

    Returns:
        Path al file statistics.csv
    """
    # Prova prima con environment variable
    env_path = os.getenv("POKEMON_DATA_PATH")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path
        print(f"[WARNING] POKEMON_DATA_PATH set but file not found: {env_path}", file=sys.stderr)

    # Fallback al path relativo
    return Path(__file__).parent.parent.parent.parent.parent / "data" / "statistics.csv"


STATISTICS_PATH = find_data_file()
print(f"[INFO] Statistics path: {STATISTICS_PATH}", file=sys.stderr)
print(f"[INFO] File exists: {STATISTICS_PATH.exists()}", file=sys.stderr)


def _optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ottimizza il DataFrame per performance migliori.

    Args:
        df: DataFrame originale

    Returns:
        DataFrame ottimizzato
    """
    # Lowercase sui nomi per ricerca case-insensitive
    if "name" in df.columns:
        df["name_lower"] = df["name"].str.lower()

    # Converti colonne tipo a categorical (riduce memoria, accelera comparazioni)
    if "type1" in df.columns:
        df["type1"] = df["type1"].astype("category")
    if "type2" in df.columns:
        df["type2"] = df["type2"].astype("category")

    # Converti generation a int8 (risparmia memoria)
    if "generation" in df.columns:
        df["generation"] = df["generation"].astype("int8")

    # Converti is_legendary a boolean
    if "is_legendary" in df.columns:
        df["is_legendary"] = df["is_legendary"].astype("int8")

    return df


def _validate_dataframe(df: pd.DataFrame) -> bool:
    """
    Valida che il DataFrame contenga le colonne necessarie.

    Args:
        df: DataFrame da validare

    Returns:
        True se valido, False altrimenti
    """
    required_columns = [
        "name",
        "pokedex_number",
        "type1",
        "hp",
        "attack",
        "defense",
        "sp_attack",
        "sp_defense",
        "speed",
        "base_total",
    ]

    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        print(f"[ERROR] Missing required columns: {', '.join(missing)}", file=sys.stderr)
        return False

    if len(df) == 0:
        print("[ERROR] DataFrame is empty", file=sys.stderr)
        return False

    print(f"[OK] Data validation passed", file=sys.stderr)
    return True


def _load_statistics() -> pd.DataFrame:
    """
    Carica le statistiche Pokemon dal CSV con ottimizzazioni.

    Returns:
        DataFrame pandas ottimizzato con tutte le statistiche
    """
    if not STATISTICS_PATH.exists():
        print(f"[ERROR] File not found: {STATISTICS_PATH}", file=sys.stderr)
        return pd.DataFrame()

    try:
        print(f"[LOAD] Reading CSV: {STATISTICS_PATH}", file=sys.stderr)
        df = pd.read_csv(STATISTICS_PATH)

        print(
            f"[OK] Loaded {len(df)} Pokemon with {len(df.columns)} columns",
            file=sys.stderr,
        )

        # Valida i dati
        if not _validate_dataframe(df):
            return pd.DataFrame()

        # Ottimizza il DataFrame
        print("[OPTIMIZE] Applying optimizations...", file=sys.stderr)
        df = _optimize_dataframe(df)

        # Calcola memoria utilizzata
        memory_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
        print(f"[OK] Memory usage: {memory_mb:.2f} MB", file=sys.stderr)

        return df

    except Exception as e:
        print(f"[ERROR] Failed to load CSV: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        return pd.DataFrame()


print("[INFO] Loading statistics...", file=sys.stderr)
STATISTICS = _load_statistics()
print(f"[OK] Statistics ready: {len(STATISTICS)} Pokemon\n", file=sys.stderr)
