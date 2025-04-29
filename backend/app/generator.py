from abc import ABC, abstractmethod
import httpx
from typing import Iterator, Any, Dict
import json

class BaseGenerator(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt."""
        pass

    @abstractmethod
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Stream generated text from a prompt."""
        pass

class OllamaGenerator(BaseGenerator):
    def __init__(self, api_url: str, model_name: str, timeout: float = 60):
        self.api_url = api_url.rstrip('/')
        self.model_name = model_name
        self.timeout = timeout

    def generate(self, prompt: str, **kwargs) -> str:
        try:
            payload = {"model": self.model_name, "prompt": prompt}
            with httpx.stream("POST", f"{self.api_url}/api/generate", json=payload, timeout=self.timeout) as r:
                r.raise_for_status()
                full_response = ""
                for chunk in r.iter_lines():
                    if chunk:
                        try:
                            data = json.loads(chunk)
                            if "response" in data:
                                full_response += data["response"]
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
                return full_response.strip()
        except (httpx.HTTPStatusError, Exception):
            return "Model not available"

    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        try:
            payload = {"model": self.model_name, "prompt": prompt, "stream": True}
            with httpx.stream("POST", f"{self.api_url}/api/generate", json=payload, timeout=self.timeout) as r:
                r.raise_for_status()
                for chunk in r.iter_lines():
                    if chunk:
                        try:
                            data = json.loads(chunk)
                            if "response" in data:
                                yield data["response"]
                        except json.JSONDecodeError:
                            continue
        except (httpx.HTTPStatusError, Exception):
            yield "Model not available"

class DummyGenerator(BaseGenerator):
    def generate(self, prompt: str, **kwargs) -> str:
        return f"[DEV] {prompt}"

    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        yield f"[DEV] {prompt}" 