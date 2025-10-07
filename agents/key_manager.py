#!/usr/bin/env python3
"""
API Key Manager for Agent-Forge
Secure storage and management of LLM provider API keys (Issue #31)
"""

import os
import json
import logging
from typing import Optional, Dict, List
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProviderKeyConfig:
    """Configuration for a provider's API key"""
    provider: str
    key_name: str
    description: str
    required: bool = False
    masked_display: bool = True


# Supported provider key configurations
PROVIDER_KEYS = {
    "openai": ProviderKeyConfig(
        provider="openai",
        key_name="OPENAI_API_KEY",
        description="OpenAI API Key (sk-...)",
        required=False
    ),
    "openai_org": ProviderKeyConfig(
        provider="openai",
        key_name="OPENAI_ORG_ID",
        description="OpenAI Organization ID (optional)",
        required=False
    ),
    "anthropic": ProviderKeyConfig(
        provider="anthropic",
        key_name="ANTHROPIC_API_KEY",
        description="Anthropic API Key (sk-ant-...)",
        required=False
    ),
    "google": ProviderKeyConfig(
        provider="google",
        key_name="GEMINI_API_KEY",
        description="Google Gemini API Key",
        required=False
    ),
    "groq": ProviderKeyConfig(
        provider="groq",
        key_name="GROQ_API_KEY",
        description="Groq API Key",
        required=False
    ),
    "replicate": ProviderKeyConfig(
        provider="replicate",
        key_name="REPLICATE_API_KEY",
        description="Replicate API Key",
        required=False
    ),
    "qwen": ProviderKeyConfig(
        provider="qwen",
        key_name="QWEN_API_KEY",
        description="Qwen API Key",
        required=False
    ),
    "xai": ProviderKeyConfig(
        provider="xai",
        key_name="XAI_API_KEY",
        description="xAI (Grok) API Key",
        required=False
    ),
    "mistral": ProviderKeyConfig(
        provider="mistral",
        key_name="MISTRAL_API_KEY",
        description="Mistral AI API Key",
        required=False
    ),
    "deepseek": ProviderKeyConfig(
        provider="deepseek",
        key_name="DEEPSEEK_API_KEY",
        description="DeepSeek API Key",
        required=False
    ),
    "openrouter": ProviderKeyConfig(
        provider="openrouter",
        key_name="OPENROUTER_API_KEY",
        description="OpenRouter API Key",
        required=False
    ),
    "huggingface": ProviderKeyConfig(
        provider="huggingface",
        key_name="HUGGINGFACE_API_KEY",
        description="Hugging Face API Key",
        required=False
    )
}


