"""
Quiz Generator Service for Study AI Platform
Handles AI-powered quiz generation using Ollama, HuggingFace, and OpenAI
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
        self.strategy = settings.QUIZ_GENERATION_STRATEGY
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.ollama_model = settings.OLLAMA_MODEL
        self.huggingface_url = settings.HUGGINGFACE_API_URL
        self.huggingface_token = settings.HUGGINGFACE_TOKEN
        self.question_model = settings.QUESTION_GENERATION_MODEL
        
        # OpenAI configuration
        self.openai_api_key = settings.OPENAI_API_KEY
        self.openai_base_url = settings.OPENAI_BASE_URL
        self.openai_model = settings.OPENAI_MODEL
        self.openai_max_tokens = settings.OPENAI_MAX_TOKENS
        self.openai_temperature = settings.OPENAI_TEMPERATURE
        
        # Initialize OpenAI client if API key is available
        self.openai_client = None
        if self.openai_api_key:
            try:
                import openai
                openai.api_key = self.openai_api_key
                openai.base_url = self.openai_base_url
                self.openai_client = openai
                logger.info("OpenAI client initialized successfully")
            except ImportError:
                logger.warning("OpenAI package not available, OpenAI integration disabled")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {str(e)}")
        
        logger.info(f"Initialized QuizGenerator with strategy: {self.strategy}")
        if self.strategy in ["ollama", "auto"]:
            logger.info(f"Ollama URL: {self.ollama_url}, Model: {self.ollama_model}")
        if self.strategy in ["huggingface", "auto"]:
            logger.info(f"HuggingFace URL: {self.huggingface_url}, Model: {self.question_model}")
        if self.strategy in ["openai", "auto"] and self.openai_client:
            logger.info(f"OpenAI Model: {self.openai_model}, Base URL: {self.openai_base_url}")
    
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
            
            # Generate quiz using selected strategy
            quiz_content = await self._generate_content(prompt)
            
            # Parse the response if it's a string, otherwise use as-is
            if isinstance(quiz_content, str):
                quiz_data = self._parse_quiz_response(quiz_content)
            else:
                quiz_data = quiz_content
            
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
            
            # Generate quiz using selected strategy
            quiz_content = await self._generate_content(prompt)
            
            # Parse the response if it's a string, otherwise use as-is
            if isinstance(quiz_content, str):
                quiz_data = self._parse_quiz_response(quiz_content)
            else:
                quiz_data = quiz_content
            
            # Add source information
            quiz_data["source_type"] = source_type
            quiz_data["source_id"] = source_id
            
            return quiz_data
            
        except Exception as e:
            logger.error(f"Error generating context-based quiz: {str(e)}")
            raise

    def generate_quiz_from_context_sync(
        self,
        topic: str,
        difficulty: str,
        num_questions: int,
        context_chunks: List[Dict[str, Any]],
        source_type: str,
        source_id: str
    ) -> Dict[str, Any]:
        """Synchronous version of generate_quiz_from_context for Celery tasks"""
        try:
            # Prepare context from chunks
            context = self._prepare_context_from_chunks(context_chunks)
            
            # Create prompt for context-based quiz generation
            prompt = self._create_context_quiz_prompt(
                topic, difficulty, num_questions, context, source_type
            )
            
            # Generate quiz using selected strategy (synchronous)
            quiz_content = self._generate_content_sync(prompt)
            
            # Parse the response if it's a string, otherwise use as-is
            if isinstance(quiz_content, str):
                quiz_data = self._parse_quiz_response(quiz_content)
            else:
                quiz_data = quiz_content
            
            # Add source information
            quiz_data["source_type"] = source_type
            quiz_data["source_id"] = source_id
            
            return quiz_data
        except Exception as e:
            logger.error(f"Error generating context-based quiz (sync): {str(e)}")
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
            "options": [
            "Option A", "Option B", "Option C", "Option D"],
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
    
    async def _generate_content(self, prompt: str) -> str:
        """Generate content using the selected strategy"""
        try:
            # For testing, return mock data instead of making real API calls
            logger.info("Using mock data for testing instead of real API calls")
            return self._get_mock_quiz_data()
            
            # Uncomment the following code when ready to use real APIs
            # if self.strategy == "openai" and self.openai_client:
            #     return await self._call_openai(prompt)
            # elif self.strategy == "huggingface":
            #     return await self._call_huggingface(prompt)
            # elif self.strategy == "ollama":
            #     return await self._call_ollama(prompt)
            # elif self.strategy == "auto":
            #     # Try OpenAI first, then HuggingFace, fallback to Ollama
            #     try:
            #         if self.openai_client:
            #             return await self._call_openai(prompt)
            #     except Exception as e:
            #         logger.warning(f"OpenAI failed, trying HuggingFace: {str(e)}")
            #     
            #     try:
            #         return await self._call_huggingface(prompt)
            #     except Exception as e:
            #         logger.warning(f"HuggingFace failed, falling back to Ollama: {str(e)}")
            #         return await self._call_ollama(prompt)
            # else:
            #     raise Exception(f"Unknown strategy: {self.strategy}")
        except Exception as e:
            logger.error(f"Error in content generation: {str(e)}")
            raise

    def _generate_content_sync(self, prompt: str) -> dict:
        """Synchronous variant used from Celery tasks (mock only for tests)"""
        try:
            logger.info("Using mock data for testing instead of real API calls (sync)")
            return self._get_mock_quiz_data()
        except Exception as e:
            logger.error(f"Error in sync content generation: {str(e)}")
            raise
    
    def _get_mock_quiz_data(self) -> dict:
        """Return mock quiz data for testing"""
        mock_data = {
            "title": "Quiz Title",
            "description": "Brief description of the quiz",
            "questions": [
                {
                    "id": "q1",
                    "question": "Question text?",
                    "options": {
                        "option_1": {
                            "content": "Option 1 description",
                            "isCorrect": False
                        },
                        "option_2": {
                            "content": "Option 2 description",
                            "isCorrect": True
                        },
                        "option_3": {
                            "content": "Option 3 description",
                            "isCorrect": False
                        },
                        "option_4": {
                            "content": "Option 4 description",
                            "isCorrect": True
                        }
                    },
                    "explanation": "Why this answer is correct"
                }
            ]
        }
        
        return mock_data
    
    async def _call_huggingface(self, prompt: str) -> str:
        """Call HuggingFace API to generate content"""
        try:
            logger.info(f"Calling HuggingFace API with model {self.question_model}")
            
            if not self.huggingface_token:
                raise Exception("HuggingFace token not configured")
            
            headers = {
                "Authorization": f"Bearer {self.huggingface_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 1000,
                    "temperature": 0.7,
                    "return_full_text": False
                }
            }
            
            timeout_config = httpx.Timeout(120.0)  # 2 minute timeout
            
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                response = await client.post(
                    f"{self.huggingface_url}/{self.question_model}",
                    headers=headers,
                    json=payload
                )
                
                logger.info(f"HuggingFace response status: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = response.text if response.text else "No error text"
                    logger.error(f"HuggingFace API error: {response.status_code} - {error_text}")
                    raise Exception(f"HuggingFace API error: {response.status_code} - {error_text}")
                
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    response_text = result[0].get("generated_text", "")
                else:
                    response_text = str(result)
                
                logger.info(f"HuggingFace response length: {len(response_text)} characters")
                return response_text
                
        except Exception as e:
            logger.error(f"Error calling HuggingFace API: {str(e)}")
            raise
    
    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API to generate content"""
        try:
            logger.info(f"Calling Ollama at {self.ollama_url} with model {self.ollama_model}")
            
            # Use explicit timeout configuration for better control
            timeout_config = httpx.Timeout(1200.0)  # 20 minute timeout
            
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.ollama_model,
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
            logger.error(f"Model: {self.ollama_model}")
            raise
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API to generate content"""
        try:
            logger.info(f"Calling OpenAI API with model {self.openai_model}")
            
            if not self.openai_client:
                raise Exception("OpenAI client not initialized")
            
            if not self.openai_api_key:
                raise Exception("OpenAI API key not configured")
            
            # Create chat completion request
            response = await self.openai_client.chat.completions.acreate(
                model=self.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert quiz creator. Generate quizzes in valid JSON format based on the user's request."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.openai_max_tokens,
                temperature=self.openai_temperature,
                response_format={"type": "json_object"}
            )
            
            logger.info(f"OpenAI response received successfully")
            
            # Extract the response content
            response_text = response.choices[0].message.content
            logger.info(f"OpenAI response length: {len(response_text)} characters")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            logger.error(f"OpenAI Model: {self.openai_model}")
            logger.error(f"OpenAI Base URL: {self.openai_base_url}")
            raise
    
    def _parse_quiz_response(self, response: str) -> Dict[str, Any]:
        """Parse the quiz response from AI models (OpenAI, Ollama, HuggingFace)"""
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