"""
Utilities per caricare i dati del progetto.
"""
from pathlib import Path
import json
import sys

# Path configurazione
BIOGRAPHIES_PATH = Path(__file__).parent.parent.parent.parent.parent / 'data' / 'biographies.json'


def _load_biographies() -> dict:
    """
    Carica le biografie dal file JSON.
    Funzione privata chiamata all'import.
    """
    try:
        with open(BIOGRAPHIES_PATH, 'r', encoding='utf-8') as f:
            bios_list = json.load(f)
        return {bio['name'].lower(): bio for bio in bios_list}
    except FileNotFoundError:
        print(f"[ERROR] File {BIOGRAPHIES_PATH} not found!", file=sys.stderr)
        return {}
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON: {e}", file=sys.stderr)
        return {}


# CARICAMENTO GLOBALE - Eseguito UNA VOLTA all'import
BIOGRAPHIES = _load_biographies()
print(f"[OK] Loaded {len(BIOGRAPHIES)} biographies", file=sys.stderr)