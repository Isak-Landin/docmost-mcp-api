# Data Models

All output models are defined in `app/models.py` using Pydantic v2. All models use `model_config = {"from_attributes": True}` to support ORM-style construction from database row dicts.

## SpaceOut

Returned by `list_spaces`, `get_space`.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Space UUID |
| `name` | str? | Display name |
| `description` | str? | Optional description |
| `slug` | str | URL-friendly identifier |
| `visibility` | str | `public` or `private` |
| `default_role` | str | Default member role |
| `creator_id` | UUID? | UUID of creating user |
| `workspace_id` | UUID | Parent workspace UUID |
| `created_at` | datetime | |
| `updated_at` | datetime | |

## SpaceSummaryOut

Embedded in tree and replica responses where full space detail is not needed.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Space UUID |
| `name` | str? | Display name |
| `slug` | str | URL-friendly identifier |

## PageOut

Returned by `list_pages`, `get_page`.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Page UUID |
| `slug_id` | str | Short URL-friendly identifier |
| `title` | str? | Page title |
| `icon` | str? | Emoji or icon identifier |
| `position` | str? | Sort position within parent |
| `parent_page_id` | UUID? | Parent page UUID, or null for root pages |
| `creator_id` | UUID? | UUID of creating user |
| `last_updated_by_id` | UUID? | UUID of last updating user |
| `space_id` | UUID | Space this page belongs to |
| `workspace_id` | UUID | Parent workspace UUID |
| `is_locked` | bool | Whether page is locked for editing |
| `text_content` | str? | Normalized plain-text content |
| `created_at` | datetime | |
| `updated_at` | datetime | |

## PageTreeNode

Used in `SpaceTreeOut` and recursively in tree responses.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Page UUID |
| `title` | str? | Page title |
| `slug_id` | str | Short URL-friendly identifier |
| `icon` | str? | Emoji or icon identifier |
| `parent_page_id` | UUID? | Parent page UUID |
| `position` | str? | Sort position |
| `has_children` | bool | Whether this node has child pages |
| `children` | list[PageTreeNode] | Recursively nested child nodes |

## SpaceTreeOut

Returned by `get_space_tree`.

| Field | Type | Description |
|---|---|---|
| `space` | SpaceSummaryOut | Space summary |
| `root_pages` | list[PageTreeNode] | Top-level pages with nested descendants |
| `orphan_pages` | list[PageTreeNode] | Pages whose parent is missing or unreachable |

## ReplicaStandardsOut

Returned by `get_replica_standards`. Contains all naming, layout, and sync policy strings as fields. See the Replica System page for what each policy means.

## ReplicaNameResolutionOut

Returned by `resolve_replica_directory_name`.

| Field | Type | Description |
|---|---|---|
| `input_title` | str | Original requested title |
| `slug_id` | str? | Slug identifier provided |
| `page_id` | UUID? | Page UUID provided |
| `sanitized_title` | str | Filesystem-safe form of the title |
| `local_dir_name` | str | Resolved final directory name |
| `collision_strategy` | str | Strategy used: `title`, `title_plus_slug_id`, `title_plus_short_page_id`, or `title_plus_numeric_fallback` |

## ReplicaTreeNode

Represents one page in the local replica tree. Returned nested in `ReplicaStructureOut`.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Remote page UUID |
| `title` | str? | Page title |
| `slug_id` | str | Short identifier |
| `parent_page_id` | UUID? | Parent page UUID |
| `local_dir_name` | str | Resolved directory name at this level |
| `local_dir_path` | str | Replica-relative directory path |
| `content_file_path` | str | Replica-relative path to `page.md` |
| `meta_file_path` | str | Replica-relative path to `_meta.json` |
| `children` | list[ReplicaTreeNode] | Nested child replicas |

## ReplicaStructureOut

Returned by `get_replica_structure`.

| Field | Type | Description |
|---|---|---|
| `space` | SpaceSummaryOut | Space summary |
| `replica_root` | str | Replica root directory path |
| `replica_meta_file_path` | str | Path to `_replica.json` |
| `tree_cache_file_path` | str | Path to `_tree.json` |
| `standards` | ReplicaStandardsOut | Embedded standards |
| `root_pages` | list[ReplicaTreeNode] | Root-level replica nodes |
| `orphan_pages` | list[ReplicaTreeNode] | Orphan replica nodes |
