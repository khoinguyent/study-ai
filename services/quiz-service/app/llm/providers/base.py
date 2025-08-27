from typing import Protocol, Dict, Any


class LLMProvider(Protocol):
    name: str

    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        ...


