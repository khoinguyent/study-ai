"""
Dead Letter Queue Management API
Provides REST endpoints for monitoring and managing DLQ messages
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import os
import sys

# Add paths for imports
sys.path.append('/app')
sys.path.append('/app/shared')

from shared.dlq_monitor import DLQMonitor
from shared.celery_app import celery_app

# Initialize FastAPI app
app = FastAPI(
    title="Study AI DLQ Management API",
    description="API for managing Dead Letter Queue messages",
    version="1.0.0"
)

# Initialize DLQ monitor
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
dlq_monitor = DLQMonitor(redis_url, celery_app)

@app.get("/health")
async def get_health():
    """Get DLQ health status"""
    try:
        health = dlq_monitor.get_dlq_health()
        return {
            "status": "healthy",
            "dlq_health": health
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/stats")
async def get_dlq_stats():
    """Get detailed DLQ statistics"""
    try:
        stats = dlq_monitor.get_dlq_stats()
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/queues/{queue_name}/messages")
async def list_dlq_messages(queue_name: str, limit: int = 10):
    """List messages in a specific DLQ"""
    try:
        if queue_name not in dlq_monitor.dlq_queues:
            raise HTTPException(status_code=404, detail=f"Queue {queue_name} not found")
        
        messages = dlq_monitor.list_dlq_messages(queue_name, limit)
        return {
            "status": "success",
            "queue": queue_name,
            "message_count": len(messages),
            "messages": messages
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/queues/{queue_name}/retry/{message_index}")
async def retry_dlq_message(queue_name: str, message_index: int):
    """Retry a specific message from DLQ"""
    try:
        if queue_name not in dlq_monitor.dlq_queues:
            raise HTTPException(status_code=404, detail=f"Queue {queue_name} not found")
        
        success = dlq_monitor.retry_dlq_message(queue_name, message_index)
        
        if success:
            return {
                "status": "success",
                "message": f"Message {message_index} from {queue_name} retried successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to retry message")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/queues/{queue_name}/discard/{message_index}")
async def discard_dlq_message(queue_name: str, message_index: int):
    """Discard a specific message from DLQ"""
    try:
        if queue_name not in dlq_monitor.dlq_queues:
            raise HTTPException(status_code=404, detail=f"Queue {queue_name} not found")
        
        success = dlq_monitor.discard_dlq_message(queue_name, message_index)
        
        if success:
            return {
                "status": "success",
                "message": f"Message {message_index} from {queue_name} discarded successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to discard message")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/queues/{queue_name}/clear")
async def clear_dlq(queue_name: str):
    """Clear all messages from a DLQ"""
    try:
        if queue_name not in dlq_monitor.dlq_queues:
            raise HTTPException(status_code=404, detail=f"Queue {queue_name} not found")
        
        success = dlq_monitor.clear_dlq(queue_name)
        
        if success:
            return {
                "status": "success",
                "message": f"Queue {queue_name} cleared successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear queue")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/queues")
async def list_queues():
    """List all DLQ queues"""
    try:
        queues = list(dlq_monitor.dlq_queues.keys())
        return {
            "status": "success",
            "queues": queues,
            "queue_mappings": dlq_monitor.dlq_queues
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/summary")
async def get_summary():
    """Get a summary of all DLQ status"""
    try:
        health = dlq_monitor.get_dlq_health()
        stats = dlq_monitor.get_dlq_stats()
        
        summary = {
            "overall_status": health["status"],
            "total_failed_tasks": health["total_failed_tasks"],
            "queues": {}
        }
        
        for queue_name in dlq_monitor.dlq_queues.keys():
            queue_health = health["queues"].get(queue_name, {})
            queue_stats = stats.get(queue_name, {})
            
            summary["queues"][queue_name] = {
                "status": queue_health.get("status", "unknown"),
                "failed_tasks": queue_health.get("failed_tasks", 0),
                "original_queue": queue_stats.get("original_queue", "unknown"),
                "threshold_exceeded": queue_health.get("threshold_exceeded", False)
            }
        
        return {
            "status": "success",
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
