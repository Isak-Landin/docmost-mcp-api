# Configuration

All configuration is supplied via environment variables. Copy `env.example` to `.env` and fill in real values. There is no hardcoding in the application code.

## Database connection

Two modes are supported. `DOCMOST_DB_URL` takes priority when set.

### Option A — Full DSN

| Variable | Default | Description |
|---|---|---|
| `DOCMOST_DB_URL` | _(empty)_ | Full PostgreSQL DSN, e.g. `postgresql://docmost:PASSWORD@db:5432/docmost`. Takes priority over individual components when set. |

### Option B — Individual components (used when `DOCMOST_DB_URL` is not set)

| Variable | Default | Description |
|---|---|---|
| `DOCMOST_DB_HOST` | `db` | Hostname of the Docmost PostgreSQL container on the shared Docker network |
| `DOCMOST_DB_PORT` | `5432` | PostgreSQL port |
| `DOCMOST_DB_NAME` | `docmost` | Database name |
| `DOCMOST_DB_USER` | `docmost` | Database user |
| `DOCMOST_DB_PASSWORD` | _(empty)_ | Database password |

## Server bind

| Variable | Default | Description |
|---|---|---|
| `LISTEN_HOST` | `0.0.0.0` | Address to bind the uvicorn server to |
| `LISTEN_PORT` | `8099` | Internal port the uvicorn server listens on |
| `EXTERNAL_PORT` | `8099` | External port published by Docker Compose |

## MCP transport security

| Variable | Default | Description |
|---|---|---|
| `MCP_ALLOWED_HOSTS` | _(empty)_ | Comma-separated list of Host header values the MCP transport will accept. Required when the service is behind a reverse proxy with a custom domain. If empty, DNS-rebinding protection is disabled (not recommended for production). Example: `mcp-docmost.isaklandin.com` |

## Logging

| Variable | Default | Description |
|---|---|---|
| `MODE` | `dev` | `dev` or `prod` |
| `LOG_LEVEL` | `INFO` | `ALL`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` |

## DSN construction logic (`app/db.py`)

```
if DOCMOST_DB_URL is set and non-empty:
    use DOCMOST_DB_URL as DSN
else:
    build DSN from DOCMOST_DB_HOST, DOCMOST_DB_PORT, DOCMOST_DB_NAME, DOCMOST_DB_USER, DOCMOST_DB_PASSWORD
```
