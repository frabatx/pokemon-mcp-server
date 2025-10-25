"""
    Pokemon Biography MCP server

    Questo server espone le bio dei pockemon attraverso MCP
"""


import asyncio
import json
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

BIOGRAPHIES_PATH = Path(__file__).parent.parent.parent.parent / 'data' / 'biographies.json'

def load_biographies() -> dict:
    """Carica il file biographies.json e lo converte in un dizionario."""
    try:
        with open(BIOGRAPHIES_PATH, 'r', encoding='utf-8') as f:
            bios_list = json.load(f)
        # Convertiamo la lista in dizionario per ricerca veloce
        return {bio['name'].lower(): bio for bio in bios_list}
    except FileNotFoundError:
        print(f"ERRORE: File {BIOGRAPHIES_PATH} non trovato!")
        return {}
    except json.JSONDecodeError as e:
        print(f"ERRORE: File JSON malformato: {e}")
        return {}


# Carica i dati globalmente (una volta sola)
BIOGRAPHIES = load_biographies()
print(f" Caricate {len(BIOGRAPHIES)} biografie")


# === CREAZIONE SERVER MCP ===

# Crea l'istanza del server
server = Server("pokemon-biography-server")


# === DEFINIZIONE TOOLS ===

@server.list_tools()
async def list_tools() -> list[Tool]:
    """
    Lista tutti i tool disponibili nel server.
    Questa funzione viene chiamata dal client MCP per scoprire le funzionalità.
    """
    return [
        Tool(
            name="search_biography",
            description="Cerca la biografia completa di un Pokemon per nome. "
                       "Restituisce informazioni dettagliate sulla biologia, habitat e caratteristiche.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Il nome del Pokemon (es: 'Pikachu', 'Charizard')"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="search_biography_fulltext",
            description="Cerca nelle biografie usando una query testuale. "
                       "Utile per trovare Pokemon con caratteristiche specifiche.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Testo da cercare nelle biografie (es: 'electric type', 'evolves')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Numero massimo di risultati da restituire",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_random_biography",
            description="Restituisce la biografia di un Pokemon casuale. "
                       "Utile per scoprire Pokemon nuovi o per esempi.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_all_pokemon",
            description="Restituisce la lista completa di tutti i 809 Pokemon disponibili.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Gestisce le chiamate ai tool.
    Questa funzione viene invocata quando il client MCP vuole usare un tool.
    """
    
    if name == "search_biography":
        pokemon_name = arguments.get("name", "").lower()
        
        if pokemon_name not in BIOGRAPHIES:
            return [TextContent(
                type="text",
                text=f"❌ Pokemon '{arguments.get('name')}' non trovato. "
                     f"Usa 'list_all_pokemon' per vedere i Pokemon disponibili."
            )]
        
        bio = BIOGRAPHIES[pokemon_name]
        result = f"🎮 **{bio['name']}**\n\n{bio['bio']}"
        
        return [TextContent(type="text", text=result)]
    
    
    elif name == "search_biography_fulltext":
        query = arguments.get("query", "").lower()
        max_results = arguments.get("max_results", 5)
        
        results = []
        for bio in BIOGRAPHIES.values():
            if query in bio['bio'].lower():
                results.append(bio)
                if len(results) >= max_results:
                    break
        
        if not results:
            return [TextContent(
                type="text",
                text=f"Nessun risultato trovato per la query '{arguments.get('query')}'"
            )]
        
        result_text = f"Trovati {len(results)} Pokemon:\n\n"
        for bio in results:
            snippet = bio['bio'][:200] + "..." if len(bio['bio']) > 200 else bio['bio']
            result_text += f"**{bio['name']}**\n{snippet}\n\n"
        
        return [TextContent(type="text", text=result_text)]
    
    
    elif name == "get_random_biography":
        import random
        bio = random.choice(list(BIOGRAPHIES.values()))
        result = f"Pokemon Casuale: **{bio['name']}**\n\n{bio['bio']}"
        return [TextContent(type="text", text=result)]
    
    
    elif name == "list_all_pokemon":
        pokemon_list = sorted([bio['name'] for bio in BIOGRAPHIES.values()])
        result = f"Lista completa di {len(pokemon_list)} Pokemon:\n\n"
        result += ", ".join(pokemon_list)
        return [TextContent(type="text", text=result)]
    
    
    else:
        return [TextContent(
            type="text",
            text=f"Tool '{name}' non riconosciuto"
        )]


# === AVVIO SERVER ===

async def main():
    """Funzione principale che avvia il server MCP."""
    print("Avvio Pokemon Biography MCP Server...")
    print(f"Dati caricati da: {BIOGRAPHIES_PATH}")
    print(f"Pokemon disponibili: {len(BIOGRAPHIES)}")
    print("\nServer in ascolto su stdio...")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
