# revit-basic-mcp

A minimal MCP (Model Context Protocol) server for Revit, enabling LLMs like Claude to interact with an active Revit session.

## Architecture

| File | Runtime | Role |
|------|---------|------|
| `main.py` | CPython 3.11+ | FastMCP server — exposes tools to the LLM |
| `startup.py` | IronPython (pyRevit) | Registers HTTP routes inside Revit |

`main.py` runs outside Revit and communicates with `startup.py` via pyRevit Routes on `http://localhost:48884`.

## Requirements

- [Revit 2024+](https://www.autodesk.com/products/revit/) with [pyRevit](https://github.com/pyrevitlabs/pyRevit) installed
- Python 3.11+ (CPython) for the MCP server
- Claude Desktop or any MCP-compatible client

## Installation

### 1. Install the pyRevit extension

Copy or clone this repo into your pyRevit extensions folder:

```
%APPDATA%\pyRevit\Extensions\
```

Or add the path manually in pyRevit Settings → Extensions.

### 2. Install the MCP server dependencies

**With uv (recommended):**
```bash
uv sync
```

**With pip:**
```bash
pip install -r requirements.txt
```

### 3. Configure Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "revit": {
      "command": "uv",
      "args": ["run", "--project", "C:/path/to/revit-mcp-basic.extension", "python", "main.py"]
    }
  }
}
```

Or with plain Python:
```json
{
  "mcpServers": {
    "revit": {
      "command": "python",
      "args": ["C:/path/to/revit-mcp-basic.extension/main.py"]
    }
  }
}
```

### 4. Start Revit

pyRevit will load `startup.py` automatically on Revit startup, registering the HTTP routes.

## Available MCP Tools

| Tool | Description |
|------|-------------|
| `get_model_snapshot` | Returns elements from the active Revit model (walls, floors, roofs, rooms, levels, …) |
| `run_pyrevit_script` | Executes arbitrary IronPython code inside the Revit session |

## License

MIT
