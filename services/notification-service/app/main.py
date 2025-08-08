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

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Notification Service",
    description="Real-time notification and task status tracking service",
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

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "notification-service"}

# WebSocket endpoint for real-time notifications
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo received message for now (can be enhanced for specific functionality)
            await websocket_manager.send_personal_message(
                WebSocketMessage(type="echo", data={"message": data}),
                user_id
            )
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

# Create notification
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
        meta_data=notification.meta_data
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    # Send real-time notification via WebSocket
    await websocket_manager.broadcast_notification(
        user_id=notification.user_id,
        title=notification.title,
        message=notification.message,
        notification_type=notification.notification_type
    )
    
    return db_notification

# Get notifications for a user
@app.get("/notifications/{user_id}", response_model=List[NotificationResponse])
async def get_user_notifications(
    user_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get notifications for a specific user"""
    notifications = db.query(Notification).filter(
        Notification.user_id == user_id
    ).order_by(
        Notification.created_at.desc()
    ).limit(limit).all()
    
    return notifications

# Create task status
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
        meta_data=task_status.meta_data
    )
    db.add(db_task_status)
    db.commit()
    db.refresh(db_task_status)
    
    # Send real-time task status update via WebSocket
    await websocket_manager.broadcast_task_status(
        user_id=task_status.user_id,
        task_id=task_status.task_id,
        status=task_status.status,
        progress=task_status.progress,
        message=task_status.message
    )
    
    return db_task_status

# Update task status
@app.put("/task-status/{task_id}", response_model=TaskStatusResponse)
async def update_task_status(
    task_id: str,
    task_update: TaskStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing task status"""
    db_task_status = db.query(TaskStatus).filter(TaskStatus.task_id == task_id).first()
    if not db_task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update fields if provided
    if task_update.status:
        db_task_status.status = task_update.status
    if task_update.progress is not None:
        db_task_status.progress = task_update.progress
    if task_update.message:
        db_task_status.message = task_update.message
    if task_update.meta_data:
        db_task_status.meta_data = task_update.meta_data
    
    # Update completion time if task is completed
    if task_update.status in ["completed", "failed"]:
        db_task_status.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_task_status)
    
    # Send real-time task status update via WebSocket
    await websocket_manager.broadcast_task_status(
        user_id=db_task_status.user_id,
        task_id=task_id,
        status=db_task_status.status,
        progress=db_task_status.progress,
        message=db_task_status.message
    )
    
    return db_task_status

# Get task status
@app.get("/task-status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get status of a specific task"""
    task_status = db.query(TaskStatus).filter(TaskStatus.task_id == task_id).first()
    if not task_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task_status

# Get user's task statuses
@app.get("/users/{user_id}/tasks", response_model=List[TaskStatusResponse])
async def get_user_tasks(
    user_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get task statuses for a specific user"""
    task_statuses = db.query(TaskStatus).filter(
        TaskStatus.user_id == user_id
    ).order_by(
        TaskStatus.created_at.desc()
    ).limit(limit).all()
    
    return task_statuses

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005) 