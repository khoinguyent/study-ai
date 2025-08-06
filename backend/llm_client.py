import os
import json
from typing import List, Dict, Any, Optional
from config import config

class LLMClient:
    """Unified LLM client for local models (Ollama/LlamaIndex) and OpenAI"""
    
    def __init__(self):
        self.llm_config = config.get_llm_config()
        self.llm_type = self.llm_config['type']
        
        if self.llm_type == 'local':
            self._init_local_llm()
        else:
            self._init_openai_llm()
    
    def _init_local_llm(self):
        """Initialize local LLM (Ollama)"""
        try:
            import requests
            
            # Test Ollama connection
            response = requests.get(f"{self.llm_config['ollama_base_url']}/api/tags")
            if response.status_code == 200:
                print(f"✅ Ollama connected: {self.llm_config['ollama_base_url']}")
                self.use_ollama = True
            else:
                raise Exception("Ollama not responding")
                
        except Exception as e:
            print(f"⚠️ Ollama not available: {e}")
            print("Falling back to LlamaIndex...")
            self.use_ollama = False
            self._init_llamaindex()
    
    def _init_llamaindex(self):
        """Initialize LlamaIndex for local models"""
        try:
            from llama_index.llms import LlamaCPP
            from llama_index.embeddings import HuggingFaceEmbedding
            
            # Initialize LlamaCPP model
            model_path = os.path.join(
                self.llm_config['llamaindex_model_path'],
                self.llm_config['llamaindex_model_name']
            )
            
            if os.path.exists(model_path):
                self.llm = LlamaCPP(
                    model_path=model_path,
                    temperature=0.1,
                    max_new_tokens=256,
                    context_window=3900,
                    generate_kwargs={},
                    model_kwargs={"n_gpu_layers": 1},
                    verbose=True,
                )
                
                # Initialize embeddings
                self.embedding_model = HuggingFaceEmbedding(
                    model_name="sentence-transformers/all-MiniLM-L6-v2"
                )
                
                print(f"✅ LlamaIndex initialized: {model_path}")
            else:
                raise Exception(f"Model file not found: {model_path}")
                
        except ImportError:
            raise ImportError("LlamaIndex not installed. Run: pip install llama-index llama-cpp-python")
        except Exception as e:
            raise Exception(f"Failed to initialize LlamaIndex: {e}")
    
    def _init_openai_llm(self):
        """Initialize OpenAI LLM"""
        try:
            import openai
            
            openai.api_key = self.llm_config['api_key']
            self.openai_model = self.llm_config['model']
            self.openai_embedding_model = self.llm_config['embedding_model']
            
            print(f"✅ OpenAI initialized: {self.openai_model}")
            
        except ImportError:
            raise ImportError("OpenAI not installed. Run: pip install openai")
        except Exception as e:
            raise Exception(f"Failed to initialize OpenAI: {e}")
    
    def generate_text(self, prompt: str, max_tokens: int = 2000) -> str:
        """
        Generate text using the configured LLM
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        try:
            if self.llm_type == 'local':
                if self.use_ollama:
                    return self._generate_with_ollama(prompt, max_tokens)
                else:
                    return self._generate_with_llamaindex(prompt, max_tokens)
            else:
                return self._generate_with_openai(prompt, max_tokens)
                
        except Exception as e:
            print(f"Error generating text: {e}")
            return f"Error: {str(e)}"
    
    def _generate_with_ollama(self, prompt: str, max_tokens: int) -> str:
        """Generate text using Ollama"""
        try:
            import requests
            
            response = requests.post(
                f"{self.llm_config['ollama_base_url']}/api/generate",
                json={
                    "model": self.llm_config['ollama_model'],
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7
                    }
                }
            )
            
            if response.status_code == 200:
                return response.json()['response']
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Ollama generation failed: {e}")
    
    def _generate_with_llamaindex(self, prompt: str, max_tokens: int) -> str:
        """Generate text using LlamaIndex"""
        try:
            response = self.llm.complete(prompt)
            return response.text
            
        except Exception as e:
            raise Exception(f"LlamaIndex generation failed: {e}")
    
    def _generate_with_openai(self, prompt: str, max_tokens: int) -> str:
        """Generate text using OpenAI"""
        try:
            import openai
            
            response = openai.ChatCompletion.create(
                model=self.openai_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"OpenAI generation failed: {e}")
    
    def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings for text
        
        Args:
            text: Input text
            
        Returns:
            List of embedding values
        """
        try:
            if self.llm_type == 'local':
                if self.use_ollama:
                    return self._generate_embeddings_with_ollama(text)
                else:
                    return self._generate_embeddings_with_llamaindex(text)
            else:
                return self._generate_embeddings_with_openai(text)
                
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            # Return zero vector as fallback
            return [0.0] * 1536
    
    def _generate_embeddings_with_ollama(self, text: str) -> List[float]:
        """Generate embeddings using Ollama"""
        try:
            import requests
            
            response = requests.post(
                f"{self.llm_config['ollama_base_url']}/api/embeddings",
                json={
                    "model": self.llm_config['ollama_embedding_model'],
                    "prompt": text
                }
            )
            
            if response.status_code == 200:
                return response.json()['embedding']
            else:
                raise Exception(f"Ollama embeddings API error: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Ollama embeddings failed: {e}")
    
    def _generate_embeddings_with_llamaindex(self, text: str) -> List[float]:
        """Generate embeddings using LlamaIndex"""
        try:
            embedding = self.embedding_model.get_text_embedding(text)
            return embedding
            
        except Exception as e:
            raise Exception(f"LlamaIndex embeddings failed: {e}")
    
    def _generate_embeddings_with_openai(self, text: str) -> List[float]:
        """Generate embeddings using OpenAI"""
        try:
            import openai
            
            response = openai.Embedding.create(
                model=self.openai_embedding_model,
                input=text
            )
            
            return response['data'][0]['embedding']
            
        except Exception as e:
            raise Exception(f"OpenAI embeddings failed: {e}")
    
    def chat_completion(self, messages: List[Dict[str, str]], max_tokens: int = 2000) -> str:
        """
        Generate chat completion
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response
        """
        try:
            if self.llm_type == 'local':
                if self.use_ollama:
                    return self._chat_with_ollama(messages, max_tokens)
                else:
                    return self._chat_with_llamaindex(messages, max_tokens)
            else:
                return self._chat_with_openai(messages, max_tokens)
                
        except Exception as e:
            print(f"Error in chat completion: {e}")
            return f"Error: {str(e)}"
    
    def _chat_with_ollama(self, messages: List[Dict[str, str]], max_tokens: int) -> str:
        """Chat completion using Ollama"""
        try:
            import requests
            
            # Convert messages to Ollama format
            prompt = ""
            for message in messages:
                if message['role'] == 'system':
                    prompt += f"System: {message['content']}\n"
                elif message['role'] == 'user':
                    prompt += f"User: {message['content']}\n"
                elif message['role'] == 'assistant':
                    prompt += f"Assistant: {message['content']}\n"
            
            prompt += "Assistant: "
            
            response = requests.post(
                f"{self.llm_config['ollama_base_url']}/api/generate",
                json={
                    "model": self.llm_config['ollama_model'],
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7
                    }
                }
            )
            
            if response.status_code == 200:
                return response.json()['response']
            else:
                raise Exception(f"Ollama chat API error: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Ollama chat failed: {e}")
    
    def _chat_with_llamaindex(self, messages: List[Dict[str, str]], max_tokens: int) -> str:
        """Chat completion using LlamaIndex"""
        try:
            # Convert messages to single prompt
            prompt = ""
            for message in messages:
                if message['role'] == 'system':
                    prompt += f"System: {message['content']}\n"
                elif message['role'] == 'user':
                    prompt += f"User: {message['content']}\n"
                elif message['role'] == 'assistant':
                    prompt += f"Assistant: {message['content']}\n"
            
            prompt += "Assistant: "
            
            response = self.llm.complete(prompt)
            return response.text
            
        except Exception as e:
            raise Exception(f"LlamaIndex chat failed: {e}")
    
    def _chat_with_openai(self, messages: List[Dict[str, str]], max_tokens: int) -> str:
        """Chat completion using OpenAI"""
        try:
            import openai
            
            response = openai.ChatCompletion.create(
                model=self.openai_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"OpenAI chat failed: {e}")

# Global LLM client instance
llm_client = LLMClient() 