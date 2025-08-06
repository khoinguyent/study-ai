from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import httpx
from datetime import datetime

from .database import get_db, engine
from .models import Base, Notification, TaskStatus
from .schemas import (
    NotificationCreate, NotificationResponse, 
    TaskStatusCreate, TaskStatusUpdate, TaskStatusResponse,
    WebSocketMessage
)
from .config import settings
from .websocket_manager import websocket_manager
import sys
import os

# Add shared module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))
from shared import EventConsumer, EventType, BaseEvent

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize event consumer
event_consumer = EventConsumer(settings.REDIS_URL)

# Event handlers
async def handle_document_event(event: BaseEvent):
    """Handle document-related events"""
    try:
        # Create notification for user
        notification = Notification(
            user_id=event.user_id,
            title=f"Document {event.event_type.value.replace('document.', '').title()}",
            message=f"Document {event.document_id}: {event.event_type.value}",
            notification_type="document_status",
            status="unread"
        )
        
        db = next(get_db())
        db.add(notification)
        db.commit()
        
        # Send WebSocket notification
        await websocket_manager.send_personal_message(
            user_id=event.user_id,
            message={
                "type": "document_status",
                "event": event.event_type.value,
                "document_id": event.document_id,
                "message": f"Document {event.event_type.value.replace('document.', '').title()}"
            }
        )
        
    except Exception as e:
        print(f"Error handling document event: {e}")

async def handle_indexing_event(event: BaseEvent):
    """Handle indexing-related events"""
    try:
        # Create notification for user
        notification = Notification(
            user_id=event.user_id,
            title=f"Indexing {event.event_type.value.replace('indexing.', '').title()}",
            message=f"Document {event.document_id}: {event.event_type.value}",
            notification_type="indexing_status",
            status="unread"
        )
        
        db = next(get_db())
        db.add(notification)
        db.commit()
        
        # Send WebSocket notification
        await websocket_manager.send_personal_message(
            user_id=event.user_id,
            message={
                "type": "indexing_status",
                "event": event.event_type.value,
                "document_id": event.document_id,
                "message": f"Indexing {event.event_type.value.replace('indexing.', '').title()}"
            }
        )
        
    except Exception as e:
        print(f"Error handling indexing event: {e}")

async def handle_quiz_event(event: BaseEvent):
    """Handle quiz-related events"""
    try:
        # Create notification for user
        notification = Notification(
            user_id=event.user_id,
            title=f"Quiz {event.event_type.value.replace('quiz.generation.', '').title()}",
            message=f"Quiz {event.quiz_id}: {event.event_type.value}",
            notification_type="quiz_status",
            status="unread"
        )
        
        db = next(get_db())
        db.add(notification)
        db.commit()
        
        # Send WebSocket notification
        await websocket_manager.send_personal_message(
            user_id=event.user_id,
            message={
                "type": "quiz_status",
                "event": event.event_type.value,
                "quiz_id": event.quiz_id,
                "message": f"Quiz {event.event_type.value.replace('quiz.generation.', '').title()}"
            }
        )
        
    except Exception as e:
        print(f"Error handling quiz event: {e}")

# Subscribe to events
event_consumer.subscribe_to_document_events(handle_document_event)
event_consumer.subscribe_to_indexing_events(handle_indexing_event)
event_consumer.subscribe_to_quiz_events(handle_quiz_event)

# Start event consumer
event_consumer.start()

