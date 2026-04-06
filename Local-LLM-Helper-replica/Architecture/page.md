# Architecture

## Layer overview

```
Copilot CLI / MCP client
        │
        │  HTTPS  (remote machine)
        ▼
┌─────────────────────────────────────────────────────┐
│  docmost-mcp container  (same server as Docmost)    │
│                                                     │
│  FastAPI app  (app/main.py)                         │
│    ├── /health          → routers/health.py         │
│    ├── /spaces/*        → routers/spaces.py         │
│    ├── /spaces/*/pages* → routers/pages.py          │
│    ├── /replica/*       → routers/replica.py        │
│    └── /mcp             → FastMCP sub-app           │
│                                                     │
│  MCP layer  (app/mcp_server.py)                     │
│    └── 8 read-only tools                            │
│                                                     │
│  Business logic  (app/docmost.py)                   │
│    └── space + page queries, tree builder           │
│                                                     │
│  Replica logic  (app/replica.py)                    │
│    └── standards, name resolver, structure builder  │
│                                                     │
│  DB layer  (app/db.py)                              │
│    └── psycopg2 + RealDictCursor, context manager   │
└──────────────┬──────────────────────────────────────┘
               │  TCP / PostgreSQL  (Docker network)
               ▼
        Docmost PostgreSQL container
```

## Module responsibilities

| Module | Responsibility |
|---|---|
| `app/main.py` | FastAPI app factory, router registration, MCP session lifespan |
| `app/mcp_server.py` | FastMCP instance, MCP tool definitions, transport security config |
| `app/docmost.py` | SQL queries for spaces and pages, tree builder, error types |
| `app/replica.py` | Replica standards, directory name resolver, replica structure builder |
| `app/models.py` | All Pydantic output models |
| `app/db.py` | Database DSN construction, `get_conn()` context manager |
| `app/text_utils.py` | `reformat_text()` — collapses Docmost storage noise in `text_content` |
| `app/routers/health.py` | `GET /health` |
| `app/routers/spaces.py` | `GET /spaces`, `/spaces/{id}`, `/spaces/{id}/tree` |
| `app/routers/pages.py` | `GET /spaces/{id}/pages`, `/spaces/{id}/pages/{page_id}` |
| `app/routers/replica.py` | `GET /replica/standards`, `/replica/resolve-directory-name`, `/spaces/{id}/replica-structure` |

## Request flow (REST)

1. FastAPI router handler receives request
2. Handler calls the corresponding function in `app/docmost.py` (or `app/replica.py` for replica routes)
3. `docmost.py` opens a DB connection via `app/db.get_conn()`, executes SQL, closes connection
4. Row data is mapped to Pydantic models
5. Text content passes through `app/text_utils.reformat_text()` before model construction
6. Pydantic model is returned as JSON

## Request flow (MCP)

1. MCP client calls a tool on the `/mcp` endpoint
2. FastMCP dispatches to the matching tool function in `app/mcp_server.py`
3. Tool function delegates to the same `app/docmost.py` / `app/replica.py` functions used by the REST routers
4. Database errors become `ToolError`, not-found errors become `ToolError`
5. Result is returned as a JSON MCP response

## Networking

The container must be on the same Docker network as Docmost (`docmost_default`). The PostgreSQL container is reachable inside that network at the hostname set by `DOCMOST_DB_HOST`.

The MCP endpoint is exposed externally (via `EXTERNAL_PORT`, default 8099). Copilot CLI on a remote machine connects to `https://<host>:<port>/mcp`.
