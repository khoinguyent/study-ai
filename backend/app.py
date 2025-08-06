from flask import Flask, jsonify, request, current_app
from flask_cors import CORS
from flask_restful import Api
import os
import tempfile
import uuid
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from celery import Celery
from sqlalchemy.orm import Session

# Import our modules
from database import get_db, init_db, check_db_connection
from models import User, Document, DocumentChunk, Quiz, ProcessingTask
from storage_client import storage_client
from document_processor import document_processor
from ai_agents import ai_agents
from config import config

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

# Enable CORS
CORS(app)

# Initialize API
api = Api(app)

# Initialize Celery
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=config.REDIS_URL,
        broker=config.REDIS_URL
    )
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

celery = make_celery(app)

# Initialize database on startup
@app.before_first_request
def setup_database():
    init_db()

# Basic routes
@app.route('/')
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Study AI Backend is running',
        'version': '1.0.0'
    })

@app.route('/api/health')
def api_health():
    db_status = 'connected' if check_db_connection() else 'disconnected'
    return jsonify({
        'status': 'ok',
        'services': {
            'web': 'running',
            'database': db_status,
            'redis': 'connected',
            'celery': 'running'
        }
    })

# User management routes
@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    data = request.get_json()
    if not data or 'email' not in data or 'name' not in data:
        return jsonify({'error': 'Email and name are required'}), 400
    
    db = next(get_db())
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == data['email']).first()
        if existing_user:
            return jsonify({'error': 'User already exists'}), 409
        
        # Create new user
        user = User(
            email=data['email'],
            name=data['name']
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return jsonify({
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name
            }
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get user information"""
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'created_at': user.created_at.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# Document upload and management routes
@app.route('/api/upload', methods=['POST'])
def upload_document():
    """Upload and process documents"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    user_id = request.form.get('user_id')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    # Validate file type
    allowed_extensions = {'pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx'}
    file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if file_extension not in allowed_extensions:
        return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'}), 400
    
    db = next(get_db())
    try:
        # Save file temporarily
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}')
        file.save(temp_file.name)
        
        # Upload to storage
        storage_key, storage_url = storage_client.upload_file(
            temp_file.name, 
            file.filename, 
            user_id
        )
        
        # Create document record
        document = Document(
            user_id=user_id,
            filename=os.path.basename(storage_key),
            original_filename=file.filename,
            file_size=os.path.getsize(temp_file.name),
            file_type=file_extension,
            s3_key=storage_key,
            s3_bucket=storage_client.storage_config['bucket_name'],
            status='uploaded'
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Queue document processing task
        task = process_document.delay(document.id, user_id)
        
        # Update document with task ID
        document.processing_task_id = task.id
        document.status = 'processing'
        db.commit()
        
        # Clean up temp file
        os.unlink(temp_file.name)
        
        return jsonify({
            'message': 'File uploaded successfully',
            'document_id': document.id,
            'filename': file.filename,
            'task_id': task.id,
            'status': 'processing'
        })
        
    except Exception as e:
        db.rollback()
        # Clean up temp file if it exists
        if 'temp_file' in locals():
            os.unlink(temp_file.name)
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/documents/<document_id>', methods=['GET'])
def get_document(document_id):
    """Get document information"""
    db = next(get_db())
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        return jsonify({
            'document': {
                'id': document.id,
                'filename': document.original_filename,
                'file_size': document.file_size,
                'file_type': document.file_type,
                'status': document.status,
                'created_at': document.created_at.isoformat(),
                'chunks_count': len(document.chunks)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/users/<user_id>/documents', methods=['GET'])
def get_user_documents(user_id):
    """Get all documents for a user"""
    db = next(get_db())
    try:
        documents = db.query(Document).filter(Document.user_id == user_id).all()
        
        return jsonify({
            'documents': [{
                'id': doc.id,
                'filename': doc.original_filename,
                'file_size': doc.file_size,
                'file_type': doc.file_type,
                'status': doc.status,
                'created_at': doc.created_at.isoformat(),
                'chunks_count': len(doc.chunks)
            } for doc in documents]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# Quiz generation routes
@app.route('/api/quizzes', methods=['POST'])
def create_quiz():
    """Create a new quiz from selected documents"""
    data = request.get_json()
    if not data or 'document_ids' not in data or 'user_id' not in data:
        return jsonify({'error': 'Document IDs and user ID are required'}), 400
    
    document_ids = data['document_ids']
    user_id = data['user_id']
    num_questions = data.get('num_questions', 10)
    
    db = next(get_db())
    try:
        # Verify documents belong to user
        documents = db.query(Document).filter(
            Document.id.in_(document_ids),
            Document.user_id == user_id,
            Document.status == 'completed'
        ).all()
        
        if len(documents) != len(document_ids):
            return jsonify({'error': 'Some documents not found or not processed'}), 404
        
        # Create quiz record
        quiz = Quiz(
            user_id=user_id,
            title=f"Quiz from {len(document_ids)} document(s)",
            document_ids=document_ids,
            status='generating'
        )
        
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        # Queue quiz generation task
        task = generate_quiz.delay(quiz.id, document_ids, num_questions)
        
        # Update quiz with task ID
        quiz.generation_task_id = task.id
        db.commit()
        
        return jsonify({
            'message': 'Quiz generation started',
            'quiz_id': quiz.id,
            'task_id': task.id,
            'status': 'generating'
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/quizzes/<quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    """Get quiz information"""
    db = next(get_db())
    try:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            return jsonify({'error': 'Quiz not found'}), 404
        
        return jsonify({
            'quiz': {
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description,
                'status': quiz.status,
                'topics': quiz.topics,
                'questions': quiz.questions,
                'total_questions': quiz.total_questions if quiz.questions else 0,
                'created_at': quiz.created_at.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/users/<user_id>/quizzes', methods=['GET'])
def get_user_quizzes(user_id):
    """Get all quizzes for a user"""
    db = next(get_db())
    try:
        quizzes = db.query(Quiz).filter(Quiz.user_id == user_id).all()
        
        return jsonify({
            'quizzes': [{
                'id': quiz.id,
                'title': quiz.title,
                'status': quiz.status,
                'total_questions': len(quiz.questions) if quiz.questions else 0,
                'created_at': quiz.created_at.isoformat()
            } for quiz in quizzes]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

# Task status routes
@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get task status"""
    try:
        task_result = celery.AsyncResult(task_id)
        
        return jsonify({
            'task_id': task_id,
            'status': task_result.status,
            'result': task_result.result if task_result.ready() else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Celery Tasks
@celery.task
def process_document(document_id: str, user_id: str):
    """Background task to process uploaded documents"""
    db = next(get_db())
    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise Exception("Document not found")
        
        # Download file from storage
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{document.file_type}')
        if not storage_client.download_file(document.s3_key, temp_file.name):
            raise Exception("Failed to download file from storage")
        
        # Process document
        processed_chunks = document_processor.process_document(temp_file.name, document.file_type)
        
        # Store chunks in database
        for chunk_data in processed_chunks:
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=chunk_data['chunk_index'],
                content=chunk_data['content'],
                embedding=chunk_data['embedding'],
                metadata=chunk_data['metadata']
            )
            db.add(chunk)
        
        # Update document status
        document.status = 'completed'
        db.commit()
        
        # Clean up temp file
        os.unlink(temp_file.name)
        
        return {
            'status': 'completed',
            'document_id': document_id,
            'chunks_processed': len(processed_chunks)
        }
        
    except Exception as e:
        db.rollback()
        # Update document status to failed
        if 'document' in locals():
            document.status = 'failed'
            db.commit()
        
        # Clean up temp file if it exists
        if 'temp_file' in locals():
            os.unlink(temp_file.name)
        
        return {
            'status': 'failed',
            'error': str(e),
            'document_id': document_id
        }
    finally:
        db.close()

@celery.task
def generate_quiz(quiz_id: str, document_ids: list, num_questions: int = 10):
    """Background task to generate quiz using AI agents"""
    db = next(get_db())
    try:
        # Get quiz
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise Exception("Quiz not found")
        
        # Generate quiz using AI agents
        quiz_data = ai_agents.create_quiz(document_ids, db, num_questions)
        
        # Update quiz with generated data
        quiz.title = quiz_data['title']
        quiz.description = quiz_data['description']
        quiz.topics = quiz_data['topics']
        quiz.questions = quiz_data['questions']
        quiz.status = 'completed'
        
        db.commit()
        
        return {
            'status': 'completed',
            'quiz_id': quiz_id,
            'questions_generated': len(quiz_data['questions'])
        }
        
    except Exception as e:
        db.rollback()
        # Update quiz status to failed
        if 'quiz' in locals():
            quiz.status = 'failed'
            db.commit()
        
        return {
            'status': 'failed',
            'error': str(e),
            'quiz_id': quiz_id
        }
    finally:
        db.close()

if __name__ == '__main__':
    # For development only
    app.run(debug=True, host='0.0.0.0', port=5000) 