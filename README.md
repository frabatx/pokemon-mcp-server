# Pokemon MCP Servers

A collection of **Model Context Protocol (MCP)** servers for accessing Pokemon data through AI assistants like Claude Desktop, Cursor, and other MCP clients.

## Overview

This project implements a modular architecture of MCP servers that expose Pokemon data through standardized tools. Each server specializes in a specific data type and uses an advanced **registry pattern** for scalable tool management.

### Available Servers

| Server | Description | Data Source | Tools |
|--------|-------------|-------------|-------|
| **Biography Server** | Detailed Pokemon biographies | `biographies.json` | 4 tools |
| **Statistics Server** | Combat statistics | `statistics.csv` | 3+ tools |
| **Graph Server** | Evolution relationships | Graph database | Coming soon |

---

## Project Architecture

```
pokemon-mcp-servers/
├── data/                           # Centralized shared data
│   ├── biographies.json           # 809 Pokemon biographies
│   ├── statistics.csv             # Combat stats (41 columns)
│   ├── pokemon_anime_data.json    # Anime episodes with embeddings
│   └── pokemon.cypher             # Graph database script
│
├── servers/                        # Independent MCP servers
│   ├── biography-server/
│   │   ├── main.py                # Server entry point
│   │   ├── src/
│   │   │   ├── tools/             # MCP tools
│   │   │   │   ├── __init__.py    # Auto-registration
│   │   │   │   ├── register.py    # Registry pattern
│   │   │   │   └── [tool_files].py
│   │   │   └── utils/
│   │   │       └── load_data.py   # Data loading
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── statistics-server/
│   │   ├── main.py                # Server entry point
│   │   ├── src/
│   │   │   ├── tools/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── register.py
│   │   │   │   └── [tool_files].py
│   │   │   └── utils/
│   │   │       ├── load_data.py
│   │   │       └── helpers.py     # Shared utilities
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   └── [your-new-server]/         # Repeatable pattern
│       ├── main.py                # Standard entry point
│       └── src/                   # Source code
│
└── notebooks/
    └── ingestion.ipynb            # Data preparation scripts
```

---

## Quick Start

### Prerequisites

- **Python 3.12+**
- **uv** (package manager)
- **Node.js** (for MCP Inspector)

### Installing uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Setup & Test

```bash
# 1. Clone repository
git clone https://github.com/your-username/pokemon-mcp-servers.git
cd pokemon-mcp-servers

# 2. Setup Biography Server
cd servers/biography-server
uv sync

# 3. Test server
uv run main.py

# Expected output:
# [OK] Loaded 809 biographies
# [START] Pokemon Biography MCP Server
# [READY] Server listening on stdio

# 4. Test with Inspector (new terminal)
npx @modelcontextprotocol/inspector uv run main.py
# Open http://localhost:5173
```

---

## Registry Pattern - Deep Dive

### The Problem: Traditional MCP Servers

**Without Registry Pattern**, each tool requires modifications in 3+ places:

```
PROBLEM: Duplication and Coupling

1. Define enum with tool name           <- main.py
2. Implement tool function              <- tools/my_tool.py  
3. Add to list_tools()                  <- main.py (manual!)
4. Add case to call_tool()              <- main.py (manual!)
5. Keep name/metadata synchronized      <- Error-prone!

Result: 
- Code duplication
- Easy to make errors
- Hard to maintain
- Doesn't scale well
```

### The Solution: Registry Pattern with Auto-Discovery

**With Registry Pattern**, each tool is **self-contained**:

```
SOLUTION: Single Source of Truth

1. Create tool file with decorator      <- tools/my_tool.py
2. Auto-import                          <- tools/__init__.py
3. DONE! 

Result:
- Zero duplication
- Tools self-contained
- Easy to add tools
- Scales perfectly
```

### 3-Layer Architecture

