# Pages

All page routes are scoped to a space. You must provide the `space_id` UUID.

## `GET /spaces/{space_id}/pages`

Returns all non-deleted pages belonging to the given space, ordered by creation date.

`text_content` is returned normalized: repeated newline runs and repeated `+` storage noise are collapsed.

### Path parameters

| Parameter | Type | Description |
|---|---|---|
| `space_id` | UUID | Space UUID from `GET /spaces` |

### Response model: `list[PageOut]`

### Errors

| Code | Reason |
|---|---|
| `404` | Space not found or deleted |
| `503` | Database connection failed |

---

## `GET /spaces/{space_id}/pages/{page_id}`

Returns a single page by UUID, scoped to the given space.

Returns `404` if the page does not exist, is deleted, or belongs to a different space.

### Path parameters

| Parameter | Type | Description |
|---|---|---|
| `space_id` | UUID | Space UUID |
| `page_id` | UUID | Page UUID from `GET /spaces/{space_id}/pages` |

### Response model: `PageOut`

### Errors

| Code | Reason |
|---|---|
| `404` | Space not found, or page not found in this space |
| `503` | Database connection failed |

---

## `text_content` normalization

The raw `text_content` stored in Docmost contains storage artefacts:
- Runs of 3 or more `+` characters are collapsed to a single `+`
- Runs of 2 or more newlines are collapsed to a single newline
- Leading and trailing whitespace is stripped

Applied by `app/text_utils.reformat_text()` before the `PageOut` model is constructed.
