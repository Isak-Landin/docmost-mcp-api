# Database Layer

Implemented in `app/db.py`. Provides a single context manager for acquiring and releasing PostgreSQL connections.

## Connection management

```python
with get_conn() as conn:
    with conn.cursor() as cur:
        cur.execute(...)
        rows = cur.fetchall()
```

`get_conn()` is a context manager that:
1. Constructs the DSN (from env vars)
2. Opens a `psycopg2` connection with `RealDictCursor` (rows are returned as dicts)
3. Yields the connection
4. On success: commits the transaction
5. On `OperationalError`: rolls back and raises `DocmostConnectionError`
6. On any other exception: rolls back and re-raises
7. Always closes the connection in the `finally` block

## DSN construction

See the [Configuration](../Configuration/page.md) page. `DOCMOST_DB_URL` takes priority.

## Cursor type

`RealDictCursor` — all rows are returned as `dict` objects, not tuples. This allows row data to be passed directly to Pydantic model constructors using `**row`.

## Error types

| Exception | Raised when |
|---|---|
| `DocmostConnectionError` | `psycopg2.OperationalError` occurs (connection refused, bad credentials, network failure) |

All routers and MCP tools catch `DocmostConnectionError` and convert it to a `503` HTTP error or `ToolError` respectively.

## Notes

- All database access is synchronous (psycopg2)
- There is no connection pool; each request opens and closes its own connection
- All queries are read-only (`SELECT`); the commit is a no-op in practice but is included for correctness
