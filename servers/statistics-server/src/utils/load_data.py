from pathlib import Path
import sys
import pandas as pd

print("[INFO] Initializing statistics data loader...", file=sys.stderr)


def find_data_file() -> Path:
    """Cerca il file statistics.csv nella gerarchia del progetto."""
    # current = Path(__file__).resolve()
    #
    # for _ in range(10):
    #     data_file = current / "data" / "statistics.csv"
    #     if data_file.exists():
    #         return data_file
    #     current = current.parent

    # Fallback
    return Path(__file__).parent.parent.parent.parent.parent / "data" / "statistics.csv"


STATISTICS_PATH = find_data_file()
print(f"[INFO] Statistics path: {STATISTICS_PATH}", file=sys.stderr)
print(f"[INFO] File exists: {STATISTICS_PATH.exists()}", file=sys.stderr)


def _load_statistics() -> pd.DataFrame:
    """
    Carica le statistiche Pokemon dal CSV.

    Returns:
        DataFrame pandas con tutte le statistiche
    """
    if not STATISTICS_PATH.exists():
        print(f"[ERROR] File not found: {STATISTICS_PATH}", file=sys.stderr)
        return pd.DataFrame()
    try:
        print(f"[LOAD] Reading CSV: {STATISTICS_PATH}", file=sys.stderr)
        df = pd.read_csv(STATISTICS_PATH)

        # Lowercase sui nomi per ricerca case-insensitive
        if "name" in df.columns:
            df["name_lower"] = df["name"].str.lower()

        print(
            f"[OK] Loaded {len(df)} Pokemon with {len(df.columns)} columns",
            file=sys.stderr,
        )
        print(f"[INFO] Columns: {', '.join(df.columns[:10])}...", file=sys.stderr)

        return df

    except Exception as e:
        print(f"[ERROR] Failed to load CSV: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        return pd.DataFrame()


print("[INFO] Loading statistics...", file=sys.stderr)
STATISTICS = _load_statistics()
print(f"[OK] Statistics ready: {len(STATISTICS)} Pokemon\n", file=sys.stderr)
