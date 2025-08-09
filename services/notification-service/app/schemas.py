from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

class NotificationBase(BaseModel):
    title: str
    message: str
    notification_type: str
    meta_data: Optional[Dict[str, Any]] = None

class NotificationCreate(NotificationBase):
    user_id: str

class NotificationResponse(NotificationBase):
    id: UUID
    user_id: str
    status: str
    created_at: datetime
    read_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TaskStatusBase(BaseModel):
    task_type: str
    status: str
    progress: int = 0
    message: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None

class TaskStatusCreate(TaskStatusBase):
    task_id: str
    user_id: str

class TaskStatusUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = None
    message: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None

class TaskStatusResponse(TaskStatusBase):
    id: UUID
    task_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class WebSocketMessage(BaseModel):
    type: str  # notification, task_status, etc.
    data: Dict[str, Any] 