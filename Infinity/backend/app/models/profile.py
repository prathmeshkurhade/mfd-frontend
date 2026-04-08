from datetime import datetime, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.constants.enums import GenderType


class ProfileCreate(BaseModel):
    name: str = Field(..., max_length=255)
    phone: str = Field(..., pattern=r"^\+91[0-9]{10}$")
    age: Optional[int] = Field(None, ge=18, le=100)
    gender: Optional[GenderType] = None
    area: Optional[str] = None
    num_employees: int = Field(0, ge=0)
    employee_names: Optional[str] = None
    eod_time: str = Field("18:00", pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    morning_schedule_time: Optional[time] = time(7, 0)
    afternoon_schedule_time: Optional[time] = time(14, 0)
    eod_schedule_time: Optional[time] = time(19, 0)
    whatsapp_number: Optional[str] = None
    email_daily_enabled: Optional[bool] = True
    whatsapp_daily_enabled: Optional[bool] = True
    whatsapp_greetings_enabled: Optional[bool] = True


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, pattern=r"^\+91[0-9]{10}$")
    age: Optional[int] = Field(None, ge=18, le=100)
    gender: Optional[GenderType] = None
    area: Optional[str] = None
    num_employees: Optional[int] = Field(None, ge=0)
    employee_names: Optional[str] = None
    eod_time: Optional[str] = Field(None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    notification_email: Optional[bool] = None
    notification_whatsapp: Optional[bool] = None
    notification_eod: Optional[bool] = None
    morning_schedule_time: Optional[time] = None
    afternoon_schedule_time: Optional[time] = None
    eod_schedule_time: Optional[time] = None
    whatsapp_number: Optional[str] = None
    email_daily_enabled: Optional[bool] = None
    whatsapp_daily_enabled: Optional[bool] = None
    whatsapp_greetings_enabled: Optional[bool] = None


class ProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    phone: str
    age: Optional[int] = None
    gender: Optional[GenderType] = None
    area: Optional[str] = None
    num_employees: int = 0
    employee_names: Optional[str] = None
    eod_time: Optional[str] = None
    google_connected: bool = False
    google_email: Optional[str] = None
    notification_email: bool = True
    notification_whatsapp: bool = True
    notification_eod: bool = True
    morning_schedule_time: Optional[time] = None
    afternoon_schedule_time: Optional[time] = None
    eod_schedule_time: Optional[time] = None
    whatsapp_number: Optional[str] = None
    email_daily_enabled: bool = True
    whatsapp_daily_enabled: bool = True
    whatsapp_greetings_enabled: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GoogleAuthURL(BaseModel):
    auth_url: str


class GoogleAuthCallback(BaseModel):
    code: str
    state: Optional[str] = None


class GoogleConnectResponse(BaseModel):
    message: str
    google_email: Optional[str] = None
    drive_folder_id: Optional[str] = None
    sheet_id: Optional[str] = None
