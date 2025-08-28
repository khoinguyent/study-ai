"""
Notification Service for Study AI Platform
Handles real-time notifications and event processing
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import uuid
import httpx
from sqlalchemy import func
from fastapi.responses import StreamingResponse

from .database import get_db, create_tables
from .models import Notification, TaskStatus
from .schemas import NotificationCreate, NotificationResponse, TaskStatusCreate, TaskStatusResponse
from .websocket_manager import WebSocketManager
from .config import settings
# Import event consumer and events
from shared.event_consumer import EventConsumer
from shared.events import EventType, BaseEvent
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

async def verify_auth_token(authorization: str = Header(alias="Authorization")):
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

async def start_event_consumer_with_retry():
    """Start the event consumer with retry logic for Redis connection"""
    global event_consumer
    
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to Redis (attempt {attempt + 1}/{max_retries})")
            event_consumer = EventConsumer(redis_url=settings.REDIS_URL)
            await start_event_consumer()
            logger.info("Successfully connected to Redis and started event consumer")
            break
        except Exception as e:
            logger.warning(f"Failed to connect to Redis (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error("Failed to connect to Redis after all retries. Event consumer will not be available.")
                return

async def start_event_consumer():
    """Start the event consumer to listen for events"""
    global event_consumer
    
    if event_consumer is None:
        logger.error("Event consumer not initialized")
        return
    
    def handle_document_event(event: BaseEvent):
        """Handle document-related events"""
        try:
            if event.event_type == EventType.DOCUMENT_UPLOADED:
                # Create notification for document uploaded
                create_notification_from_event(event, "Document Uploaded", f"Document uploaded successfully")
                
            elif event.event_type == EventType.DOCUMENT_PROCESSING:
                # Create notification for document processing
                create_notification_from_event(event, "Document Processing", f"Processing document {event.document_id}")
                
            elif event.event_type == EventType.DOCUMENT_PROCESSED:
                # Create notification for document processed
                create_notification_from_event(event, "Document Processed", f"Document processed successfully")
                
            elif event.event_type == EventType.DOCUMENT_FAILED:
                # Create notification for document failed
                create_notification_from_event(event, "Document Failed", f"Document processing failed: {event.metadata.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error handling document event: {str(e)}")
    
    def handle_indexing_event(event: BaseEvent):
        """Handle indexing-related events"""
        try:
            if event.event_type == EventType.INDEXING_STARTED:
                # Create notification for indexing started
                create_notification_from_event(event, "Indexing Started", f"Indexing started for document {event.document_id}")
                
            elif event.event_type == EventType.INDEXING_PROGRESS:
                # Create notification for indexing progress
                create_notification_from_event(event, "Indexing Progress", f"Indexing progress: {event.metadata.get('progress', 0)}%")
                
            elif event.event_type == EventType.INDEXING_COMPLETED:
                # Create notification for indexing completed
                create_notification_from_event(event, "Indexing Completed", f"Document indexed successfully")
                
            elif event.event_type == EventType.INDEXING_FAILED:
                # Create notification for indexing failed
                create_notification_from_event(event, "Indexing Failed", f"Indexing failed: {event.metadata.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error handling indexing event: {str(e)}")
    
    def handle_task_status_event(event: BaseEvent):
        """Handle task status events"""
        async def async_handler():
            try:
                # Create task status record
                db = next(get_db())
                try:
                    task_status = TaskStatus(
                        task_id=event.metadata.get('task_id', ''),
                        user_id=event.user_id,
                        task_type=event.metadata.get('task_type', ''),
                        status=event.metadata.get('status', ''),
                        progress=event.metadata.get('progress', 0),
                        message=event.metadata.get('message', '')
                    )
                    db.add(task_status)
                    db.commit()
                    
                    # Send WebSocket notification
                    await websocket_manager.send_notification(
                        event.user_id,
                        {
                            "type": "task_status_update",
                            "task_id": event.metadata.get('task_id', ''),
                            "task_type": event.metadata.get('task_type', ''),
                            "status": event.metadata.get('status', ''),
                            "progress": event.metadata.get('progress', 0),
                            "message": event.metadata.get('message', ''),
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                    
                finally:
                    db.close()
                    
            except Exception as e:
                logger.error(f"Error handling task status event: {str(e)}")
        
        # Run the async handler
        asyncio.create_task(async_handler())
    
    def handle_user_notification_event(event: BaseEvent):
        """Handle user notification events"""
        async def async_handler():
            try:
                # Send WebSocket notification
                await websocket_manager.send_notification(
                    event.user_id,
                    {
                        "type": "notification",
                        "title": event.metadata.get('title', ''),
                        "message": event.metadata.get('message', ''),
                        "notification_type": event.metadata.get('notification_type', ''),
                        "timestamp": datetime.utcnow().isoformat(),
                        "metadata": event.metadata
                    }
                )
            except Exception as e:
                logger.error(f"Error handling user notification event: {str(e)}")
        
        # Run the async handler
        asyncio.create_task(async_handler())
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
    # Subscribe to events
    try:
        event_consumer.subscribe_to_document_events(handle_document_event)
        event_consumer.subscribe_to_indexing_events(handle_indexing_event)
        event_consumer.subscribe_to_event(EventType.TASK_STATUS_UPDATE, handle_task_status_event)
        event_consumer.subscribe_to_event(EventType.USER_NOTIFICATION, handle_user_notification_event)
        
        # Start the event consumer
        event_consumer.start()
        logger.info("Event consumer started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start event consumer: {str(e)}")
        raise

def create_notification_from_event(event: BaseEvent, title: str, message: str):
    """Create a notification from an event"""
    async def async_handler():
        db = next(get_db())
        try:
            notification = Notification(
                user_id=event.user_id,
                title=title,
                message=message,
                notification_type=event.event_type.value,
                metadata=event.metadata
            )
            db.add(notification)
            db.commit()
            
            # Send WebSocket notification
            asyncio.create_task(websocket_manager.send_notification(
                event.user_id,
                {
                    "type": "notification",
                    "title": title,
                    "message": message,
                    "notification_type": event.event_type.value,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))
            
        finally:
            db.close()
    
    # Run the async handler
    asyncio.create_task(async_handler())

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

@app.get("/events")
async def events_stream(userId: str = Query(...)):
    """SSE stream for real-time events and notifications"""
    async def event_generator():
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'message': 'Event stream connected'})}\n\n"
            
            # For now, send a heartbeat every 30 seconds to keep connection alive
            # In a full implementation, this would stream real events from Redis/event system
            import asyncio
            while True:
                await asyncio.sleep(30)
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': str(datetime.utcnow())})}\n\n"
                
        except Exception as e:
            logger.error(f"Event stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.get("/uploads/events")
async def upload_events_stream(userId: str = Query(...)):
    """SSE stream specifically for upload events"""
    async def event_generator():
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'message': 'Upload events stream connected'})}\n\n"
            
            # For now, send a heartbeat every 30 seconds to keep connection alive
            # In a full implementation, this would stream real upload events from Redis/event system
            import asyncio
            while True:
                await asyncio.sleep(30)
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': str(datetime.utcnow())})}\n\n"
                
        except Exception as e:
            logger.error(f"Upload events stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

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

@app.delete("/notifications/clear-all")
async def clear_all_notifications(
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Clear all notifications for a user"""
    try:
        # Delete all notifications for the user
        deleted_count = db.query(Notification).filter(
            Notification.user_id == user_id
        ).delete()
        
        # Delete all task statuses for the user
        task_deleted_count = db.query(TaskStatus).filter(
            TaskStatus.user_id == user_id
        ).delete()
        
        db.commit()
        
        return {
            "message": "All notifications cleared successfully",
            "notifications_deleted": deleted_count,
            "task_statuses_deleted": task_deleted_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear notifications: {str(e)}"
        )

