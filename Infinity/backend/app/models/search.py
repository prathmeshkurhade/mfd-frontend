"""Pydantic models for Search."""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    """Individual search result item."""

    id: UUID
    entity_type: str  # client, lead, task, touchpoint, goal
    name: str  # Display name
    subtitle: Optional[str] = None  # Secondary info (phone, email, etc.)
    match_field: str  # Which field matched the query


class SearchResults(BaseModel):
    """Search results across all entities."""

    query: str
    clients: List[SearchResultItem]
    leads: List[SearchResultItem]
    tasks: List[SearchResultItem]
    touchpoints: List[SearchResultItem]
    goals: List[SearchResultItem]
    total: int
