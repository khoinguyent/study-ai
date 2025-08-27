import requests
import json
import os
from typing import Dict, Any


class HFProvider:
    name = "huggingface"

    def __init__(self, model_id: str, api_key: str | None = None, temperature: float = 0.2):
        self.model_id = model_id
        self.api_key = api_key or os.getenv("HF_API_KEY")
        self.temperature = temperature

    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        prompt = f"{system_prompt}\n\n{user_prompt}\n\nReturn ONLY JSON."
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        r = requests.post(
            f"https://api-inference.huggingface.co/models/{self.model_id}",
            headers=headers,
            json={"inputs": prompt, "parameters": {"temperature": self.temperature}}
        )
        r.raise_for_status()
        out = r.json()
        txt = out[0]["generated_text"] if isinstance(out, list) else r.text
        i, j = txt.find("{"), txt.rfind("}")
        return json.loads(txt[i:j+1]) if i >= 0 and j >= 0 else {}


