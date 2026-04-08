from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.constants.enums import TaskMediumType, TaskPriorityType, TaskStatusType


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    client_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    priority: TaskPriorityType = TaskPriorityType.medium
    medium: Optional[TaskMediumType] = None
    due_date: date
    due_time: Optional[str] = None
    all_day: Optional[bool] = None
    product_type: Optional[str] = None
    is_business_opportunity: Optional[bool] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    client_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    priority: Optional[TaskPriorityType] = None
    medium: Optional[TaskMediumType] = None
    due_date: Optional[date] = None
    due_time: Optional[str] = None
    status: Optional[TaskStatusType] = None
    all_day: Optional[bool] = None
    product_type: Optional[str] = None
    is_business_opportunity: Optional[bool] = None


class TaskResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str] = Field(None, validation_alias="description")
    client_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    client_name: Optional[str] = None
    lead_name: Optional[str] = None
    priority: TaskPriorityType
    medium: Optional[TaskMediumType] = None
    due_date: date
    due_time: Optional[str] = None
    status: TaskStatusType
    completed_at: Optional[datetime] = None
    original_due_date: Optional[date] = Field(None, validation_alias="original_date")
    carry_forward_count: int = 0
    all_day: Optional[bool] = None
    product_type: Optional[str] = None
    is_business_opportunity: Optional[bool] = None
    google_event_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class TaskBulkComplete(BaseModel):
    task_ids: List[UUID]


class TaskBulkCarryForward(BaseModel):
    task_ids: List[UUID]
    new_due_date: date


class TodayTasksResponse(BaseModel):
    pending: List[TaskResponse]
    completed: List[TaskResponse]
    overdue: List[TaskResponse]
    pending_count: int
    completed_count: int
    overdue_count: int