```
┌─────────────────────────────────────────────────────┐
│  LAYER 1: Server Entry Point                        │
│  (main.py)                                          │
│                                                     │
│  @server.list_tools()                               │
│  async def list_tools():                            │
│      return get_all_tools()  <- From registry       │
│                                                     │
│  @server.call_tool()                                │
│  async def call_tool(name, args):                   │
│      return await call_tool_from_registry(...)      │
│                                                     │
│  ZERO business logic - Only delegation!             │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ delegates to
                   │
┌──────────────────▼──────────────────────────────────┐
│  LAYER 2: Registry & Dispatcher                     │
│  (src/tools/register.py)                            │
│                                                     │
│  tool_registry = {}  <- Global dictionary           │
│                                                     │
│  @register_tool(name, description, schema)          │
│  def decorator(fn):                                 │
│      tool_registry[name] = RegisteredTool(...)      │
│      return fn                                      │
│                                                     │
│  get_all_tools() -> Generate Tool list              │
│  call_tool_from_registry() -> Dispatcher            │
│                                                     │
│  AUTO-DISCOVERY: Finds all registered tools         │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ registers
                   │
┌──────────────────▼──────────────────────────────────┐
│  LAYER 3: Tool Implementations                      │
│  (src/tools/my_tool.py, etc.)                       │
│                                                     │
│  @register_tool(                                    │
│      name=ToolNames.MY_TOOL,                        │
│      description="...",                             │
│      input_schema={...}                             │
│  )                                                  │
│  async def my_tool(args, data):                     │
│      # ... specific logic ...                       │
│      return [TextContent(...)]                      │
│                                                     │
│  SELF-CONTAINED: Everything in one file!            │
└─────────────────────────────────────────────────────┘
```

### Auto-Registration Flow

**What happens when the server starts:**

1. **Server Import**
   ```
   Python executes: python main.py
   ```

2. **Server imports Tools Package**
   ```
   Python executes: from src.tools.register import ...
   Python executes: src/tools/__init__.py
   ```

3. **Tools Package imports each Tool**
   ```
   # In src/tools/__init__.py:
   from . import my_first_tool
   from . import my_second_tool
   from . import my_third_tool
   ```

4. **Each Import executes the Decorator**
   ```
   # my_first_tool.py is executed
   @register_tool(...)  <- DECORATOR EXECUTES NOW!
   async def my_first_tool(...): ...
   
   # Decorator adds to registry:
   tool_registry["my_first_tool"] = RegisteredTool(...)
   ```

5. **Registry Populated**
   ```
   tool_registry = {
       "my_first_tool": RegisteredTool(...),
       "my_second_tool": RegisteredTool(...),
       "my_third_tool": RegisteredTool(...)
   }
   ```

6. **Server Ready**
   ```
   get_all_tools() -> reads from tool_registry
   call_tool_from_registry() -> automatic dispatcher
   ```

### Registry Components

#### 1. Type Aliases (Type Safety)

```python
# Python 3.12 type statement
type ToolArguments = dict[str, Any]
type ToolResult = list[TextContent]
type ToolFn = Callable[..., Awaitable[ToolResult]]
```

**Benefits:**
- Clean type hints
- IDE auto-completion
- Less verbosity

#### 2. ToolNames Enum (Centralized Names)

```python
class ToolNames(StrEnum):
    MY_FIRST_TOOL = "my_first_tool"
    MY_SECOND_TOOL = "my_second_tool"
```

**Benefits:**
- No typos in names
- Safe refactoring
- Auto-completion

#### 3. Metadata Dataclasses (Structure)

```python
@dataclass
class ToolMetadata:
    name: str
    description: str
    input_schema: dict[str, Any]

@dataclass
class RegisteredTool:
    func: ToolFn
    metadata: ToolMetadata
```

**Benefits:**
- Strong typing
- Immutability
- Automatic validation

#### 4. Decorator (Auto-Registration)

```python
def register_tool(name, description, input_schema):
    def decorator(fn):
        # Create metadata
        metadata = ToolMetadata(...)
        
        # Register in global dictionary
        tool_registry[name] = RegisteredTool(
            func=fn,
            metadata=metadata
        )
        
        return fn
    return decorator
```

**Benefits:**
- Declarative (not imperative)
- Metadata close to logic
- Automatic execution on import

#### 5. Utility Functions (Public API)

```python
def get_all_tools() -> list[Tool]:
    """Generate MCP Tool list from registry"""
    return [
        Tool(
            name=reg.metadata.name,
            description=reg.metadata.description,
            inputSchema=reg.metadata.input_schema
        )
        for reg in tool_registry.values()
    ]

async def call_tool_from_registry(name, args, data):
    """Intelligent dispatcher with introspection"""
    if name not in tool_registry:
        return error_response(...)
    
    func = tool_registry[name].func
    
    # Introspection: 1 or 2 parameters?
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())
    
    if len(params) == 1:
        return await func(data)
    else:
        return await func(args, data)
```

