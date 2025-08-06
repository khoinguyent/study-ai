from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_restful import Api
import os
from dotenv import load_dotenv
from celery import Celery

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/study_ai')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CORS
CORS(app)

# Initialize API
api = Api(app)

# Initialize Celery
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    )
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

celery = make_celery(app)

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
    return jsonify({
        'status': 'ok',
        'services': {
            'web': 'running',
            'database': 'connected',
            'redis': 'connected',
            'celery': 'running'
        }
    })

# API Routes
@app.route('/api/upload', methods=['POST'])
def upload_document():
    """Upload and process documents"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # TODO: Implement file processing logic
    # This would typically:
    # 1. Save the file temporarily
    # 2. Queue a Celery task for processing
    # 3. Return a task ID for tracking
    
    return jsonify({
        'message': 'File uploaded successfully',
        'filename': file.filename,
        'task_id': 'task_123'  # This would be the actual Celery task ID
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests"""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400
    
    # TODO: Implement chat logic
    # This would typically:
    # 1. Process the user message
    # 2. Query the vector database
    # 3. Generate AI response
    
    return jsonify({
        'response': f"AI response to: {data['message']}",
        'sources': []
    })

# Celery Tasks
@celery.task
def process_document(file_path, user_id):
    """Background task to process uploaded documents"""
    try:
        # TODO: Implement document processing
        # 1. Extract text from document
        # 2. Chunk the text
        # 3. Generate embeddings
        # 4. Store in vector database
        
        return {
            'status': 'completed',
            'file_path': file_path,
            'user_id': user_id
        }
    except Exception as e:
        return {
            'status': 'failed',
            'error': str(e),
            'file_path': file_path,
            'user_id': user_id
        }

@celery.task
def generate_ai_response(message, context):
    """Background task to generate AI responses"""
    try:
        # TODO: Implement AI response generation
        # 1. Process the message
        # 2. Query relevant context
        # 3. Generate response using OpenAI
        
        return {
            'status': 'completed',
            'response': f"AI response to: {message}",
            'context': context
        }
    except Exception as e:
        return {
            'status': 'failed',
            'error': str(e),
            'message': message
        }

if __name__ == '__main__':
    # For development only
    app.run(debug=True, host='0.0.0.0', port=5000) 