app = FastAPI(
    title="Notification Service",
    description="Real-time notifications and task status management service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def verify_auth_token(authorization: str = Depends(Header)):
    """Verify JWT token with auth service"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/verify",
                headers={"Authorization": authorization}
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            return response.json()["user_id"]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "notification-service"}

# WebSocket endpoint for real-time notifications
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket_manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # You can handle incoming messages here if needed
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

# Task Status Management
@app.post("/task-status", response_model=TaskStatusResponse)
async def create_task_status(
    task_status: TaskStatusCreate,
    db: Session = Depends(get_db)
):
    """Create a new task status"""
    db_task_status = TaskStatus(
        task_id=task_status.task_id,
        user_id=task_status.user_id,
        task_type=task_status.task_type,
        status=task_status.status,
        progress=task_status.progress,
        message=task_status.message,
        metadata=task_status.metadata
    )
    
    db.add(db_task_status)
    db.commit()
    db.refresh(db_task_status)
    
    # Send WebSocket notification
    await websocket_manager.broadcast_task_status(
        user_id=task_status.user_id,
        task_id=task_status.task_id,
        status=task_status.status,
        progress=task_status.progress,
        message=task_status.message
    )
    
    return TaskStatusResponse(
        id=db_task_status.id,
        task_id=db_task_status.task_id,
        user_id=db_task_status.user_id,
        task_type=db_task_status.task_type,
        status=db_task_status.status,
        progress=db_task_status.progress,
        message=db_task_status.message,
        metadata=db_task_status.metadata,
        created_at=db_task_status.created_at,
        updated_at=db_task_status.updated_at,
        completed_at=db_task_status.completed_at
    )

@app.put("/task-status/{task_id}", response_model=TaskStatusResponse)
async def update_task_status(
    task_id: str,
    task_update: TaskStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update task status"""
    db_task_status = db.query(TaskStatus).filter(TaskStatus.task_id == task_id).first()
    if not db_task_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task status not found"
        )
    
    # Update fields
    if task_update.status is not None:
        db_task_status.status = task_update.status
    if task_update.progress is not None:
        db_task_status.progress = task_update.progress
    if task_update.message is not None:
        db_task_status.message = task_update.message
    if task_update.metadata is not None:
        db_task_status.metadata = task_update.metadata
    
    # Set completed_at if status is completed
    if task_update.status == "completed":
        db_task_status.completed_at = datetime.utcnow()
    
    db_task_status.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_task_status)
    
    # Send WebSocket notification
    await websocket_manager.broadcast_task_status(
        user_id=db_task_status.user_id,
        task_id=db_task_status.task_id,
        status=db_task_status.status,
        progress=db_task_status.progress,
        message=db_task_status.message
    )
    
    return TaskStatusResponse(
        id=db_task_status.id,
        task_id=db_task_status.task_id,
        user_id=db_task_status.user_id,
        task_type=db_task_status.task_type,
        status=db_task_status.status,
        progress=db_task_status.progress,
        message=db_task_status.message,
        metadata=db_task_status.metadata,
        created_at=db_task_status.created_at,
        updated_at=db_task_status.updated_at,
        completed_at=db_task_status.completed_at
    )

@app.get("/task-status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get task status by task ID"""
    db_task_status = db.query(TaskStatus).filter(TaskStatus.task_id == task_id).first()
    if not db_task_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task status not found"
        )
    
    return TaskStatusResponse(
        id=db_task_status.id,
        task_id=db_task_status.task_id,
        user_id=db_task_status.user_id,
        task_type=db_task_status.task_type,
        status=db_task_status.status,
        progress=db_task_status.progress,
        message=db_task_status.message,
        metadata=db_task_status.metadata,
        created_at=db_task_status.created_at,
        updated_at=db_task_status.updated_at,
        completed_at=db_task_status.completed_at
    )

@app.get("/task-status/user/{user_id}", response_model=List[TaskStatusResponse])
async def get_user_task_statuses(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get all task statuses for a user"""
    task_statuses = db.query(TaskStatus).filter(TaskStatus.user_id == user_id).order_by(TaskStatus.created_at.desc()).all()
    
    return [
        TaskStatusResponse(
            id=task.id,
            task_id=task.task_id,
            user_id=task.user_id,
            task_type=task.task_type,
            status=task.status,
            progress=task.progress,
            message=task.message,
            metadata=task.metadata,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at
        )
        for task in task_statuses
    ]

# Notification Management
@app.post("/notifications", response_model=NotificationResponse)
async def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db)
):
    """Create a new notification"""
    db_notification = Notification(
        user_id=notification.user_id,
        title=notification.title,
        message=notification.message,
        notification_type=notification.notification_type,
        metadata=notification.metadata
    )
    
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    # Send WebSocket notification
    await websocket_manager.broadcast_notification(
        user_id=notification.user_id,
        title=notification.title,
        message=notification.message,
        notification_type=notification.notification_type
    )
    
    return NotificationResponse(
        id=db_notification.id,
        user_id=db_notification.user_id,
        title=db_notification.title,
        message=db_notification.message,
        notification_type=db_notification.notification_type,
        status=db_notification.status,
        metadata=db_notification.metadata,
        created_at=db_notification.created_at,
        read_at=db_notification.read_at
    )

@app.get("/notifications/user/{user_id}", response_model=List[NotificationResponse])
async def get_user_notifications(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get all notifications for a user"""
    notifications = db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()
    
    return [
        NotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            title=notification.title,
            message=notification.message,
            notification_type=notification.notification_type,
            status=notification.status,
            metadata=notification.metadata,
            created_at=notification.created_at,
            read_at=notification.read_at
        )
        for notification in notifications
    ]

@app.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    db_notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not db_notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    db_notification.status = "read"
    db_notification.read_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Notification marked as read"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005) 