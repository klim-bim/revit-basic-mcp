import httpx
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("Revit MCP")

REVIT_URL = "http://localhost:48884/revit_mcp"


### HTTP communication

async def _post(endpoint: str, data: dict, timeout: float = 30.0) -> dict:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{REVIT_URL}{endpoint}", json=data)
            return r.json() if r.is_success else {"status": "error", "detail": r.text}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


async def _get(endpoint: str, timeout: float = 10.0) -> dict:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(f"{REVIT_URL}{endpoint}")
            return r.json() if r.is_success else {"status": "error", "detail": r.text}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


### Tools

@mcp.tool()
async def run_script(code: str) -> str:
    """
    Execute Python code in the active Revit session.
    Has access to `doc` (active document) and `DB` (Revit API namespace).
    Use for operations not covered by other tools.
    """
    r = await _post("/run_script/", {"code": code})
    if r.get("status") == "error":
        return f"[HTTP error] {r.get('detail', r)}"
    data = r.get("data", r)
    if isinstance(data, dict) and data.get("status") == "error":
        parts = [f"[Script error] {data.get('error', '')}"]
        if data.get("output"):
            parts.append(f"Output:\n{data['output']}")
        if data.get("traceback"):
            parts.append(f"Traceback:\n{data['traceback']}")
        return "\n".join(parts)
    return data.get("output", "") if isinstance(data, dict) else str(data)


@mcp.tool()
async def get_model_snapshot(
    categories: list = ["levels", "grids", "rooms", "walls", "floors", "roofs", "columns", "windows", "doors"]
) -> str:
    """
    Return a snapshot of placed Revit elements by category.
    Available categories: levels, grids, rooms, walls, floors, roofs, columns, windows, doors.
    Only request categories relevant to the current task to save tokens.
    """
    r = await _post("/get_model_snapshot/", {"categories": categories})
    return str(r)


if __name__ == "__main__":
    mcp.run(transport="stdio")
