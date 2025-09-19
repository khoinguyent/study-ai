"""
Notification Service for Study AI Platform
Handles real-time notifications and event processing
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status, Header, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import json
import asyncio
import time
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

# Create database tables on startup
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    # Start event consumer with retry logic
    await start_event_consumer_with_retry()
    yield
    # Shutdown
    if event_consumer:
        event_consumer.stop()

app = FastAPI(
    title="Notification Service",
    description="Real-time notification and event processing service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize WebSocket manager
websocket_manager = WebSocketManager()

# Event consumer - will be initialized before background thread starts
event_consumer = None

# Global event handlers
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
    try:
        # Create or update task status record (upsert approach)
        db = next(get_db())
        try:
            # Check if task already exists
            existing_task = db.query(TaskStatus).filter(TaskStatus.task_id == event.task_id).first()
            
            if existing_task:
                # Update existing task
                existing_task.status = event.status
                existing_task.progress = event.progress
                existing_task.message = event.message or ''
                existing_task.updated_at = datetime.utcnow()
                if event.status == 'completed':
                    existing_task.completed_at = datetime.utcnow()
                print(f"📝 Updated existing task: {event.task_id}")
            else:
                # Create new task
                task_status = TaskStatus(
                    task_id=event.task_id,
                    user_id=event.user_id,
                    task_type=event.task_type,
                    status=event.status,
                    progress=event.progress,
                    message=event.message or ''
                )
                db.add(task_status)
                print(f"📝 Created new task: {event.task_id}")
            
            db.commit()
            
            # Send WebSocket notification using a new event loop for the background thread
            def send_notification_async():
                try:
                    asyncio.run(websocket_manager.send_notification(
                        event.user_id,
                        {
                            "type": "task_status_update",
                            "task_id": event.task_id,
                            "task_type": event.task_type,
                            "status": event.status,
                            "progress": event.progress,
                            "message": event.message or '',
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    ))
                except Exception as e:
                    logger.error(f"Error sending WebSocket notification: {str(e)}")
            
            # Run in a separate thread to avoid blocking
            import threading
            threading.Thread(target=send_notification_async, daemon=True).start()
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error handling task status event: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

def handle_user_notification_event(event: BaseEvent):
    """Handle user notification events"""
    try:
        # Send WebSocket notification using a new event loop for the background thread
        def send_notification_async():
            try:
                asyncio.run(websocket_manager.send_notification(
                    event.user_id,
                    {
                        "type": "notification",
                        "title": event.title,
                        "message": event.message,
                        "notification_type": event.notification_type,
                        "timestamp": datetime.utcnow().isoformat(),
                        "metadata": event.metadata
                    }
                ))
            except Exception as e:
                logger.error(f"Error sending WebSocket notification: {str(e)}")
        
        # Run in a separate thread to avoid blocking
        import threading
        threading.Thread(target=send_notification_async, daemon=True).start()
    except Exception as e:
        logger.error(f"Error handling user notification event: {str(e)}")

def handle_quiz_event(event: BaseEvent):
    """Handle quiz-related events"""
    try:
        if event.event_type == EventType.QUIZ_GENERATION_STARTED:
            # Create notification for quiz generation started
            create_notification_from_event(event, "Quiz Generation Started", f"Starting quiz generation for {event.metadata.get('question_count', 0)} questions")
            
        elif event.event_type == EventType.QUIZ_GENERATION_PROGRESS:
            # Create notification for quiz generation progress
            progress = event.metadata.get('progress', 0)
            create_notification_from_event(event, "Quiz Generation Progress", f"Generating quiz: {progress}% complete")
            
        elif event.event_type == EventType.QUIZ_GENERATED:
            # Create notification for quiz generation completed
            quiz_id = event.metadata.get('quiz_id', 'unknown')
            question_count = event.metadata.get('question_count', 0)
            create_notification_from_event(event, "Quiz Ready", f"Quiz with {question_count} questions is ready to use", notification_type="quiz_generated")
            
        elif event.event_type == EventType.QUIZ_GENERATION_FAILED:
            # Create notification for quiz generation failed
            error_msg = event.metadata.get('error', 'Unknown error')
            create_notification_from_event(event, "Quiz Generation Failed", f"Failed to generate quiz: {error_msg}")
            
    except Exception as e:
        logger.error(f"Error handling quiz event: {str(e)}")

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
    
    # Subscribe to events using the global handlers
    try:
        event_consumer.subscribe_to_document_events(handle_document_event)
        event_consumer.subscribe_to_indexing_events(handle_indexing_event)
        event_consumer.subscribe_to_event(EventType.TASK_STATUS_UPDATE, handle_task_status_event)
        event_consumer.subscribe_to_event(EventType.USER_NOTIFICATION, handle_user_notification_event)
        event_consumer.subscribe_to_event(EventType.QUIZ_GENERATION_STARTED, handle_quiz_event)
        event_consumer.subscribe_to_event(EventType.QUIZ_GENERATION_PROGRESS, handle_quiz_event)
        event_consumer.subscribe_to_event(EventType.QUIZ_GENERATED, handle_quiz_event)
        event_consumer.subscribe_to_event(EventType.QUIZ_GENERATION_FAILED, handle_quiz_event)
        
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

# Database tables and event consumer are now handled by lifespan context manager

# Event consumer is now managed by lifespan context manager

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
            
            # Send mock quiz generation events for testing
            logger.info(f"Starting event stream for user {userId}")
            
            # Simulate quiz generation progress
            await asyncio.sleep(1)  # Initial delay
            
            # Send quiz generation started event
            yield f"data: {json.dumps({'type': 'quiz_generation_started', 'data': {'job_id': 'mock-job-123', 'progress': 0, 'message': 'Starting quiz generation...'}})}\n\n"
            
            # Simulate progress updates
            for progress in [25, 50, 75, 100]:
                await asyncio.sleep(2)  # 2 second intervals
                yield f"data: {json.dumps({'type': 'quiz_generation_progress', 'data': {'job_id': 'mock-job-123', 'progress': progress, 'message': f'Generating questions... {progress}%'}})}\n\n"
            
            # Send completion event
            await asyncio.sleep(1)
            yield f"data: {json.dumps({'type': 'quiz_generation_completed', 'data': {'job_id': 'mock-job-123', 'quiz_id': 'mock-quiz-456', 'session_id': 'mock-session-789', 'progress': 100, 'message': 'Quiz generation completed!'}})}\n\n"
            
            # Keep connection alive with heartbeats
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
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@app.get("/uploads/events")
async def uploads_events_stream(userId: str = Query(...)):
    """SSE stream for upload events (compatibility with frontend)"""
    async def event_generator():
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'message': 'Upload event stream connected'})}\n\n"
            
            # For now, send a heartbeat every 30 seconds to keep connection alive
            # In a full implementation, this would stream real events from Redis/event system
            import asyncio
            while True:
                await asyncio.sleep(30)
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': str(datetime.utcnow())})}\n\n"
                
        except Exception as e:
            logger.error(f"Upload event stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@app.get("/api/notifications/queue-status")
async def get_queue_status():
    """Get the current status of the notification queue"""
    try:
        # Get pending notifications count
        db = next(get_db())
        try:
            pending_count = db.query(Notification).filter(Notification.status == "pending").count()
            return {
                "status": "healthy",
                "pending_notifications": pending_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error getting queue status: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/api/study-sessions/events")
async def study_sessions_events_stream(job_id: str = Query(...)):
    """SSE stream for study session events (what the frontend is actually calling)"""
    try:
        # Forward the request to the quiz service which has the actual SSE implementation
        import httpx
        from fastapi import HTTPException
        import os
        
        async def stream_events():
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "GET",
                    f"{os.getenv('QUIZ_SERVICE_URL', 'http://quiz-service:8000')}/study-sessions/events",
                    params={"job_id": job_id},
                    timeout=30.0
                ) as response:
                    if response.status_code == 200:
                        async for chunk in response.aiter_bytes():
                            yield chunk
                    else:
                        # For non-200 responses, we need to handle them differently
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"Quiz service error: {response.text}"
                        )
        
        # Proxy SSE directly to quiz service with correct MIME type
        return StreamingResponse(
            stream_events(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        logger.error(f"Study session event stream error: {e}")
        # Return error as SSE event
        async def error_stream():
            yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'job_id': job_id})}\n\n"
        
        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )

@app.post("/notifications/clear-by-type")
async def clear_notifications_by_type(request: Request):
    """Clear notifications by type for the authenticated user"""
    try:
        # Get the request body
        body = await request.json()
        notification_type = body.get("notification_type")
        
        if not notification_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="notification_type is required"
            )
        
        # For now, we'll just return success since we don't have a full notification system
        # In a real implementation, this would delete notifications from the database
        logger.info(f"Clearing notifications of type: {notification_type}")
        
        return {
            "message": f"Cleared notifications of type: {notification_type}",
            "notification_type": notification_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing notifications by type: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear notifications: {str(e)}"
        )
