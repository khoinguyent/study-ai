import requests
import json
from typing import Dict, Any


class OllamaProvider:
    name = "ollama"

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
        temperature: float = 0.2,
    ):
        self.base_url = base_url
        self.model = model
        self.temperature = temperature

    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        prompt = f"{system_prompt}\n\n{user_prompt}\n\nReturn ONLY JSON."
        resp = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "options": {"temperature": self.temperature}
            }
        )
        resp.raise_for_status()
        text = resp.json().get("response", "")
        i, j = text.find("{"), text.rfind("}")
        return json.loads(text[i:j+1]) if i >= 0 and j >= 0 else {}


