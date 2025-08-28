from typing import Dict, Any, Optional, List
from openai import OpenAI
import json
import logging

logger = logging.getLogger(__name__)

class OpenAIProvider:
    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        base_url: Optional[str] = None,
        vector_store_ids: Optional[List[str]] = None,
    ):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.temperature = temperature
        self.vector_store_ids = vector_store_ids or []

    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        try:
            logger.info(
                "[OPENAI] Preparing request",
                extra={
                    "provider": "openai",
                    "model": self.model,
                    "temperature": self.temperature,
                    "system_prompt_preview": (system_prompt[:200] + "...") if len(system_prompt) > 200 else system_prompt,
                    "user_prompt_preview": (user_prompt[:200] + "...") if len(user_prompt) > 200 else user_prompt,
                },
            )
            
            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Add vector store context if available
            if self.vector_store_ids:
                logger.info(f"Using vector store IDs: {self.vector_store_ids}")
            
            # Create chat completion with timeout
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                response_format={"type": "json_object"},
                timeout=120  # 2 minute timeout
            )
            
            logger.info(
                "[OPENAI] API call completed",
                extra={
                    "provider": "openai",
                    "model": self.model,
                    "usage": getattr(response, "usage", None).__dict__ if getattr(response, "usage", None) else None,
                },
            )
            
            # Extract and parse response
            response_text = response.choices[0].message.content
            if not response_text:
                logger.warning("OpenAI returned empty response")
                return {}
                
            try:
                parsed = json.loads(response_text)
                # Log a safe preview of the parsed JSON
                try:
                    preview = json.dumps(parsed)[:1000]
                except Exception:
                    preview = str(parsed)[:1000]
                logger.info(
                    "[OPENAI] Parsed JSON response",
                    extra={
                        "provider": "openai",
                        "model": self.model,
                        "response_preview": preview,
                    },
                )
                return parsed
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response as JSON: {e}")
                logger.error(f"Raw response: {response_text[:500]}...")
                return {}
                
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise


