from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user_id
from app.models.common import SuccessMessage
from app.models.goal import (
    GoalCreate,
    GoalListResponse,
    GoalResponse,
    GoalUpdate,
    GoalWithSubgoals,
)
from app.services.goal_service import GoalService

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.get("/", response_model=GoalListResponse)
async def list_goals(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    client_id: Optional[UUID] = None,
    goal_type: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    user_id: UUID = Depends(get_current_user_id),
):
    """List all goals with optional filters and pagination."""
    service = GoalService(user_id)
    result = await service.list_goals(
        page=page,
        limit=limit,
        client_id=client_id,
        goal_type=goal_type,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return GoalListResponse(**result)


@router.post("/", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    data: GoalCreate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a new goal."""
    service = GoalService(user_id)
    try:
        goal = await service.create_goal(data)
        return GoalResponse(**goal)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create goal: {str(e)}",
        )


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Get goal by ID."""
    service = GoalService(user_id)
    goal = await service.get_goal(goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    return GoalResponse(**goal)


@router.get("/{goal_id}/with-subgoals", response_model=GoalWithSubgoals)
async def get_goal_with_subgoals(
    goal_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Get goal with all sub-goals."""
    service = GoalService(user_id)
    try:
        goal_with_subgoals = await service.get_with_subgoals(goal_id)
        return goal_with_subgoals
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get goal with subgoals: {str(e)}",
        )


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: UUID,
    data: GoalUpdate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Update goal."""
    service = GoalService(user_id)
    try:
        goal = await service.update_goal(goal_id, data)
        return GoalResponse(**goal)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update goal: {str(e)}",
        )


@router.delete("/{goal_id}", response_model=SuccessMessage)
async def delete_goal(
    goal_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Delete goal and its sub-goals."""
    service = GoalService(user_id)
    try:
        await service.delete_goal(goal_id)
        return SuccessMessage(message="Goal deleted successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete goal: {str(e)}",
        )


@router.patch("/{goal_id}/progress", response_model=GoalResponse)
async def update_progress(
    goal_id: UUID,
    current_investment: float = Query(..., ge=0, description="Current investment amount"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Update goal progress."""
    service = GoalService(user_id)
    try:
        goal = await service.update_progress(goal_id, current_investment)
        return GoalResponse(**goal)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update progress: {str(e)}",
        )


@router.get("/client/{client_id}", response_model=List[GoalResponse])
async def get_client_goals(
    client_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Get all goals for a client."""
    service = GoalService(user_id)
    try:
        goals = await service.get_client_goals(client_id)
        return [GoalResponse(**goal) for goal in goals]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client goals: {str(e)}",
        )
