#!/usr/bin/env python3
"""
LLM Provider Implementations for Agent-Forge
Multi-provider LLM support with unified interface (Issue #31)
"""

import logging
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
import requests
import json

logger = logging.getLogger(__name__)


@dataclass
class LLMMessage:
    """Standard message format for LLM interactions"""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """Standard response format from LLM"""
    content: str
    model: str
    provider: str
    finish_reason: str
    usage: Dict[str, int]  # {"prompt_tokens": X, "completion_tokens": Y, "total_tokens": Z}
    raw_response: Optional[Dict] = None


class LLMProvider(ABC):
    """
    Base class for LLM providers.
    
    All providers must implement:
    - chat_completion(): Generate text completion
    - test_connection(): Test API key validity
    - get_available_models(): List available models
    """
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
        self.provider_name = self.__class__.__name__.replace("Provider", "").lower()
    
    @abstractmethod
    def chat_completion(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate chat completion"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if API key is valid"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider (GPT-4, GPT-4 Turbo, GPT-3.5)"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, org_id: Optional[str] = None):
        super().__init__(api_key, base_url or "https://api.openai.com/v1")
        self.org_id = org_id
    
    def chat_completion(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate OpenAI chat completion"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            if self.org_id:
                headers["OpenAI-Organization"] = self.org_id
            
            payload = {
                "model": model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            choice = data["choices"][0]
            
            return LLMResponse(
                content=choice["message"]["content"],
                model=data["model"],
                provider="openai",
                finish_reason=choice["finish_reason"],
                usage=data["usage"],
                raw_response=data
            )
        
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test OpenAI API key"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=10
            )
            
            return response.status_code == 200
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get available OpenAI models"""
        return [
            "gpt-4-turbo-preview",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-4-32k",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider (Claude 3.5 Sonnet, Claude 3 Opus/Haiku)"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        super().__init__(api_key, base_url or "https://api.anthropic.com")
    
    def chat_completion(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate Anthropic chat completion"""
        try:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            
            # Anthropic uses different format - extract system message
            system_message = ""
            user_messages = []
            
            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    user_messages.append({"role": msg.role, "content": msg.content})
            
            payload = {
                "model": model,
                "messages": user_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs
            }
            
            if system_message:
                payload["system"] = system_message
            
            response = requests.post(
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            
            return LLMResponse(
                content=data["content"][0]["text"],
                model=data["model"],
                provider="anthropic",
                finish_reason=data["stop_reason"],
                usage={
                    "prompt_tokens": data["usage"]["input_tokens"],
                    "completion_tokens": data["usage"]["output_tokens"],
                    "total_tokens": data["usage"]["input_tokens"] + data["usage"]["output_tokens"]
                },
                raw_response=data
            )
        
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test Anthropic API key"""
        try:
            # Simple test with minimal tokens
            test_messages = [LLMMessage(role="user", content="Hi")]
            self.chat_completion(test_messages, "claude-3-haiku-20240307", max_tokens=10)
            return True
        except Exception as e:
            logger.error(f"Anthropic connection test failed: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get available Anthropic models"""
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]


class GoogleProvider(LLMProvider):
    """Google Gemini provider"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        super().__init__(api_key, base_url or "https://generativelanguage.googleapis.com/v1")
    
    def chat_completion(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate Google Gemini completion"""
        try:
            # Gemini format
            contents = []
            for msg in messages:
                role = "user" if msg.role in ["user", "system"] else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.content}]
                })
            
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                }
            }
            
            response = requests.post(
                f"{self.base_url}/models/{model}:generateContent?key={self.api_key}",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            candidate = data["candidates"][0]
            
            return LLMResponse(
                content=candidate["content"]["parts"][0]["text"],
                model=model,
                provider="google",
                finish_reason=candidate.get("finishReason", "STOP"),
                usage={
                    "prompt_tokens": data.get("usageMetadata", {}).get("promptTokenCount", 0),
                    "completion_tokens": data.get("usageMetadata", {}).get("candidatesTokenCount", 0),
                    "total_tokens": data.get("usageMetadata", {}).get("totalTokenCount", 0)
                },
                raw_response=data
            )
        
        except Exception as e:
            logger.error(f"Google API error: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test Google API key"""
        try:
            response = requests.get(
                f"{self.base_url}/models?key={self.api_key}",
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Google connection test failed: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get available Google models"""
        return [
            "gemini-pro",
            "gemini-pro-vision",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ]


class LocalProvider(LLMProvider):
    """Local LLM provider (Ollama, LM Studio, etc.)"""
    
    def __init__(self, api_key: str = "", base_url: str = "http://localhost:11434"):
        super().__init__(api_key, base_url)
    
    def chat_completion(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate local LLM completion (Ollama format)"""
        try:
            payload = {
                "model": model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            data = response.json()
            
            return LLMResponse(
                content=data["message"]["content"],
                model=data["model"],
                provider="local",
                finish_reason=data.get("done_reason", "stop"),
                usage={
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                },
                raw_response=data
            )
        
        except Exception as e:
            logger.error(f"Local LLM error: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test local LLM connection"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Local LLM connection test failed: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get available local models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except:
            pass
        
        return ["llama3", "mistral", "codellama", "qwen2.5-coder"]


# Provider registry
PROVIDERS = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "google": GoogleProvider,
    "local": LocalProvider
}


def get_provider(
    provider_name: str,
    api_key: str,
    base_url: Optional[str] = None,
    **kwargs
) -> Optional[LLMProvider]:
    """
    Get LLM provider instance.
    
    Args:
        provider_name: Provider name ("openai", "anthropic", "google", "local")
        api_key: API key for provider
        base_url: Optional custom base URL
        **kwargs: Additional provider-specific arguments
    
    Returns:
        LLMProvider instance or None if provider not found
    """
    provider_class = PROVIDERS.get(provider_name.lower())
    
    if not provider_class:
        logger.error(f"Unknown provider: {provider_name}")
        return None
    
    try:
        if base_url:
            return provider_class(api_key, base_url, **kwargs)
        else:
            return provider_class(api_key, **kwargs)
    except Exception as e:
        logger.error(f"Failed to create provider {provider_name}: {e}")
        return None


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🤖 LLM Provider Test\n")
    
    # Test local provider (no API key needed)
    print("Testing local provider (Ollama)...")
    local = LocalProvider(base_url="http://localhost:11434")
    
    if local.test_connection():
        print("✅ Local LLM connected")
        models = local.get_available_models()
        print(f"📋 Available models: {', '.join(models[:3])}...")
    else:
        print("❌ Local LLM not available")
    
    print("\n📚 Registered providers:")
    for name in PROVIDERS.keys():
        print(f"  - {name}")
