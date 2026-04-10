"""Pydantic response models matching the GivEnergy Cloud API format."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class DataResponse(BaseModel):
    data: Any


class PaginationLinks(BaseModel):
    first: str
    last: str
    prev: Optional[str] = None
    next: Optional[str] = None


class PaginationMeta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    current_page: int
    from_: int = Field(default=1, alias="from")
    last_page: int
    path: str
    per_page: int
    to: int
    total: int


class PaginatedResponse(BaseModel):
    data: list[Any]
    links: PaginationLinks
    meta: PaginationMeta


class ErrorResponse(BaseModel):
    message: str
    errors: dict[str, list[str]] = {}