@app.delete("/notifications/clear-pending")
async def clear_pending_notifications(
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Clear all pending/processing task statuses for a user"""
    try:
        # Delete all pending/processing task statuses
        deleted_count = db.query(TaskStatus).filter(
            TaskStatus.user_id == user_id,
            TaskStatus.status.in_(["pending", "processing"])
        ).delete()
        
        db.commit()
        
        return {
            "message": "Pending notifications cleared successfully",
            "pending_tasks_deleted": deleted_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear pending notifications: {str(e)}"
        )

@app.delete("/notifications/clear-by-type/{notification_type}")
async def clear_notifications_by_type(
    notification_type: str,
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Clear notifications by type for a user"""
    try:
        # Delete notifications by type
        deleted_count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.notification_type == notification_type
        ).delete()
        
        db.commit()
        
        return {
            "message": f"Notifications of type '{notification_type}' cleared successfully",
            "notifications_deleted": deleted_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear notifications by type: {str(e)}"
        )

@app.get("/notifications/queue-status")
async def get_notification_queue_status(
    user_id: str = Depends(verify_auth_token),
    db: Session = Depends(get_db)
):
    """Get notification queue status for a user"""
    try:
        # Count notifications by type
        notification_counts = db.query(
            Notification.notification_type,
            func.count(Notification.id)
        ).filter(
            Notification.user_id == user_id
        ).group_by(Notification.notification_type).all()
        
        # Count task statuses by status
        task_counts = db.query(
            TaskStatus.status,
            func.count(TaskStatus.id)
        ).filter(
            TaskStatus.user_id == user_id
        ).group_by(TaskStatus.status).all()
        
        return {
            "notification_counts": dict(notification_counts),
            "task_status_counts": dict(task_counts),
            "total_notifications": sum(count for _, count in notification_counts),
            "total_tasks": sum(count for _, count in task_counts)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue status: {str(e)}"
        ) 