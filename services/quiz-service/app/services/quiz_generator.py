"""
Quiz Generator Service for Study AI Platform
Handles AI-powered quiz generation using Ollama
"""

import asyncio
import json
import httpx
from typing import List, Dict, Any
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class QuizGenerator:
    """Service for generating quizzes using AI"""
    
    def __init__(self):
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        logger.info(f"Initialized QuizGenerator with Ollama URL: {self.ollama_url}, Model: {self.model}")
    
    async def generate_quiz(
        self, 
        topic: str, 
        difficulty: str, 
        num_questions: int, 
        context_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate a quiz based on search results"""
        try:
            # Prepare context from search results
            context = self._prepare_context_from_chunks(context_chunks)
            
            # Create prompt for quiz generation
            prompt = self._create_quiz_prompt(topic, difficulty, num_questions, context)
            
            # Generate quiz using Ollama
            quiz_content = await self._call_ollama(prompt)
            
            # Parse the response
            quiz_data = self._parse_quiz_response(quiz_content)
            
            return quiz_data
            
        except Exception as e:
            logger.error(f"Error generating quiz: {str(e)}")
            raise
    
    async def generate_quiz_from_context(
        self,
        topic: str,
        difficulty: str,
        num_questions: int,
        context_chunks: List[Dict[str, Any]],
        source_type: str,
        source_id: str
    ) -> Dict[str, Any]:
        """Generate a quiz from specific context (subject or category)"""
        try:
            # Prepare context from chunks
            context = self._prepare_context_from_chunks(context_chunks)
            
            # Create prompt for context-based quiz generation
            prompt = self._create_context_quiz_prompt(
                topic, difficulty, num_questions, context, source_type
            )
            
            # Generate quiz using Ollama
            quiz_content = await self._call_ollama(prompt)
            
            # Parse the response
            quiz_data = self._parse_quiz_response(quiz_content)
            
            # Add source information
            quiz_data["source_type"] = source_type
            quiz_data["source_id"] = source_id
            
            return quiz_data
            
        except Exception as e:
            logger.error(f"Error generating context-based quiz: {str(e)}")
            raise
    
    def _prepare_context_from_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """Prepare context string from document chunks"""
        if not chunks:
            return "No specific context available."
        
        context_parts = []
        for chunk in chunks:
            if isinstance(chunk, dict):
                content = chunk.get("content", "")
                if content:
                    context_parts.append(content)
            else:
                # Handle case where chunk might be a different structure
                context_parts.append(str(chunk))
        
        return "\n\n".join(context_parts)
    
    def _create_quiz_prompt(
        self, 
        topic: str, 
        difficulty: str, 
        num_questions: int, 
        context: str
    ) -> str:
        """Create a prompt for quiz generation using the working structure"""
        return f"""You are an expert quiz creator. Based ONLY on the provided context, generate exactly {num_questions} multiple-choice questions to help a student learn about {topic}.

Your response MUST be a single JSON object with this exact structure:
{{
    "title": "Quiz Title",
    "description": "Brief description of the quiz",
    "questions": [
        {{
            "id": "q1",
            "question": "Question text?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": 0,
            "explanation": "Why this answer is correct"
        }}
    ]
}}

IMPORTANT RULES:
1. Create exactly {num_questions} questions
2. Each question must have exactly 4 options (A, B, C, D)
3. correct_answer must be 0, 1, 2, or 3 (where 0=A, 1=B, 2=C, 3=D)
4. Base ALL questions ONLY on the provided context - do not use external knowledge
5. If the context is insufficient, create questions about what IS available in the context
6. Vary the difficulty appropriately for {difficulty} level
7. Make sure the JSON is valid and properly formatted

Context:
{context}

Generate the quiz based ONLY on the provided context:"""
    
    def _create_context_quiz_prompt(
        self,
        topic: str,
        difficulty: str,
        num_questions: int,
        context: str,
        source_type: str
    ) -> str:
        """Create a prompt for context-based quiz generation"""
        return f"""You are an expert quiz creator. Based ONLY on the provided context from the {source_type}, generate exactly {num_questions} multiple-choice questions to help a student learn about {topic}.

Your response MUST be a single JSON object with this exact structure:
{{
    "title": "Quiz Title",
    "description": "Brief description of the quiz",
    "questions": [
        {{
            "id": "q1",
            "question": "Question text?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": 0,
            "explanation": "Why this answer is correct"
        }}
    ]
}}

IMPORTANT RULES:
1. Create exactly {num_questions} questions
2. Each question must have exactly 4 options (A, B, C, D)
3. correct_answer must be 0, 1, 2, or 3 (where 0=A, 1=B, 2=C, 3=D)
4. Base ALL questions ONLY on the provided context from the {source_type} - do not use external knowledge
5. If the context is insufficient, create questions about what IS available in the context
6. Vary the difficulty appropriately for {difficulty} level
7. Make sure the JSON is valid and properly formatted

Context from {source_type}:
{context}

Generate the quiz based ONLY on the provided context:"""
    
    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API to generate content"""
        try:
            logger.info(f"Calling Ollama at {self.ollama_url} with model {self.model}")
            
            # Use explicit timeout configuration for better control
            timeout_config = httpx.Timeout(1200.0)  # 20 minute timeout
            
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"  # Ensure JSON format is requested
                    }
                )
                
                logger.info(f"Ollama response status: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = response.text if response.text else "No error text"
                    logger.error(f"Ollama API error: {response.status_code} - {error_text}")
                    raise Exception(f"Ollama API error: {response.status_code} - {error_text}")
                
                result = response.json()
                response_text = result.get("response", "")
                logger.info(f"Ollama response length: {len(response_text)} characters")
                return response_text
            
            # For testing, return a mock response instead of calling Ollama
            """
            logger.info("Using mock response for testing")
            mock_response = '''{
                "title": "Tay Son Rebellion Quiz",
                "description": "Test quiz about the Tay Son Rebellion",
                "questions": [
                    {
                        "id": "q1",
                        "question": "What was the main cause of the Tay Son Rebellion?",
                        "options": ["Economic hardship", "Religious conflict", "Foreign invasion", "Natural disaster"],
                        "correct_answer": 0,
                        "explanation": "The rebellion was primarily caused by economic hardship and social inequality."
                    }
                ]
            }'''
            return mock_response
            """
                
        except httpx.TimeoutException:
            logger.error("Ollama request timed out")
            raise Exception("Ollama request timed out")
        except httpx.ConnectError:
            logger.error(f"Failed to connect to Ollama at {self.ollama_url}")
            raise Exception(f"Failed to connect to Ollama at {self.ollama_url}")
        except Exception as e:
            logger.error(f"Error calling Ollama: {str(e)}")
            logger.error(f"Ollama URL: {self.ollama_url}")
            logger.error(f"Model: {self.model}")
            raise
    
    def _parse_quiz_response(self, response: str) -> Dict[str, Any]:
        """Parse the quiz response from Ollama"""
        try:
            # Try to extract JSON from the response
            # Look for JSON content between ```json and ``` or just parse the whole response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_content = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_content = response[json_start:json_end].strip()
            else:
                json_content = response.strip()
            
            # Parse JSON
            quiz_data = json.loads(json_content)
            
            # Validate structure
            if "title" not in quiz_data or "questions" not in quiz_data:
                raise ValueError("Invalid quiz structure")
            
            return quiz_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse quiz response as JSON: {str(e)}")
            logger.error(f"Response content: {response[:500]}...")
            # Return a fallback quiz structure
            return {
                "title": "Generated Quiz",
                "description": "Quiz generated from content",
                "questions": [
                    {
                        "id": "q1",
                        "question": "Sample question based on the content?",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_answer": 0,
                        "explanation": "This is a sample question."
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Error parsing quiz response: {str(e)}")
            raise 