"""
AI Provider abstraction layer supporting multiple LLM providers.
Supports: Anthropic Claude, OpenAI, Ollama (local), and Google Gemini.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import os
import json


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def generate_completion(self, prompt: str, system: Optional[str] = None,
                                  max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate a completion from the AI model."""
        pass

    @abstractmethod
    async def generate_streaming(self, prompt: str, system: Optional[str] = None):
        """Generate a streaming completion (yields chunks)."""
        pass


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model

    async def generate_completion(self, prompt: str, system: Optional[str] = None,
                                  max_tokens: int = 1000, temperature: float = 0.7) -> str:
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package not installed. Run: uv add anthropic")

        client = anthropic.Anthropic(api_key=self.api_key)

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }

        if system:
            kwargs["system"] = system

        response = client.messages.create(**kwargs)
        return response.content[0].text

    async def generate_streaming(self, prompt: str, system: Optional[str] = None):
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package not installed. Run: uv add anthropic")

        client = anthropic.Anthropic(api_key=self.api_key)

        kwargs = {
            "model": self.model,
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        }

        if system:
            kwargs["system"] = system

        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model

    async def generate_completion(self, prompt: str, system: Optional[str] = None,
                                  max_tokens: int = 1000, temperature: float = 0.7) -> str:
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("openai package not installed. Run: uv add openai")

        client = AsyncOpenAI(api_key=self.api_key)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content

    async def generate_streaming(self, prompt: str, system: Optional[str] = None):
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("openai package not installed. Run: uv add openai")

        client = AsyncOpenAI(api_key=self.api_key)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        stream = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class OllamaProvider(AIProvider):
    """Ollama local model provider."""

    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    async def generate_completion(self, prompt: str, system: Optional[str] = None,
                                  max_tokens: int = 1000, temperature: float = 0.7) -> str:
        try:
            import httpx
        except ImportError:
            raise ImportError("httpx package not installed. Run: uv add httpx")

        async with httpx.AsyncClient() as client:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }

            if system:
                payload["system"] = system

            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()["response"]

    async def generate_streaming(self, prompt: str, system: Optional[str] = None):
        try:
            import httpx
        except ImportError:
            raise ImportError("httpx package not installed. Run: uv add httpx")

        async with httpx.AsyncClient() as client:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": True
            }

            if system:
                payload["system"] = system

            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60.0
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]


class GeminiProvider(AIProvider):
    """Google Gemini provider."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model

    async def generate_completion(self, prompt: str, system: Optional[str] = None,
                                  max_tokens: int = 1000, temperature: float = 0.7) -> str:
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("google-generativeai package not installed. Run: uv add google-generativeai")

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)

        # Combine system and prompt if system is provided
        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        response = await model.generate_content_async(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )
        )

        return response.text

    async def generate_streaming(self, prompt: str, system: Optional[str] = None):
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("google-generativeai package not installed. Run: uv add google-generativeai")

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)

        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        response = await model.generate_content_async(full_prompt, stream=True)

        async for chunk in response:
            if chunk.text:
                yield chunk.text


def get_ai_provider(config: Optional[Dict[str, Any]] = None) -> AIProvider:
    """
    Factory function to get the configured AI provider.

    Config format:
    {
        "provider": "anthropic|openai|ollama|gemini",
        "api_key": "...",  # Not needed for Ollama
        "model": "...",     # Optional, uses defaults
        "base_url": "..."   # Only for Ollama
    }
    """
    if config is None:
        # Try to load from environment or config file
        config = load_config()

    provider_type = config.get("provider", "anthropic").lower()

    if provider_type == "anthropic":
        api_key = config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key not found in config or ANTHROPIC_API_KEY env var")
        model = config.get("model", "claude-3-5-sonnet-20241022")
        return AnthropicProvider(api_key, model)

    elif provider_type == "openai":
        api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found in config or OPENAI_API_KEY env var")
        model = config.get("model", "gpt-4o")
        return OpenAIProvider(api_key, model)

    elif provider_type == "ollama":
        model = config.get("model", "llama3.1")
        base_url = config.get("base_url", "http://localhost:11434")
        return OllamaProvider(model, base_url)

    elif provider_type == "gemini":
        api_key = config.get("api_key") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key not found in config or GOOGLE_API_KEY env var")
        model = config.get("model", "gemini-1.5-flash")
        return GeminiProvider(api_key, model)

    else:
        raise ValueError(f"Unknown provider: {provider_type}")


def load_config() -> Dict[str, Any]:
    """Load AI configuration from config.json file."""
    config_path = "config.json"

    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f).get("ai", {})

    # Return default config
    return {
        "provider": "anthropic",
        "model": "claude-3-5-sonnet-20241022"
    }


def save_config(config: Dict[str, Any]):
    """Save AI configuration to config.json file."""
    config_path = "config.json"

    existing_config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            existing_config = json.load(f)

    existing_config["ai"] = config

    with open(config_path, 'w') as f:
        json.dump(existing_config, f, indent=2)
