import asyncio
import json
import httpx
from typing import List, Dict, Any
from ..config import settings

class QuizGenerator:
    def __init__(self):
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.notification_url = settings.NOTIFICATION_SERVICE_URL
    
    async def create_task_status(self, task_id: str, user_id: str, task_type: str, status: str = "pending", progress: int = 0, message: str = None):
        """Create a task status in the notification service"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.notification_url}/task-status",
                    json={
                        "task_id": task_id,
                        "user_id": user_id,
                        "task_type": task_type,
                        "status": status,
                        "progress": progress,
                        "message": message
                    }
                )
                return response.json()
            except Exception as e:
                print(f"Failed to create task status: {e}")
    
    async def update_task_status(self, task_id: str, status: str, progress: int = None, message: str = None):
        """Update task status in the notification service"""
        async with httpx.AsyncClient() as client:
            try:
                update_data = {"status": status}
                if progress is not None:
                    update_data["progress"] = progress
                if message is not None:
                    update_data["message"] = message
                
                response = await client.put(
                    f"{self.notification_url}/task-status/{task_id}",
                    json=update_data
                )
                return response.json()
            except Exception as e:
                print(f"Failed to update task status: {e}")
    
    async def generate_quiz(self, topic: str, difficulty: str, num_questions: int, context_chunks: List[Dict[str, Any]], user_id: str):
        """Generate a quiz using Ollama"""
        task_id = f"quiz_gen_{topic}_{asyncio.get_event_loop().time()}"
        
        try:
            # Create initial task status
            await self.create_task_status(
                task_id=task_id,
                user_id=user_id,
                task_type="quiz_generation",
                status="processing",
                progress=10,
                message="Starting quiz generation..."
            )
            
            # Prepare context from chunks
            context = "\n".join([chunk.get("content", "") for chunk in context_chunks[:5]])  # Use first 5 chunks
            
            await self.update_task_status(
                task_id=task_id,
                status="processing",
                progress=30,
                message="Analyzing document content..."
            )
            
            # Create prompt for quiz generation
            prompt = self._create_quiz_prompt(topic, difficulty, num_questions, context)
            
            await self.update_task_status(
                task_id=task_id,
                status="processing",
                progress=50,
                message="Generating quiz questions..."
            )
            
            # Generate quiz using Ollama
            quiz_content = await self._call_ollama(prompt)
            
            await self.update_task_status(
                task_id=task_id,
                status="processing",
                progress=80,
                message="Formatting quiz content..."
            )
            
            # Parse the response
            parsed_quiz = self._parse_quiz_response(quiz_content)
            
            await self.update_task_status(
                task_id=task_id,
                status="completed",
                progress=100,
                message="Quiz generated successfully!"
            )
            
            return parsed_quiz
            
        except Exception as e:
            await self.update_task_status(
                task_id=task_id,
                status="failed",
                progress=0,
                message=f"Quiz generation failed: {str(e)}"
            )
            raise
    
    def _create_quiz_prompt(self, topic: str, difficulty: str, num_questions: int, context: str) -> str:
        """Create a prompt for quiz generation"""
        return f"""You are an expert educator creating a quiz. Based on the following context about {topic}, create a {difficulty} level quiz with {num_questions} multiple choice questions.

Context:
{context}

Please generate a quiz in the following JSON format:
{{
    "title": "Quiz Title",
    "questions": [
        {{
            "question": "Question text?",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
            "explanation": "Explanation of why this is correct"
        }}
    ]
}}

Make sure the questions are relevant to the context provided and appropriate for {difficulty} level. Each question should have exactly 4 options (A, B, C, D) and one correct answer."""
    
    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API to generate content"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=120.0  # 2 minutes timeout
                )
                
                if response.status_code != 200:
                    raise Exception(f"Ollama API error: {response.text}")
                
                result = response.json()
                return result.get("response", "")
                
            except Exception as e:
                raise Exception(f"Failed to call Ollama: {str(e)}")
    
    def _parse_quiz_response(self, response: str) -> Dict[str, Any]:
        """Parse the quiz response from Ollama"""
        try:
            # Try to extract JSON from the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                quiz_data = json.loads(json_str)
                
                # Validate the structure
                if "title" not in quiz_data or "questions" not in quiz_data:
                    raise ValueError("Invalid quiz structure")
                
                return quiz_data
            else:
                # Fallback: create a simple quiz structure
                return {
                    "title": "Generated Quiz",
                    "questions": [
                        {
                            "question": "Sample question based on the content?",
                            "options": ["A", "B", "C", "D"],
                            "correct_answer": "A",
                            "explanation": "This is a sample explanation."
                        }
                    ]
                }
                
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to parse quiz response: {e}")
            # Return a fallback quiz
            return {
                "title": "Generated Quiz",
                "questions": [
                    {
                        "question": "Sample question based on the content?",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": "A",
                        "explanation": "This is a sample explanation."
                    }
                ]
            } 