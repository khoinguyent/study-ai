"""
Notification Service for Study AI Platform
Handles real-time notifications and event processing
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from .database import get_db, create_tables
from .models import Notification, TaskStatus
from .schemas import NotificationCreate, NotificationResponse, TaskStatusCreate, TaskStatusResponse
from .websocket_manager import WebSocketManager
from .config import settings
# Temporarily commented out to fix import issues
# from shared.event_consumer import EventConsumer
# from shared.events import EventType, BaseEvent
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Notification Service",
    description="Real-time notification and event processing service",
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

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()
    # Start event consumer with retry logic
    await start_event_consumer_with_retry()

# Initialize WebSocket manager
websocket_manager = WebSocketManager()

# Event consumer - will be initialized in start_event_consumer_with_retry
event_consumer = None

async def start_event_consumer_with_retry():
    """Start the event consumer with retry logic for Redis connection"""
    global event_consumer
    
    # Temporarily disabled to fix import issues
    logger.info("Event consumer temporarily disabled - import issues being resolved")
    return
    
    # max_retries = 5
    # retry_delay = 2
    # 
    # for attempt in range(max_retries):
    #     try:
    #         logger.info(f"Attempting to connect to Redis (attempt {attempt + 1}/{max_retries})")
    #         event_consumer = EventConsumer(redis_url=settings.REDIS_URL)
    #         await start_event_consumer()
    #         logger.info("Successfully connected to Redis and started event consumer")
    #         break
    #         except Exception as e:
    #         logger.warning(f"Failed to connect to Redis (attempt {attempt + 1}/{max_retries}): {str(e)}")
    #         if attempt < max_retries - 1:
    #         await asyncio.sleep(retry_delay)
    #         retry_delay *= 2  # Exponential backoff
    #         else:
    #         logger.error("Failed to connect to Redis after all retries. Event consumer will not be available.")
    #         return

async def start_event_consumer():
    """Start the event consumer to listen for events"""
    global event_consumer
    
    # Temporarily disabled to fix import issues
    logger.info("Event consumer temporarily disabled - import issues being resolved")
    return
    
    # if event_consumer is None:
    #     logger.error("Event consumer not initialized")
    #     return
    #     
    # def handle_document_event(event: BaseEvent):
    #     """Handle document-related events"""
    #     try:
    #         if event.event_type == EventType.DOCUMENT_UPLOADED:
    #         # Create notification for document uploaded
    #         create_notification_from_event(event, "Document Uploaded", f"Document {event.filename} uploaded successfully")
    #         
    #         elif event.event_type == EventType.DOCUMENT_PROCESSING:
    #         # Create notification for document processing
    #         create_notification_from_event(event, "Document Processing", f"Processing document {event.document_id}")
    #         
    #         elif event.event_type == EventType.DOCUMENT_PROCESSED:
    #         # Create notification for document processed
    #         create_notification_from_event(event, "Document Processed", f"Document processed successfully in {event.processing_time:.2f}s")
    #         
    #         elif event.event_type == EventType.DOCUMENT_FAILED:
    #         # Create notification for document failed
    #         create_notification_from_event(event, "Document Failed", f"Document processing failed: {event.error_message}")
    #         
    #         except Exception as e:
    #         logger.error(f"Error handling document event: {str(e)}")
    #     
    # def handle_indexing_event(event: BaseEvent):
    #     """Handle indexing-related events"""
    #     try:
    #         if event.event_type == EventType.INDEXING_STARTED:
    #         # Create notification for document uploaded
    #         create_notification_from_event(event, "Document Uploaded", f"Document {event.filename} uploaded successfully")
    #         
    #         elif event.event_type == EventType.INDEXING_PROCESSING:
    #             # Create notification for indexing progress
    #             create_notification_from_event(event, "Indexing Progress", f"Indexing progress: {event.progress}%")
    #             
    #         elif event.event_type == EventType.INDEXING_COMPLETED:
    #             # Create notification for indexing completed
    #             create_notification_from_event(event, "Indexing Completed", f"Document indexed successfully with {event.vectors_count} vectors")
    #             
    #         elif event.event_type == EventType.INDEXING_FAILED:
    #             # Create notification for indexing failed
    #             create_notification_from_event(event, "Indexing Failed", f"Indexing failed: {event.error_message}")
    #             
    #     except Exception as e:
    #         logger.error(f"Error handling indexing event: {str(e)}")
    # 
    # def handle_task_status_event(event: BaseEvent):
    #     """Handle task status events"""
    #     async def async_handler():
    #         try:
    #             # Create task status record
    #             db = next(get_db())
    #             try:
    #                 task_status = TaskStatus(
    #                     task_id=event.task_id,
    #                     user_id=event.user_id,
    #                     task_type=event.task_type,
    #                     status=event.status,
    #                     progress=event.progress,
    #                     message=event.message,
    #                     meta_data=event.metadata
    #                 )
    #                 db.add(task_status)
    #                 db.commit()
    #                 
    #                 # Send WebSocket notification
    #                 await websocket_manager.send_notification(
    #                     event.user_id,
    #                     {
    #                         "type": "task_status_update",
    #                         "task_id": event.task_id,
    #                         "task_type": event.task_type,
    #                         "status": event.status,
    #                         "progress": event.progress,
    #                         "message": event.message,
    #                         "timestamp": datetime.utcnow().isoformat()
    #                 }
    #                 )
    #                 
    #         finally:
    #                 db.close()
    #                 
    #         except Exception as e:
    #             logger.error(f"Error handling task status event: {str(e)}")
    #     
    #     # Run the async handler
    #     asyncio.create_task(async_handler())
    # 
    # def handle_user_notification_event(event: BaseEvent):
    #     """Handle user notification events"""
    #     async def async_handler():
    #         try:
    #             # Send WebSocket notification
    #             await websocket_manager.send_notification(
    #                 event.user_id,
    #                 {
    #                     "type": "notification",
    #                     "title": event.title,
    #                     "message": event.message,
    #                     "notification_type": event.notification_type,
    #                     "timestamp": datetime.utcnow().isoformat(),
    #                     "metadata": event.metadata
    #                 }
    #             )
    #         except Exception as e:
    #             logger.error(f"Error handling user notification event: {str(e)}")
    #     
    #     # Run the async handler
    #     asyncio.create_task(async_handler())
    # 
    # # Subscribe to events
    # try:
    #     event_consumer.subscribe_to_document_events(handle_document_event)
    #     event_consumer.subscribe_to_indexing_events(handle_indexing_event)
    #     event_consumer.subscribe_to_event(EventType.TASK_STATUS_UPDATE, handle_task_status_event)
    #     event_consumer.subscribe_to_event(EventType.USER_NOTIFICATION, handle_user_notification_event)
    #     
    #     # Start the event consumer
    #     event_consumer.start()
    #     logger.info("Event consumer started successfully")
    #     
    # except Exception as e:
    #     logger.error(f"Failed to start event consumer: {str(e)}")
    #     raise

# Temporarily commented out to fix import issues
# def create_notification_from_event(event: BaseEvent, title: str, message: str):
#     """Create a notification from an event"""
#     async def async_handler():
#         db = next(get_db())
#         try:
#             notification = Notification(
#                 user_id=event.user_id,
#                 title=title,
#                 message=message,
#                 notification_type=event.event_type.value,
#                 metadata=event.metadata
#                 )
#             db.add(notification)
#             db.commit()
#             
#             # Send WebSocket notification
#             await websocket_manager.send_notification(
#                 event.user_id,
#                 {
#                     "type": "notification",
#                     "title": title,
#                     "message": message,
#                     "notification_type": event.event_type.value,
#                     "timestamp": datetime.utcnow().isoformat()
#                 }
#             )
#             
#         finally:
#             db.close()
#     
#     # Run the async handler
#     asyncio.create_task(async_handler())

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "notification-service"}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time notifications"""
    await websocket_manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive - wait for any message or ping
            try:
                data = await websocket.receive_text()
                # Handle ping messages
                if data == "ping":
                    await websocket.send_text("pong")
            except Exception as e:
                print(f"WebSocket error for user {user_id}: {e}")
                break
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user {user_id}")
    finally:
        websocket_manager.disconnect(websocket)

