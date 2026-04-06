from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.db import get_conn
from app.models import SpaceOut

router = APIRouter(prefix="/spaces", tags=["spaces"])


@router.get(
    "",
    response_model=List[SpaceOut],
    summary="List all spaces",
    description="Returns all non-deleted spaces from the live Docmost database, ordered by creation date.",
)
def list_spaces():
    sql = """
        SELECT id, name, description, slug, visibility, default_role,
               creator_id, workspace_id, created_at, updated_at
        FROM public.spaces
        WHERE deleted_at IS NULL
        ORDER BY created_at ASC
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    return [dict(r) for r in rows]


@router.get(
    "/{space_id}",
    response_model=SpaceOut,
    summary="Get a space",
    description="Returns a single space by its UUID. Returns 404 if the space does not exist or has been deleted.",
)
def get_space(space_id: UUID):
    sql = """
        SELECT id, name, description, slug, visibility, default_role,
               creator_id, workspace_id, created_at, updated_at
        FROM public.spaces
        WHERE id = %s AND deleted_at IS NULL
        LIMIT 1
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (str(space_id),))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Space not found")
    return dict(row)
