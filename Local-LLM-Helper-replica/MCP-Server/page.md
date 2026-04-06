# MCP Server

The MCP server is implemented with `FastMCP` (from the `mcp` library) in `app/mcp_server.py`. It is mounted at `/` under the FastAPI app and exposes the MCP endpoint at `/mcp`.

## Lifecycle

The MCP session manager runs inside the FastAPI lifespan context in `app/main.py`:

```python
@asynccontextmanager
async def app_lifespan(_: FastAPI):
    async with mcp.session_manager.run():
        yield
```

## Transport security

Controlled by the `MCP_ALLOWED_HOSTS` environment variable.

- If `MCP_ALLOWED_HOSTS` is set: only those Host headers are accepted (DNS-rebinding protection enabled)
- If `MCP_ALLOWED_HOSTS` is empty: DNS-rebinding protection is disabled

## Exposed tools

All tools are read-only. They delegate to the same functions used by the REST routers.

| Tool | Input | Description |
|---|---|---|
| `list_spaces` | _(none)_ | List all non-deleted spaces |
| `get_space` | `space_id: UUID` | Get one space by UUID |
| `get_space_tree` | `space_id: UUID` | Get the nested page tree for a space |
| `get_replica_standards` | _(none)_ | Get local replica naming, layout, and sync rules |
| `resolve_replica_directory_name` | `title`, `slug_id?`, `page_id?`, `existing_dir_names?` | Resolve the local directory name for a page title |
| `get_replica_structure` | `space_id: UUID` | Get the deterministic local replica layout for a space |
| `list_pages` | `space_id: UUID` | List all pages in a space |
| `get_page` | `space_id: UUID`, `page_id: UUID` | Get one page by UUID within its space |

## Error handling

| Source error | MCP error |
|---|---|
| `DocmostConnectionError` | `ToolError` |
| `SpaceNotFoundError` | `ToolError` |
| `PageNotFoundError` | `ToolError` |

## Built-in instructions (published to MCP clients)

The `FastMCP` instance includes a `SERVER_INSTRUCTIONS` string that guides MCP clients on how to use the server. Key rules published:

- This server is strictly read-only
- Start with `list_spaces` when you need to identify the correct space
- Use `get_space_tree` for the full nested hierarchy
- Use `get_replica_structure` for the deterministic local replica layout
- Pages are always space-scoped
- Treat `text_content` as normalized plain text
- If local replica changes exist, treat the local replica as the working source of truth
- After local-only edits, remote Docmost may be stale until the user manually syncs back