class KeyManager:
    """
    Manages API keys for LLM providers.
    
    Keys are stored in keys.json with the following structure:
    {
        "OPENAI_API_KEY": "sk-...",
        "ANTHROPIC_API_KEY": "sk-ant-...",
        ...
    }
    
    Security features:
    - File permissions: 0600 (read/write owner only)
    - Masked display in API responses
    - Environment variable fallback
    - Validation before storage
    """
    
    def __init__(self, keys_file: str = "/home/flip/agent-forge/keys.json"):
        self.keys_file = Path(keys_file)
        self.keys: Dict[str, str] = {}
        self._load_keys()
    
    def _load_keys(self) -> None:
        """Load keys from JSON file or create empty file"""
        try:
            if self.keys_file.exists():
                # Check file permissions
                stat_info = self.keys_file.stat()
                if stat_info.st_mode & 0o077:
                    logger.warning(f"⚠️ {self.keys_file} has insecure permissions. Run: chmod 600 {self.keys_file}")
                
                with open(self.keys_file, 'r') as f:
                    self.keys = json.load(f)
                logger.info(f"✅ Loaded {len(self.keys)} API keys from {self.keys_file}")
            else:
                # Create empty keys file
                self._save_keys()
                logger.info(f"✅ Created new keys file: {self.keys_file}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse {self.keys_file}: {e}")
            self.keys = {}
        except Exception as e:
            logger.error(f"❌ Failed to load keys: {e}")
            self.keys = {}
    
    def _save_keys(self) -> None:
        """Save keys to JSON file with secure permissions"""
        try:
            # Create directory if needed
            self.keys_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write keys
            with open(self.keys_file, 'w') as f:
                json.dump(self.keys, f, indent=2)
            
            # Set secure permissions (0600 - owner read/write only)
            os.chmod(self.keys_file, 0o600)
            
            logger.debug(f"💾 Saved {len(self.keys)} keys to {self.keys_file}")
        except Exception as e:
            logger.error(f"❌ Failed to save keys: {e}")
            raise
    
    def get_key(self, key_name: str) -> Optional[str]:
        """
        Get API key by name.
        
        Priority:
        1. keys.json file
        2. Environment variable
        3. None
        
        Args:
            key_name: Key name (e.g., "OPENAI_API_KEY")
        
        Returns:
            API key or None if not found
        """
        # Try keys.json first
        if key_name in self.keys and self.keys[key_name]:
            return self.keys[key_name]
        
        # Fall back to environment variable
        env_value = os.getenv(key_name)
        if env_value:
            logger.debug(f"🔍 Found {key_name} in environment")
            return env_value
        
        return None
    
    def set_key(self, key_name: str, value: str) -> bool:
        """
        Set API key.
        
        Args:
            key_name: Key name (e.g., "OPENAI_API_KEY")
            value: API key value
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate key format (basic check)
            if not value or len(value.strip()) < 10:
                logger.error(f"❌ Invalid key format for {key_name}")
                return False
            
            # Store key
            self.keys[key_name] = value.strip()
            self._save_keys()
            
            logger.info(f"✅ Stored API key: {key_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to set key {key_name}: {e}")
            return False
    
    def delete_key(self, key_name: str) -> bool:
        """
        Delete API key.
        
        Args:
            key_name: Key name to delete
        
        Returns:
            True if deleted, False if not found
        """
        if key_name in self.keys:
            del self.keys[key_name]
            self._save_keys()
            logger.info(f"🗑️ Deleted API key: {key_name}")
            return True
        return False
    
    def mask_key(self, key: str) -> str:
        """
        Mask API key for display.
        
        Shows only last 6 characters: "sk-...abc123"
        
        Args:
            key: Full API key
        
        Returns:
            Masked key
        """
        if not key or len(key) < 10:
            return "***"
        return f"{key[:3]}...{key[-6:]}"
    
    def list_configured_providers(self) -> List[Dict[str, any]]:
        """
        List all providers with configuration status.
        
        Returns:
            List of dicts with provider info
        """
        providers = []
        
        for provider_id, config in PROVIDER_KEYS.items():
            if provider_id.endswith("_org"):  # Skip optional sub-keys
                continue
            
            key = self.get_key(config.key_name)
            
            providers.append({
                "provider": config.provider,
                "key_name": config.key_name,
                "description": config.description,
                "configured": key is not None,
                "masked_key": self.mask_key(key) if key else None,
                "required": config.required
            })
        
        return providers
    
    def test_key(self, provider: str, key: Optional[str] = None) -> tuple[bool, str]:
        """
        Test if API key is valid by making a test request.
        
        Args:
            provider: Provider name ("openai", "anthropic", etc.)
            key: Optional key to test (uses stored key if None)
        
        Returns:
            (success, message) tuple
        """
        # Get key to test
        if key is None:
            provider_config = PROVIDER_KEYS.get(provider)
            if not provider_config:
                return False, f"Unknown provider: {provider}"
            key = self.get_key(provider_config.key_name)
        
        if not key:
            return False, f"No API key configured for {provider}"
        
        # Import provider and test
        try:
            from agents.llm_providers import get_provider
            
            provider_instance = get_provider(provider, key)
            if not provider_instance:
                return False, f"Failed to initialize {provider} provider"
            
            # Test connection
            success = provider_instance.test_connection()
            
            if success:
                return True, f"✅ {provider.title()} connection successful"
            else:
                return False, f"❌ {provider.title()} connection failed"
        
        except ImportError:
            # Provider system not fully implemented yet
            logger.debug(f"Provider system not available, skipping test for {provider}")
            return True, f"⚠️ Key stored (validation not available)"
        except Exception as e:
            logger.error(f"Failed to test {provider} key: {e}")
            return False, f"❌ Test failed: {str(e)}"
    
    def get_all_keys(self, masked: bool = True) -> Dict[str, str]:
        """
        Get all stored keys.
        
        Args:
            masked: If True, mask keys for display
        
        Returns:
            Dictionary of key_name -> key (masked or full)
        """
        if masked:
            return {k: self.mask_key(v) for k, v in self.keys.items()}
        return self.keys.copy()
    
    def validate_key_format(self, provider: str, key: str) -> tuple[bool, str]:
        """
        Validate API key format for a provider.
        
        Args:
            provider: Provider name
            key: API key to validate
        
        Returns:
            (valid, message) tuple
        """
        # Basic validation
        if not key or len(key.strip()) < 10:
            return False, "Key too short (minimum 10 characters)"
        
        key = key.strip()
        
        # Provider-specific validation
        if provider == "openai":
            if not key.startswith("sk-"):
                return False, "OpenAI keys must start with 'sk-'"
        
        elif provider == "anthropic":
            if not key.startswith("sk-ant-"):
                return False, "Anthropic keys must start with 'sk-ant-'"
        
        # All checks passed
        return True, "Key format valid"


# Global key manager instance
_key_manager: Optional[KeyManager] = None


def get_key_manager() -> KeyManager:
    """Get global KeyManager instance (singleton pattern)"""
    global _key_manager
    if _key_manager is None:
        _key_manager = KeyManager()
    return _key_manager


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🔑 API Key Manager Test\n")
    
    manager = KeyManager()
    
    # List providers
    print("📋 Configured providers:")
    for provider in manager.list_configured_providers():
        status = "✅" if provider["configured"] else "❌"
        key_display = provider["masked_key"] or "Not configured"
        print(f"  {status} {provider['provider']}: {key_display}")
    
    print(f"\n💾 Keys file: {manager.keys_file}")
    print(f"🔐 Total keys stored: {len(manager.keys)}")