@app.post("/notifications", response_model=NotificationResponse)
async def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db)
):
    """Create a new notification"""
    db_notification = Notification(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    # Send WebSocket notification
    await websocket_manager.send_notification(
        notification.user_id,
        {
            "type": "notification",
            "title": notification.title,
            "message": notification.message,
            "notification_type": notification.notification_type,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    return db_notification

@app.get("/notifications/{user_id}", response_model=List[NotificationResponse])
async def get_user_notifications(
    user_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get notifications for a user"""
    notifications = db.query(Notification).filter(
        Notification.user_id == user_id
    ).order_by(Notification.created_at.desc()).limit(limit).all()
    
    return notifications

@app.post("/task-status", response_model=TaskStatusResponse)
async def create_task_status(
    task_status: TaskStatusCreate,
    db: Session = Depends(get_db)
):
    """Create a new task status"""
    db_task_status = TaskStatus(**task_status.dict())
    db.add(db_task_status)
    db.commit()
    db.refresh(db_task_status)
    
    # Send WebSocket notification
    await websocket_manager.send_notification(
        task_status.user_id,
        {
            "type": "task_status_update",
            "task_id": task_status.task_id,
            "task_type": task_status.task_type,
            "status": task_status.status,
            "progress": task_status.progress,
            "message": task_status.message,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    return db_task_status

@app.put("/task-status/{task_id}", response_model=TaskStatusResponse)
async def update_task_status(
    task_id: str,
    task_status_update: dict,
    db: Session = Depends(get_db)
):
    """Update a task status"""
    task_status = db.query(TaskStatus).filter(TaskStatus.task_id == task_id).first()
    if not task_status:
        raise HTTPException(status_code=404, detail="Task status not found")
    
    # Update fields
    for field, value in task_status_update.items():
        if hasattr(task_status, field):
            setattr(task_status, field, value)
    
    task_status.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task_status)
    
    # Send WebSocket notification
    await websocket_manager.send_notification(
        task_status.user_id,
        {
            "type": "task_status_update",
            "task_id": task_status.task_id,
            "task_type": task_status.task_type,
            "status": task_status.status,
            "progress": task_status.progress,
            "message": task_status.message,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    return task_status

@app.get("/task-status/{user_id}", response_model=List[TaskStatusResponse])
async def get_user_task_statuses(
    user_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get task statuses for a user"""
    task_statuses = db.query(TaskStatus).filter(
        TaskStatus.user_id == user_id
    ).order_by(TaskStatus.created_at.desc()).limit(limit).all()
    
    return task_statuses

@app.post("/quiz-sessions/notify")
async def notify_quiz_session_status(
    user_id: str,
    session_id: str,
    job_id: str,
    status: str,
    progress: int = 0,
    message: str = None,
    quiz_data: dict = None
):
    """Notify a user about quiz session status updates"""
    try:
        logger.info(f"Quiz session notification: user_id={user_id}, session_id={session_id}, status={status}, progress={progress}")
        
        # Send real-time notification via WebSocket
        await websocket_manager.broadcast_quiz_session_status(
            user_id=user_id,
            session_id=session_id,
            job_id=job_id,
            status=status,
            progress=progress,
            message=message,
            quiz_data=quiz_data
        )
        
        return {"message": "Quiz session notification sent successfully"}
    except Exception as e:
        logger.error(f"Error sending quiz session notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 