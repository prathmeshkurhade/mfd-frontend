from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.constants.enums import DeviceType


class DeviceRegisterRequest(BaseModel):
    device_token: str = Field(..., min_length=10, description="FCM device token")
    device_type: DeviceType
    device_name: Optional[str] = Field(None, max_length=255, description="e.g., Rahul's Phone")
    device_model: Optional[str] = Field(None, max_length=255, description="e.g., Samsung S21")
    os_version: Optional[str] = Field(None, max_length=50, description="e.g., Android 13")
    app_version: Optional[str] = Field(None, max_length=50, description="e.g., 1.0.0")


class DeviceUnregisterRequest(BaseModel):
    device_token: str = Field(..., min_length=10)


class DeviceTokenRefreshRequest(BaseModel):
    old_token: str = Field(..., min_length=10)
    new_token: str = Field(..., min_length=10)


class DeviceResponse(BaseModel):
    id: UUID
    user_id: UUID
    device_token: str
    device_type: DeviceType
    device_name: Optional[str]
    device_model: Optional[str]
    os_version: Optional[str]
    app_version: Optional[str]
    is_active: bool
    last_used_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    devices: List[DeviceResponse]
    total: int
    active_count: int


class DeviceRegisterResponse(BaseModel):
    success: bool
    message: str
    device_id: Optional[UUID] = None


class PushNotificationRequest(BaseModel):
    user_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    data: Optional[dict] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[UUID] = None


class PushNotificationResponse(BaseModel):
    success: bool
    message: str
    devices_sent: int = 0
    devices_failed: int = 0
