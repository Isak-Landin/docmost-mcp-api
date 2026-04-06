from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class SpaceOut(BaseModel):
    id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    slug: str
    visibility: str
    default_role: str
    creator_id: Optional[UUID] = None
    workspace_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PageOut(BaseModel):
    id: UUID
    slug_id: str
    title: Optional[str] = None
    icon: Optional[str] = None
    position: Optional[str] = None
    parent_page_id: Optional[UUID] = None
    creator_id: Optional[UUID] = None
    last_updated_by_id: Optional[UUID] = None
    space_id: UUID
    workspace_id: UUID
    is_locked: bool
    text_content: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PageCreate(BaseModel):
    title: str
    parent_page_id: Optional[UUID] = None
    text_content: Optional[str] = None


class PageUpdate(BaseModel):
    title: Optional[str] = None
    parent_page_id: Optional[UUID] = None
    text_content: Optional[str] = None
