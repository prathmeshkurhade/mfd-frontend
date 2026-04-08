from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user_id
from app.models.common import SuccessMessage
from app.models.task import (
    TaskBulkCarryForward,
    TaskBulkComplete,
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
    TodayTasksResponse,
)
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    client_id: Optional[UUID] = None,
    lead_id: Optional[UUID] = None,
    due_date: Optional[date] = None,
    sort_by: str = Query("due_date", description="Field to sort by"),
    sort_order: str = Query("asc", description="Sort order: asc or desc"),
    user_id: UUID = Depends(get_current_user_id),
):
    """List all tasks with optional filters and pagination."""
    service = TaskService(user_id)
    result = await service.list_tasks(
        page=page,
        limit=limit,
        status=status,
        priority=priority,
        client_id=client_id,
        lead_id=lead_id,
        due_date=due_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return TaskListResponse(**result)


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a new task."""
    service = TaskService(user_id)
    try:
        task = await service.create_task(data)
        return TaskResponse(**task)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}",
        )


@router.get("/today", response_model=TodayTasksResponse)
async def get_today_tasks(
    user_id: UUID = Depends(get_current_user_id),
):
    """Get today's tasks split by status."""
    service = TaskService(user_id)
    result = await service.get_today_tasks()
    return TodayTasksResponse(**result)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Get task by ID."""
    service = TaskService(user_id)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return TaskResponse(**task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Update task."""
    service = TaskService(user_id)
    try:
        task = await service.update_task(task_id, data)
        return TaskResponse(**task)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}",
        )


@router.delete("/{task_id}", response_model=SuccessMessage)
async def delete_task(
    task_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Delete task."""
    service = TaskService(user_id)
    try:
        await service.delete_task(task_id)
        return SuccessMessage(message="Task deleted successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Mark task as completed."""
    service = TaskService(user_id)
    try:
        task = await service.complete_task(task_id)
        return TaskResponse(**task)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{task_id}/carry-forward", response_model=TaskResponse)
async def carry_forward_task(
    task_id: UUID,
    new_date: date = Query(..., description="New due date"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Carry forward task to new date."""
    service = TaskService(user_id)
    try:
        task = await service.carry_forward(task_id, new_date)
        return TaskResponse(**task)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to carry forward task: {str(e)}",
        )


@router.post("/bulk-complete", response_model=SuccessMessage)
async def bulk_complete(
    data: TaskBulkComplete,
    user_id: UUID = Depends(get_current_user_id),
):
    """Bulk complete tasks."""
    service = TaskService(user_id)
    count = await service.bulk_complete(data.task_ids)
    return SuccessMessage(
        message=f"Successfully completed {count} out of {len(data.task_ids)} tasks"
    )


@router.post("/bulk-carry-forward", response_model=SuccessMessage)
async def bulk_carry_forward(
    data: TaskBulkCarryForward,
    user_id: UUID = Depends(get_current_user_id),
):
    """Bulk carry forward tasks."""
    service = TaskService(user_id)
    count = await service.bulk_carry_forward(data.task_ids, data.new_due_date)
    return SuccessMessage(
        message=f"Successfully carried forward {count} out of {len(data.task_ids)} tasks"
    )
