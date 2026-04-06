# Deployment

## Overview

The service is deployed as a Docker container on the same server as the live Docmost stack, joined to the same Docker network so it can reach the Docmost PostgreSQL container.

## Docker Compose

`docker-compose.yml` defines one service: `docmost-mcp`.

Key configuration:
- Reads env from `.env` via `env_file`
- Sets DB and server env vars explicitly from `.env` values
- Publishes `EXTERNAL_PORT` (default 8099) → `LISTEN_PORT` (default 8099)
- Joins the `docmost_network` Docker network (external, expected to already exist as `docmost_default`)

## Network requirement

The `docmost_network` must already exist as an external Docker network named `docmost_default`. This is the network created by the live Docmost Docker Compose stack.

If your Docmost network has a different name, update the `networks.docmost_network.name` value in `docker-compose.yml`.

## Setup steps

1. Clone this repository onto the server running Docmost
2. Copy `env.example` to `.env` and fill in values (DB credentials, allowed MCP hosts)
3. Ensure the `docmost_default` Docker network exists
4. Run:
   ```bash
   docker compose up -d --build
   ```
5. Verify with:
   ```bash
   curl http://localhost:8099/health
   # → {"ok": true}
   ```

## Dockerfile

The Dockerfile installs Python dependencies from `requirements.txt` and runs:
```
python -m app.main
```

## Copilot CLI integration

On the remote machine (where Copilot CLI runs), add the MCP server in your Copilot CLI settings pointing to:
```
https://<YOUR_HOST>:<EXTERNAL_PORT>/mcp
```

If using a reverse proxy with a custom domain, set `MCP_ALLOWED_HOSTS` in `.env` to that domain.

## Runtime defaults

| Setting | Default |
|---|---|
| Listen host | `0.0.0.0` |
| Listen port | `8099` |
| External port | `8099` |
