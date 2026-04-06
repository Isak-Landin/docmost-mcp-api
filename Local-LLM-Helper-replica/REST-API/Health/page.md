# Health

## `GET /health`

Returns `{"ok": true}` when the service process is running and reachable.

**This does not verify live database connectivity.** It is a process-level liveness check only.

### Response

```json
{"ok": true}
```

### Implementation

`app/routers/health.py` — returns a `JSONResponse` directly, no database call, no model validation.
