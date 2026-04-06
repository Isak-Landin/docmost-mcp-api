from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.db import get_conn
from app.models import PageOut
from app.text_utils import reformat_text

router = APIRouter(prefix="/spaces/{space_id}/pages", tags=["pages"])


def _assert_space_exists(cur, space_id: UUID) -> dict:
    cur.execute(
        "SELECT id, workspace_id FROM public.spaces WHERE id = %s AND deleted_at IS NULL LIMIT 1",
        (str(space_id),),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Space not found")
    return dict(row)


def _assert_page_in_space(cur, page_id: UUID, space_id: UUID) -> dict:
    cur.execute(
        """
        SELECT id, slug_id, title, icon, position, parent_page_id, creator_id,
               last_updated_by_id, space_id, workspace_id, is_locked,
               text_content, created_at, updated_at
        FROM public.pages
        WHERE id = %s AND space_id = %s AND deleted_at IS NULL
        LIMIT 1
        """,
        (str(page_id), str(space_id)),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Page not found in this space")
    return dict(row)


def _format_page(row: dict) -> dict:
    row = dict(row)
    if row.get("text_content"):
        row["text_content"] = reformat_text(row["text_content"])
    return row


@router.get(
    "",
    response_model=List[PageOut],
    summary="List pages in a space",
    description=(
        "Returns all non-deleted pages belonging to the given space, ordered by creation date. "
        "`text_content` is returned normalized: repeated newline runs and repeated `+` storage "
        "noise are collapsed."
    ),
)
def list_pages(space_id: UUID):
    sql = """
        SELECT id, slug_id, title, icon, position, parent_page_id, creator_id,
               last_updated_by_id, space_id, workspace_id, is_locked,
               text_content, created_at, updated_at
        FROM public.pages
        WHERE space_id = %s AND deleted_at IS NULL
        ORDER BY created_at ASC
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            _assert_space_exists(cur, space_id)
            cur.execute(sql, (str(space_id),))
            rows = cur.fetchall()
    return [_format_page(r) for r in rows]


@router.get(
    "/{page_id}",
    response_model=PageOut,
    summary="Get a page",
    description=(
        "Returns a single page by its UUID, scoped to the given space. "
        "Returns 404 if the page does not exist, is deleted, or belongs to a different space."
    ),
)
def get_page(space_id: UUID, page_id: UUID):
    with get_conn() as conn:
        with conn.cursor() as cur:
            _assert_space_exists(cur, space_id)
            row = _assert_page_in_space(cur, page_id, space_id)
    return _format_page(row)
