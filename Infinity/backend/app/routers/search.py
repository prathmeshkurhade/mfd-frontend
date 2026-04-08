from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user_id
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/", response_model=Dict[str, Any])
async def global_search(
    q: str = Query(..., min_length=2, description="Search query (min 2 characters)"),
    limit: int = Query(20, ge=1, le=100, description="Max results per category"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Global search across all entities."""
    service = SearchService(user_id)
    try:
        results = await service.global_search(q, limit)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.get("/clients", response_model=List[Dict[str, Any]])
async def search_clients(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Search clients by name, phone, email, or area."""
    service = SearchService(user_id)
    try:
        results = await service.search_clients(q, limit)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Client search failed: {str(e)}",
        )


@router.get("/leads", response_model=List[Dict[str, Any]])
async def search_leads(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Search leads by name, phone, or email."""
    service = SearchService(user_id)
    try:
        results = await service.search_leads(q, limit)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lead search failed: {str(e)}",
        )


@router.get("/tasks", response_model=List[Dict[str, Any]])
async def search_tasks(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Search tasks by title or description."""
    service = SearchService(user_id)
    try:
        results = await service.search_tasks(q, limit)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task search failed: {str(e)}",
        )


@router.get("/recent", response_model=List[str])
async def get_recent_searches(
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Get recent search queries."""
    service = SearchService(user_id)
    try:
        results = await service.get_recent_searches(limit)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent searches: {str(e)}",
        )
