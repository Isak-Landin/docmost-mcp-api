# Replica System

The replica system generates a deterministic local file layout for any Docmost space. It is implemented in `app/replica.py`.

## Purpose

Because the Docmost MCP server is read-only, the recommended usage pattern involves maintaining a **local replica** — a directory tree that mirrors remote Docmost pages as local files. The replica system standardizes how this tree is laid out so all clients agree on paths.

## Replica root

```
./{space_name}-replica/
```

Example: space "tool-ai-gateway" → `./tool-ai-gateway-replica/`

The space name is sanitized before use:
- Invalid path characters (`< > : " / \ | ? * \x00-\x1f`) → replaced with `-`
- Whitespace runs → collapsed to single space
- Multi-dash runs → collapsed to single `-`
- Trailing dots or spaces → stripped
- Windows reserved names (`CON`, `NUL`, etc.) → prefixed with `_`

## Replica root files

| File | Description |
|---|---|
| `_replica.json` | Replica-level metadata and sync state |
| `_tree.json` | Resolved tree snapshot used for the replica |

## Per-page layout

Every page maps to a **directory** inside the replica tree:

| File | Description |
|---|---|
| `page.md` | Normalized plain-text content of the page |
| `_meta.json` | Page metadata: id, title, slug_id, parent_page_id, local paths |

Child pages become nested subdirectories under the parent page's directory.

## Directory naming rules

Applied level-by-level, not globally:

1. **Base**: use the filesystem-safe page title as the directory name
2. **Sibling collision**: if two sibling pages resolve to the same base name, append `__{slug_id}` to every page in the collision set
3. **Fallback**: if `slug_id` is missing or still collides, append `__{short_page_id}` (first 8 characters of the page UUID)
4. **Numeric fallback**: if still colliding, append `__{short_page_id}-{n}` with incrementing `n`

## Source of truth rules

| Scenario | Source of truth |
|---|---|
| No local replica exists | Remote Docmost |
| Local replica exists, no local edits | Remote Docmost (refresh via `get_replica_structure`) |
| Local replica has been edited | Local replica (until manually synced back to remote) |
| After local-only edits | Remote Docmost is potentially stale |

## Editing policy

- Apply documentation edits to the **local replica**, not to remote Docmost
- When local files are edited, report which replica files changed and which remote pages they correspond to
- Prompt the user to manually copy those changes back to remote Docmost

## Using the replica tools

| When | Use |
|---|---|
| Building or refreshing an existing remote space locally | `get_replica_structure(space_id)` |
| Creating a new local-only page not yet on remote | `get_replica_standards()` + `resolve_replica_directory_name(...)` |
| Mapping a local file back to its remote page | Read `_meta.json` in the page directory |

## Implementation notes

- `_resolve_level_directory_names()` in `replica.py` resolves names for a full sibling group before assigning any, so collision detection is consistent
- The recursive `_build_replica_level()` walks the `PageTreeNode` tree from `get_space_tree()` and builds `ReplicaTreeNode` objects
- No I/O is performed; the structure is returned as a Pydantic model and it is the client's responsibility to write files
