from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ScheduledNotificationCreate(BaseModel):
    notification_type: str  # morning_schedule, afternoon_progress, eod_summary, greeting_gm, etc.
    channel: str  # email, whatsapp
    scheduled_time: datetime
    content: Optional[Dict[str, Any]] = None


class ScheduledNotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    notification_type: str
    channel: str
    scheduled_time: datetime
    sent_at: Optional[datetime] = None
    status: str
    content: Optional[Dict[str, Any]] = None
    external_message_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScheduledNotificationListResponse(BaseModel):
    notifications: List[ScheduledNotificationResponse]
    total: int


class DailyScheduleContent(BaseModel):
    date: date
    tasks: List[Dict[str, Any]]
    touchpoints: List[Dict[str, Any]]
    followups: List[Dict[str, Any]]
    birthdays: List[Dict[str, Any]]
    stats: Dict[str, Any]


class ProgressContent(BaseModel):
    completed_count: int
    remaining_count: int
    completed_tasks: List[Dict[str, Any]]
    remaining_tasks: List[Dict[str, Any]]


class EODContent(BaseModel):
    completed_count: int
    carry_forward_count: int
    completed_tasks: List[Dict[str, Any]]
    carry_forward_tasks: List[Dict[str, Any]]
    tomorrow_preview: Optional[Dict[str, Any]] = None
