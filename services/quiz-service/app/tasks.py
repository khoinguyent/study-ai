"""
Quiz Service Tasks for Study AI Platform
Handles quiz generation tasks using Celery and event-driven architecture
"""

import time
from app.database import get_db
from app.models import Quiz
from app.celery_app import celery_app, quiz_task
# Lightweight local event publisher fallback
class _LocalEventPublisher:
    def publish_quiz_generation_started(self, **kwargs):
        logger.info(f"[events] quiz_generation_started {kwargs}")
    def publish_quiz_generation_progress(self, **kwargs):
        logger.info(f"[events] quiz_generation_progress {kwargs}")
    def publish_quiz_generation_completed(self, **kwargs):
        logger.info(f"[events] quiz_generation_completed {kwargs}")
    def publish_quiz_generation_failed(self, **kwargs):
        logger.info(f"[events] quiz_generation_failed {kwargs}")
    def publish_task_status_update(self, **kwargs):
        logger.info(f"[events] task_status_update {kwargs}")
    def publish_user_notification(self, **kwargs):
        logger.info(f"[events] user_notification {kwargs}")
import logging

logger = logging.getLogger(__name__)

# Initialize services
event_publisher = _LocalEventPublisher()

@quiz_task(bind=True)
def generate_quiz(self, document_id: str, user_id: str, subject_id: str = None, category_id: str = None):
    """
    Generate quiz questions for a document
    """
    task_id = self.request.id
    
    try:
        logger.info(f"Starting quiz generation for document {document_id}, user {user_id}")
        
        # Publish quiz generation started event
        event_publisher.publish_quiz_generation_started(
            user_id=user_id,
            document_id=document_id,
            subject_id=subject_id,
            category_id=category_id
        )
        
        # Update task status
        self.update_state(
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
            self.update_state(
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

@quiz_task(bind=True)
def regenerate_quiz(self, quiz_id: str, user_id: str):
    """
    Regenerate an existing quiz
    """
    return generate_quiz.delay(quiz_id, user_id)

@quiz_task(bind=True)
def generate_quiz_background_task(self, quiz_id: str, topic: str, difficulty: str, num_questions: int, 
                                 context_chunks: list, source_type: str, source_id: str, user_id: str):
    """
    Background task to generate quiz content using Celery
    """
    task_id = self.request.id
    
    try:
        logger.info(f"Starting background quiz generation for quiz {quiz_id}, user {user_id}")
        
        # Publish quiz generation started event
        event_publisher.publish_quiz_generation_started(
            user_id=user_id,
            document_id=source_id,
            subject_id=source_id if source_type == "subject" else None,
            category_id=source_id if source_type == "category" else None
        )
        
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'message': 'Starting quiz generation...'}
        )
        
        # Get database session
        db = next(get_db())
        
        try:
            # Update quiz status to processing
            quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
            if quiz:
                quiz.status = "processing"
                quiz.questions = {"message": "Quiz generation in progress..."}
                db.commit()
            
            # Import quiz generator here to avoid circular imports
            from .services.quiz_generator import QuizGenerator
            quiz_generator = QuizGenerator()
            
            # Generate quiz using AI (synchronous call in Celery task)
            quiz_content = quiz_generator.generate_quiz_from_context_sync(
                topic=topic,
                difficulty=difficulty,
                num_questions=num_questions,
                context_chunks=context_chunks,
                source_type=source_type,
                source_id=source_id
            )
            
            # Update quiz with generated content
            quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
            if quiz:
                quiz.status = "completed"
                quiz.title = quiz_content.get("title", "Generated Quiz")
                quiz.description = quiz_content.get("description", "")
                quiz.questions = quiz_content.get("questions", [])
                db.commit()
                
                logger.info(f"Quiz generation completed successfully for quiz ID: {quiz_id}")
                
                # Publish quiz generation completed event
                event_publisher.publish_quiz_generation_completed(
                    user_id=user_id,
                    document_id=source_id,
                    questions_count=len(quiz_content.get("questions", [])),
                    generation_time=0  # Could calculate actual time if needed
                )
                
                # Publish task completed event
                event_publisher.publish_task_status_update(
                    user_id=user_id,
                    task_id=task_id,
                    task_type="quiz_generation",
                    status="completed",
                    progress=100,
                    message=f"Quiz generated successfully with {len(quiz_content.get('questions', []))} questions"
                )
                
                # Publish quiz ready notification
                event_publisher.publish_user_notification(
                    user_id=user_id,
                    notification_type="quiz_ready",
                    title="Quiz Ready",
                    message=f"Quiz about {topic} is now ready",
                    priority="normal"
                )
                
        finally:
            db.close()
            
        return {
            'status': 'success',
            'quiz_id': quiz_id,
            'questions_count': len(quiz_content.get("questions", [])),
            'source_type': source_type,
            'source_id': source_id
        }
        
    except Exception as e:
        logger.error(f"Quiz generation failed for quiz ID {quiz_id}: {str(e)}")
        
        # Get database session for error update
        db = next(get_db())
        try:
            # Update quiz with error message
            quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
            if quiz:
                quiz.status = "failed"
                quiz.questions = {
                    "error": str(e),
                    "traceback": str(e)
                }
                db.commit()
        finally:
            db.close()
        
        # Publish failure events
        event_publisher.publish_quiz_generation_failed(
            user_id=user_id,
            document_id=source_id,
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