### Pattern Comparison

| Aspect | Traditional | Registry Pattern |
|--------|-------------|------------------|
| **Adding tools** | Modify 4+ files | Create 1 file |
| **Synchronization** | Manual | Automatic |
| **Server main** | 100+ lines | 20 lines |
| **Duplication** | High | None |
| **Maintainability** | Difficult | Easy |
| **Scalability** | Limited | Unlimited |
| **Errors** | Frequent | Rare |

### Pattern Benefits

1. **DRY (Don't Repeat Yourself)**
   - Tool name in 1 place only
   - Input/output schema near logic
   - Zero duplication

2. **Single Responsibility**
   - Server main: orchestration only
   - Registry: discovery/dispatch only
   - Tools: business logic only

3. **Open/Closed Principle**
   - Open for extension (new tools)
   - Closed for modification (server main unchanged)

4. **Scalability**
   - 10 tools = 20 lines server main
   - 100 tools = 20 lines server main
   - O(1) complexity instead of O(n)

5. **Developer Experience**
   - Self-contained tools
   - Auto-import
   - Zero boilerplate

---

## Guide: Creating a New Server

### Scenario: Generic MCP Server

We want to create a new MCP server that exposes data through standardized tools.

---

### STEP 1: Directory Structure

Create the new server structure:

```bash
cd servers/
mkdir my-server
cd my-server
mkdir src src/tools src/utils
```

**Target structure:**
```
my-server/
├── main.py                      # Entry point (standardized name)
├── src/
│   ├── tools/
│   │   ├── __init__.py          # Package + auto-registration
│   │   ├── register.py          # Registry pattern
│   │   ├── my_first_tool.py     # Tool implementation
│   │   └── my_second_tool.py    # Tool implementation
│   └── utils/
│       ├── __init__.py
│       └── load_data.py         # Data loading/connection
├── pyproject.toml
├── .python-version
└── README.md
```

**Note:** `main.py` is in the root of the server directory, not inside `src/`. This standardization allows consistent Docker and command patterns across all servers.

---

### STEP 2: pyproject.toml

Create the project configuration file:

**Minimal configuration:**
```toml
[project]
name = "my-server"
version = "0.1.0"
description = "MCP Server for [your data]"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "mcp",
    # Add your specific dependencies here
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Key points:**
- No version pins on dependencies (allows flexibility)
- No `[project.scripts]` entry point (we use `uv run main.py` directly)
- Minimal configuration for maximum compatibility

---

### STEP 3: Registry Pattern (src/tools/register.py)

**Components to create:**

1. **Type Aliases**
   - Define types for arguments, data, and results
   - Use Python 3.12+ `type` statement for clean syntax

2. **ToolNames Enum**
   - Centralized location for all tool names
   - Prevents typos and enables refactoring
   - Use `StrEnum` for string-based enum values

3. **Metadata Dataclasses**
   - `ToolMetadata`: name, description, input schema
   - `RegisteredTool`: function + metadata together
   - Provides structure and type safety

4. **Global Registry**
   - Dictionary mapping tool names to RegisteredTool objects
   - Populated automatically during import phase

5. **Decorator Function**
   - `@register_tool` decorator for tool functions
   - Accepts metadata as decorator parameters
   - Automatically registers tool in global registry

6. **Utility Functions**
   - `get_all_tools()`: Generate MCP Tool list from registry
   - `call_tool_from_registry()`: Intelligent dispatcher with parameter introspection

**Pattern identical to existing servers - promotes consistency!**

---

### STEP 4: Tool Implementation (src/tools/my_tool.py)

**File structure:**

1. **Import statements**
   - Import TextContent from mcp.types
   - Import decorator and types from register.py
   - Import utilities from utils/ package

2. **Decorator with Metadata**
   - Use `@register_tool` decorator
   - Provide name from ToolNames enum
   - Include clear description for AI
   - Define JSON schema for input parameters

3. **Function Implementation**
   - Async function signature
   - Type hints for parameters and return
   - Extract parameters from arguments dict
   - Implement business logic
   - Handle errors gracefully
   - Format output as Markdown
   - Return list of TextContent

**Key principles:**
- Tool completely self-contained
- Metadata in decorator (not duplicated elsewhere)
- Type hints for IDE support
- Internal error handling

---

### STEP 5: Auto-Registration (src/tools/__init__.py)

**Purpose:** Import all tools to trigger their decorators

**Content:**

1. **Export Registry Components**
   - Export decorator function
   - Export utility functions
   - Export type aliases and enums
   - Make public API available to server

2. **Import Tools (Auto-Registration!)**
   - Import each tool module
   - Imports execute the decorators
   - Tools automatically register themselves
   - Order matters: registry first, then tools

3. **__all__ Declaration (Optional)**
   - Explicit list of public exports
   - Documents public API
   - Controls wildcard imports

**CRITICAL:** Tool imports MUST be after registry import, because tools use the decorator from register.py!

---

### STEP 6: Utilities (src/utils/load_data.py)

**Shared utilities for all tools**

**Typical content:**

1. **Data Loading/Connection**
   - Database connection setup
   - File reading logic
   - Connection pooling
   - Configuration management

2. **Query Helpers**
   - Execute queries/requests
   - Handle errors
   - Parse responses
   - Return structured data

3. **Formatting Helpers**
   - Format data for output
   - Markdown generation
   - Data transformation
   - Consistent styling

**Principle:** If 2+ tools use the same logic, create a utility!

---

### STEP 7: Server Entry Point (main.py)

**Location:** Root of server directory (not in `src/`)

**Minimal structure - Standard pattern:**

1. **Import Statements**
   - Import MCP server components
   - Import registry functions from `src.tools.register`
   - Import data utilities from `src.utils`
   - Import standard library

2. **Global Setup**
   - Initialize data connections/loaders
   - Create server instance with descriptive name
   - Load configuration

3. **list_tools Handler** (1 line!)
   - Decorated with `@server.list_tools()`
   - Returns `get_all_tools()` from registry
   - No manual tool list needed

4. **call_tool Handler** (2-3 lines!)
   - Decorated with `@server.call_tool()`
   - Delegates to `call_tool_from_registry()`
   - Passes name, arguments, and data

5. **Main Function**
   - Async main for server loop
   - Prints startup information to stderr
   - Logs registered tools
   - Starts stdio server transport
   - Synchronous entry point calls async main

**Magic:** Server main is ALWAYS ~30 lines, regardless of number of tools!

**Example structure:**
```python
import asyncio
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.tools.register import get_all_tools, call_tool_from_registry, tool_registry
from src.utils.load_data import DATA, DATA_PATH

server = Server("my-server-name")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return get_all_tools()

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    return await call_tool_from_registry(name, arguments, DATA)

async def async_main():
    print("[START] My Server", file=sys.stderr)
    print(f"[DATA] Loaded from: {DATA_PATH}", file=sys.stderr)
    print(f"[INFO] Registered tools: {list(tool_registry.keys())}", file=sys.stderr)
    print("[READY] Server listening on stdio\n", file=sys.stderr)
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(async_main())
```

---

### STEP 8: Test & Deploy

**Local testing:**

```bash
# 1. Install dependencies
cd servers/my-server
uv sync

# 2. Test import and registration
uv run python -c "from src.tools.register import tool_registry; print(tool_registry.keys())"
# Output: dict_keys(['my_first_tool', 'my_second_tool'])

# 3. Test server
uv run main.py
# Output: [READY] Server listening on stdio

# 4. Test with Inspector
npx @modelcontextprotocol/inspector uv run main.py
# Open http://localhost:5173 in browser
# Connect to server and test tools
```

**Docker integration:**

The standardized `main.py` location allows consistent Dockerfile across all servers:

```dockerfile
CMD ["uv", "run", "main.py"]
```

---

### Complete Server Checklist

**Directory Structure:**
- [ ] `main.py` in server root (not in src/)
- [ ] `src/` directory created
- [ ] `src/tools/` directory created
- [ ] `src/utils/` directory created
- [ ] `pyproject.toml` present
- [ ] `.python-version` set

**Registry Pattern:**
- [ ] `src/tools/register.py` implemented
- [ ] Type aliases defined
- [ ] ToolNames enum populated
- [ ] Decorator `@register_tool` working
- [ ] `get_all_tools()` implemented
- [ ] `call_tool_from_registry()` implemented

**Tools Package:**
- [ ] `src/tools/__init__.py` with registry import
- [ ] `src/tools/__init__.py` with tool imports
- [ ] At least 1 tool implemented
- [ ] Tool uses decorator correctly

**Utilities:**
- [ ] `src/utils/__init__.py` empty file present
- [ ] Utility for connection/data loading
- [ ] Shared helper functions

**Server Main:**
- [ ] `main.py` in root directory
- [ ] Clean organized imports
- [ ] `list_tools()` delegates to registry
- [ ] `call_tool()` delegates to registry
- [ ] Async main function present
- [ ] Logging to stderr (not stdout!)

**Testing:**
- [ ] `uv sync` completes without errors
- [ ] Registry correctly populated
- [ ] `uv run main.py` starts without crashes
- [ ] Inspector connects successfully
- [ ] Tools executable and return results

---

### Tool File Conceptual Flow

**Abstract representation of a complete tool:**

**File:** `src/tools/my_tool.py`

```
┌─────────────────────────────────────────────────────┐
│ 1. IMPORTS                                          │
│    - TextContent from mcp.types                     │
│    - Decorator and types from register.py           │
│    - Utilities from utils/                          │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 2. DECORATOR @register_tool                         │
│    name: ToolNames.MY_TOOL                          │
│    description: "Clear description for AI..."       │
│    input_schema: {                                  │
│        properties: {                                │
│            param1: {type: "string", ...}            │
│            param2: {type: "integer", ...}           │
│        },                                           │
│        required: ["param1"]                         │
│    }                                                │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│ 3. ASYNC FUNCTION                                   │
│    async def my_tool(args, data):                   │
│                                                     │
│    A. Input Validation                              │
│       - Extract parameters from arguments dict      │
│       - Validate format and types                   │
│       - Handle missing/invalid parameters           │
│                                                     │
│    B. Business Logic                                │
│       - Query data source                           │
│       - Process data                                │
│       - Apply transformations                       │
│       - Aggregate results                           │
│                                                     │
│    C. Error Handling                                │
│       - Data not found -> clear message             │
│       - Connection errors -> fallback message       │
│       - Invalid input -> helpful guidance           │
│                                                     │
│    D. Output Formatting                             │
│       - Create structured Markdown                  │
│       - Headers, lists, bold for readability        │
│       - Consistent styling                          │
│                                                     │
│    E. Return                                        │
│       - return [TextContent(type="text", text=...)] │
└─────────────────────────────────────────────────────┘
```

**When the file is imported:**
```
Python executes decorator -> Registers tool in registry -> Tool ready!
```

---

## Best Practices

### DO

**Tool Implementation:**
- One tool = one file
- File name = tool name (snake_case)
- Use type hints for all parameters
- Handle errors gracefully with clear messages
- Format output in Markdown for readability
- Document input schema in decorator

**Utility Functions:**
- Create utility when logic used 2+ times
- Descriptive names (not abbreviations)
- Docstrings with examples
- Type hints on input/output

**Registry Pattern:**
- Use `ToolNames` enum for names
- Complete metadata in decorator
- Immutable global registry after init
- Dispatcher with introspection (1 vs 2 parameters)

**Server Main:**
- Always name it `main.py` in server root
- All prints to stderr (`file=sys.stderr`)
- Delegate everything to registry
- Informative logs on startup
- Async handlers where needed

**Project Structure:**
- `main.py` in root for standardization
- `src/` for all source code
- Consistent across all servers

### DON'T

**Common Mistakes:**
- Don't modify `call_tool()` for each new tool
- Don't duplicate tool name in enum + decorator + handler
- Don't print to stdout (breaks MCP protocol)
- Don't forget tool import in `__init__.py`
- Don't hardcode absolute paths
- Don't use tool names with typos
- Don't mix business logic in server main
- Don't put `main.py` inside `src/`

---

## Data Schema

### Biography JSON
```json
{
  "name": "Pikachu",
  "bio": "Biology [ edit | edit source ] Pikachu is..."
}
```

### Statistics CSV (41 columns)
```
Main columns:
- name, japanese_name, pokedex_number
- hp, attack, defense, sp_attack, sp_defense, speed, base_total
- type1, type2
- abilities (stringified list)
- against_* (18 columns: bug, dark, dragon, ...)
- height_m, weight_kg
- capture_rate, base_happiness, base_egg_steps
- percentage_male, generation, is_legendary
```

---

## Testing

### Local Testing

```bash
# Direct server test
cd servers/your-server
uv run main.py

# Test with Inspector
npx @modelcontextprotocol/inspector uv run main.py
```

### Step-by-Step Verification

```bash
# 1. Verify registry populated
uv run python -c "from src.tools.register import tool_registry; print(list(tool_registry.keys()))"

# 2. Verify metadata
uv run python -c "from src.tools.register import tool_registry; print(tool_registry['tool_name'].metadata)"

# 3. Test server startup
uv run main.py 2>&1 | grep "READY"

# 4. Test with Inspector
npx @modelcontextprotocol/inspector uv run main.py
```

### Inspector Usage

1. Start Inspector: `npx @modelcontextprotocol/inspector uv run main.py`
2. Open browser at `http://localhost:5173`
3. Connect to server
4. Browse available tools in left panel
5. Select a tool and fill parameters
6. Click "Call Tool" to test
7. Verify formatted output

---

## Troubleshooting

### Registry Pattern Issues

**"Tool not registered"**
- Verify import in `src/tools/__init__.py`
- Check decorator syntax `@register_tool(...)`
- Confirm name in `ToolNames` enum

**"get_all_tools() returns empty"**
- Import tools AFTER importing register.py
- Check tool files for syntax errors
- Print `tool_registry.keys()` for debugging

**"Tool executed but wrong results"**
- Verify introspection signature correct
- Check function parameters match (1 vs 2 params)
- Ensure return is always `list[TextContent]`

### General Issues

**"Module not found"**
```bash
uv sync  # Reinstall dependencies
```

**"Inspector can't connect"**
- All prints must be to stderr
- Server must stay listening (no crashes)
- Check `main.py` has proper async setup

**"Import errors from main.py"**
- Verify imports use `from src.tools...`
- Check `src/` has `__init__.py` files
- Ensure working directory is server root

---

## Resources

### MCP (Model Context Protocol)
- [Official Documentation](https://modelcontextprotocol.io/)
- [Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Awesome MCP Servers](https://github.com/punkpeye/awesome-mcp-servers)

### Patterns & Architecture
- [Registry Pattern](https://en.wikipedia.org/wiki/Service_locator_pattern)
- [Decorator Pattern](https://refactoring.guru/design-patterns/decorator/python)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

### Docker MCP Toolkit
- [Docker MCP Catalog](https://hub.docker.com/mcp)
- [Toolkit Documentation](https://docs.docker.com/ai/mcp-catalog-and-toolkit/toolkit/)

---

## Contributing

### Workflow

1. Fork & Clone repository
2. Create feature branch (`git checkout -b feature/new-server`)
3. Develop following registry pattern
4. Test locally with Inspector
5. Commit & Push with descriptive messages
6. Open Pull Request with:
   - Server/tool description
   - Output screenshots
   - Usage examples

### Code Style

- Python 3.12+ with modern type hints
- Async/await for tool functions
- Google-style docstrings
- Descriptive names (no abbreviations)
- Black formatter (100 character line)

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Authors

**Francesco Battista** - *Initial work*
- GitHub: [@frabatx](https://github.com/frabatx)
- LinkedIn: [Francesco Battista](www.linkedin.com/in/francesco-battista-4b4329147)

---

## Acknowledgments

- Anthropic for Model Context Protocol
- Docker for MCP Toolkit & Catalog
- Bulbapedia for Pokemon data
- MCP Community for inspiration

---

## Roadmap

### v1.0 - Current
- Biography Server (4 tools)
- Statistics Server (3 tools)
- Advanced Registry Pattern
- Shared utilities

### v1.1 - Next
- Graph Server
- Anime Server (semantic search)
- Docker Compose orchestration

### v2.0 - Future
- Docker MCP Catalog publishing
- Team builder tool
- Battle simulator
- WebUI for server management

---

## Support

- **Issues**: [GitHub Issues](https://github.com/frabatx/pokemon-mcp-servers/issues)
- **Discussions**: [GitHub Discussions](https://github.com/frabatx/pokemon-mcp-servers/discussions)

---

<div align="center">

**If this project is useful to you, leave a star!**

Made with care for Pokemon trainers and AI enthusiasts

</div>
