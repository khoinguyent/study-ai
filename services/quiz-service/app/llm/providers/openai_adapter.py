from typing import Dict, Any, Optional, List
from openai import OpenAI
import json


class OpenAIProvider:
    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
    ):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        r = self.client.responses.create(
            model=self.model,
            temperature=self.temperature,
            input=[
                {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "text", "text": user_prompt}]}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(r.output_text or "{}")


