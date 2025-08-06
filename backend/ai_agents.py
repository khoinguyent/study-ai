import openai
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import json
from database import get_vector_similarity_scores
from document_processor import document_processor

load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

class AIAgents:
    def __init__(self):
        self.model = "gpt-4"
        self.max_tokens = 2000
    
    def topic_extractor_agent(self, document_ids: List[str], db_session) -> List[str]:
        """
        Agent 1: Extract key topics from selected documents
        
        Args:
            document_ids: List of document IDs to analyze
            db_session: Database session
            
        Returns:
            List of extracted topics
        """
        try:
            # Get sample text chunks from the documents
            sample_chunks = self._get_sample_chunks(document_ids, db_session, limit=20)
            
            if not sample_chunks:
                return ["General Knowledge"]
            
            # Create prompt for topic extraction
            prompt = f"""
            Analyze the following text samples from educational documents and identify 5-8 diverse, specific topics that would be suitable for creating quiz questions.
            
            Text samples:
            {sample_chunks[:2000]}  # Limit to avoid token limits
            
            Instructions:
            1. Identify distinct, specific topics (e.g., "Cell Structure", "Photosynthesis", "DNA Replication")
            2. Focus on topics that can generate meaningful quiz questions
            3. Ensure diversity across different subject areas
            4. Return only the topic names, one per line
            
            Topics:
            """
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert educational content analyzer. Extract specific, diverse topics suitable for quiz generation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.3
            )
            
            # Parse topics from response
            topics_text = response.choices[0].message.content.strip()
            topics = [topic.strip() for topic in topics_text.split('\n') if topic.strip()]
            
            # Clean and validate topics
            topics = [topic for topic in topics if len(topic) > 2 and len(topic) < 100]
            
            return topics[:8]  # Limit to 8 topics
            
        except Exception as e:
            print(f"Error in topic extraction: {e}")
            return ["General Knowledge"]
    
    def question_generator_agent(self, topic: str, document_ids: List[str], db_session) -> str:
        """
        Agent 2: Generate relevant context for a specific topic
        
        Args:
            topic: The topic to find context for
            document_ids: List of document IDs to search within
            db_session: Database session
            
        Returns:
            Relevant context text for the topic
        """
        try:
            # Generate embedding for the topic
            topic_embedding = document_processor.generate_embeddings(topic)
            
            # Find similar chunks using vector similarity
            similar_chunks = get_vector_similarity_scores(
                topic_embedding, 
                document_ids=document_ids, 
                limit=5
            )
            
            if not similar_chunks:
                return f"Context for topic: {topic}"
            
            # Combine relevant chunks
            context_parts = []
            for chunk_id, similarity_score, content in similar_chunks:
                if similarity_score > 0.7:  # Only include highly relevant chunks
                    context_parts.append(content)
            
            context = "\n\n".join(context_parts)
            
            return context if context.strip() else f"Context for topic: {topic}"
            
        except Exception as e:
            print(f"Error in question generation: {e}")
            return f"Context for topic: {topic}"
    
    def quiz_creator_agent(self, topic: str, context: str) -> Dict[str, Any]:
        """
        Agent 3: Create a quiz question from context
        
        Args:
            topic: The topic for the question
            context: Relevant context text
            
        Returns:
            Structured question object
        """
        try:
            prompt = f"""
            Create a high-quality multiple-choice question based on the following topic and context.
            
            Topic: {topic}
            Context: {context}
            
            Instructions:
            1. Create a clear, specific question that tests understanding
            2. Provide 4 answer options (A, B, C, D)
            3. Mark the correct answer
            4. Include a brief explanation for the correct answer
            5. Ensure the question is appropriate for educational assessment
            
            Return the response in the following JSON format:
            {{
                "question": "The question text here?",
                "options": {{
                    "A": "Option A text",
                    "B": "Option B text", 
                    "C": "Option C text",
                    "D": "Option D text"
                }},
                "correct_answer": "A",
                "explanation": "Brief explanation of why this is correct",
                "difficulty": "easy|medium|hard",
                "topic": "{topic}"
            }}
            """
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert educational content creator. Create clear, accurate multiple-choice questions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.4
            )
            
            # Parse JSON response
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response
            try:
                # Find JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                json_str = response_text[start_idx:end_idx]
                
                question_data = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['question', 'options', 'correct_answer', 'explanation']
                for field in required_fields:
                    if field not in question_data:
                        raise ValueError(f"Missing required field: {field}")
                
                return question_data
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing question JSON: {e}")
                # Return a fallback question
                return self._create_fallback_question(topic)
                
        except Exception as e:
            print(f"Error in quiz creation: {e}")
            return self._create_fallback_question(topic)
    
    def _get_sample_chunks(self, document_ids: List[str], db_session, limit: int = 20) -> str:
        """Get sample text chunks from documents for topic extraction"""
        try:
            from models import DocumentChunk
            
            # Get random sample of chunks from the documents
            chunks = db_session.query(DocumentChunk.content)\
                .filter(DocumentChunk.document_id.in_(document_ids))\
                .limit(limit)\
                .all()
            
            if not chunks:
                return ""
            
            # Combine chunk contents
            sample_text = "\n\n".join([chunk.content for chunk in chunks])
            return sample_text
            
        except Exception as e:
            print(f"Error getting sample chunks: {e}")
            return ""
    
    def _create_fallback_question(self, topic: str) -> Dict[str, Any]:
        """Create a fallback question when AI generation fails"""
        return {
            "question": f"What is the main concept related to {topic}?",
            "options": {
                "A": "A fundamental principle",
                "B": "A secondary detail", 
                "C": "An unrelated concept",
                "D": "A minor aspect"
            },
            "correct_answer": "A",
            "explanation": f"This question tests understanding of the main concept in {topic}.",
            "difficulty": "medium",
            "topic": topic
        }
    
    def create_quiz(self, document_ids: List[str], db_session, num_questions: int = 10) -> Dict[str, Any]:
        """
        Main function to orchestrate the entire agentic workflow
        
        Args:
            document_ids: List of document IDs to create quiz from
            db_session: Database session
            num_questions: Number of questions to generate
            
        Returns:
            Complete quiz object
        """
        try:
            # Step 1: Extract topics
            print("Extracting topics...")
            topics = self.topic_extractor_agent(document_ids, db_session)
            
            if not topics:
                topics = ["General Knowledge"]
            
            # Step 2 & 3: Generate questions for each topic
            questions = []
            questions_per_topic = max(1, num_questions // len(topics))
            
            for topic in topics:
                print(f"Generating questions for topic: {topic}")
                
                # Get context for the topic
                context = self.question_generator_agent(topic, document_ids, db_session)
                
                # Generate questions for this topic
                for i in range(questions_per_topic):
                    if len(questions) >= num_questions:
                        break
                    
                    question = self.quiz_creator_agent(topic, context)
                    questions.append(question)
            
            # Create quiz object
            quiz = {
                "title": f"Quiz from {len(document_ids)} document(s)",
                "description": f"Generated quiz covering {len(topics)} topics",
                "topics": topics,
                "questions": questions,
                "total_questions": len(questions),
                "document_ids": document_ids
            }
            
            return quiz
            
        except Exception as e:
            print(f"Error creating quiz: {e}")
            # Return a basic quiz structure
            return {
                "title": "Quiz Generation Failed",
                "description": "Failed to generate quiz questions",
                "topics": ["General Knowledge"],
                "questions": [self._create_fallback_question("General Knowledge")],
                "total_questions": 1,
                "document_ids": document_ids
            }

# Global AI agents instance
ai_agents = AIAgents() 