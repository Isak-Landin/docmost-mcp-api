# REST API

The REST API is served by FastAPI at the root of the service. All routes are read-only.

## Route summary

| Method | Path | Router module | Description |
|---|---|---|---|
| `GET` | `/health` | `routers/health.py` | Process health check |
| `GET` | `/spaces` | `routers/spaces.py` | List all non-deleted spaces |
| `GET` | `/spaces/{space_id}` | `routers/spaces.py` | Get one space |
| `GET` | `/spaces/{space_id}/tree` | `routers/spaces.py` | Get nested page tree for a space |
| `GET` | `/spaces/{space_id}/pages` | `routers/pages.py` | List all pages in a space |
| `GET` | `/spaces/{space_id}/pages/{page_id}` | `routers/pages.py` | Get one page in its space |
| `GET` | `/spaces/{space_id}/replica-structure` | `routers/replica.py` | Get deterministic local replica layout for a space |
| `GET` | `/replica/standards` | `routers/replica.py` | Get local replica naming, structure, and sync rules |
| `GET` | `/replica/resolve-directory-name` | `routers/replica.py` | Resolve local directory name for a page title |

## Shared HTTP error codes

| Code | Meaning |
|---|---|
| `404` | Space or page not found (deleted or never existed) |
| `503` | Docmost database connection failed |

## Lookup flow

The API is intentionally **space-first**:

1. Call `GET /spaces` to get the UUID of the target space
2. Use that UUID as `space_id` in all further calls
3. Use `GET /spaces/{space_id}/tree` for the full nested hierarchy
4. Use `GET /spaces/{space_id}/pages` for the flat page list
5. Use `GET /spaces/{space_id}/pages/{page_id}` only once you have the page UUID

Page lookup is not global. Pages are always scoped to a space.

## Interactive docs

FastAPI auto-generates OpenAPI docs. Available at `/docs` and `/redoc` when the service is running.
