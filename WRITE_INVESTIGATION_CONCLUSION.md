# Content Write Investigation — Conclusion

## Root cause

Content passed to `create_page` and `update_page` was silently discarded on the remote Docmost instance.

**The cause was a Docmost version mismatch.**

The remote server was running an older version of Docmost where `CreatePageDto` and `UpdatePageDto` did **not** declare `content` or `format` as valid fields. NestJS `ValidationPipe({ whitelist: true })` strips any undeclared fields from incoming request bodies before they reach the handler — so content was accepted without error but never written to the database.

In Docmost **v0.71.1** (`docmost/docmost:latest`), both fields are fully declared with proper validation decorators:

```js
// /app/apps/server/dist/core/page/dto/create-page.dto.js
@IsOptional()
content

@ValidateIf(...) @IsIn(['json', 'markdown', 'html'])
format
```

## Verification

Confirmed by:
1. Spinning up a local Docmost stack (`~/docmost-local/`) using `docmost/docmost:latest`
2. Running the MCP container (`docmost-mcp-local-test`) against it with inline env overrides
3. Creating a page with markdown content via `POST /spaces/{id}/pages` — content appeared in the Docmost UI immediately

## What was correct all along

- `app/write/docmost.py` — sends `content` + `format: "markdown"` correctly
- `docs/docmost-write-api.md` — accurately documents `content`/`format` field support (written from container source inspection)
- `app/routers/write.py` — passes content through to the Docmost API without modification

No code changes are required.

## Resolution

Update the remote Docmost instance:

```bash
docker compose pull docmost
docker compose up -d --no-deps docmost
```

This is safe — no volumes are affected. After the update, `create_page` and `update_page` will write content as expected.
