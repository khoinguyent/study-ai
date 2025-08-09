"""
Quiz Service Tasks for Study AI Platform
Handles quiz generation tasks using Celery and event-driven architecture
"""

import time
from celery import current_task
from app.database import get_db
from app.models import Quiz
from shared.celery_app import celery_app, EventDrivenTask, quiz_task
from shared.event_publisher import EventPublisher
from shared.events import EventType, create_event
import logging

logger = logging.getLogger(__name__)

# Initialize services
event_publisher = EventPublisher()

@quiz_task
def generate_quiz(document_id: str, user_id: str, subject_id: str = None, category_id: str = None):
    """
    Generate quiz questions for a document
    """
    task_id = current_task.request.id
    
    try:
        # Publish quiz generation started event
        event_publisher.publish_quiz_generation_started(
            user_id=user_id,
            document_id=document_id,
            subject_id=subject_id,
            category_id=category_id
        )
        
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'message': 'Starting quiz generation...'}
        )
        
        # Simulate quiz generation process
        start_time = time.time()
        total_questions = 10
        generated_questions = 0
        
        # Process questions in batches
        for batch in range(0, total_questions, 2):
            # Simulate question generation
            time.sleep(1)
            generated_questions += 2
            progress = min((generated_questions / total_questions) * 100, 100)
            
            # Update task status
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'progress': int(progress),
                    'message': f'Generating questions {generated_questions}/{total_questions}...'
                }
            )
            
            # Publish quiz generation progress event
            event_publisher.publish_quiz_generation_progress(
                user_id=user_id,
                document_id=document_id,
                progress=int(progress),
                generated_questions=generated_questions,
                total_questions=total_questions
            )
        
        generation_time = time.time() - start_time
        
        logger.info(f"Quiz for document {document_id} generated successfully in {generation_time:.2f}s")
        
        # Publish quiz generation completed event
        event_publisher.publish_quiz_generation_completed(
            user_id=user_id,
            document_id=document_id,
            questions_count=total_questions,
            generation_time=generation_time
        )
        
        # Publish task completed event
        event_publisher.publish_task_status_update(
            user_id=user_id,
            task_id=task_id,
            task_type="quiz_generation",
            status="completed",
            progress=100,
            message=f"Quiz generated successfully with {total_questions} questions"
        )
        
        # Publish quiz ready notification
        event_publisher.publish_user_notification(
            user_id=user_id,
            notification_type="quiz_ready",
            title="Quiz Ready",
            message=f"Quiz for document {document_id} is now ready",
            priority="normal"
        )
        
        return {
            'status': 'success',
            'document_id': document_id,
            'generation_time': generation_time,
            'questions_count': total_questions
        }
        
    except Exception as e:
        logger.error(f"Failed to generate quiz for document {document_id}: {str(e)}")
        
        # Publish failure events
        event_publisher.publish_quiz_generation_failed(
            user_id=user_id,
            document_id=document_id,
            error_message=str(e)
        )
        
        event_publisher.publish_task_status_update(
            user_id=user_id,
            task_id=task_id,
            task_type="quiz_generation",
            status="failed",
            progress=0,
            message=f"Quiz generation failed: {str(e)}"
        )
        
        raise

@quiz_task
def regenerate_quiz(quiz_id: str, user_id: str):
    """
    Regenerate an existing quiz
    """
    return generate_quiz.delay(quiz_id, user_id)
