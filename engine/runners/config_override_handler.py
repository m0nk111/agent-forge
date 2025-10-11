"""Configuration override handler for polling service.

Handles merging of YAML configuration with programmatic overrides,
ensuring that only explicitly set values override YAML defaults.
"""

import os
from dataclasses import fields, MISSING
from typing import Any, Dict

from engine.runners.polling_models import PollingConfig


class ConfigOverrideHandler:
    """Handles configuration override logic with smart default detection."""
    
    def __init__(self, base_config: PollingConfig):
        """Initialize handler with base configuration.
        
        Args:
            base_config: The base configuration to apply overrides to
        """
        self.config = base_config
        self._defaults = self._build_defaults_map()
    
    def _build_defaults_map(self) -> Dict[str, Any]:
        """Build a map of default values from the dataclass definition.
        
        Returns:
            Dictionary mapping field names to their default values
        """
        defaults = {}
        for f in fields(PollingConfig):
            if f.default is not MISSING:
                defaults[f.name] = f.default
            elif f.default_factory is not MISSING:  # type: ignore[attr-defined]
                defaults[f.name] = f.default_factory()  # type: ignore[misc]
            else:
                defaults[f.name] = None
        return defaults
    
    def _is_default_value(self, field_name: str, value: Any) -> bool:
        """Check if a value equals the dataclass default.
        
        Args:
            field_name: Name of the field
            value: Value to check
            
        Returns:
            True if value equals the default
        """
        if value is None:
            return True
        
        default_value = self._defaults.get(field_name)
        return value == default_value
    
    def _is_github_token_from_env(self, token: str) -> bool:
        """Check if a GitHub token likely comes from environment variables.
        
        Args:
            token: Token value to check
            
        Returns:
            True if token matches environment variable values
        """
        env_token = os.getenv('BOT_GITHUB_TOKEN') or os.getenv('GITHUB_TOKEN')
        return token == env_token
    
    def _should_skip_override(self, field_name: str, value: Any) -> bool:
        """Determine if an override should be skipped.
        
        Args:
            field_name: Name of the field
            value: Override value
            
        Returns:
            True if override should be skipped
        """
        # Skip if value is default
        if self._is_default_value(field_name, value):
            return True
        
        # Special case: avoid overriding YAML token with env-provided token
        if field_name == 'github_token' and self._is_github_token_from_env(value):
            return True
        
        return False
    
    def apply_overrides(self, override: PollingConfig) -> None:
        """Apply configuration overrides from another PollingConfig instance.
        
        Only applies overrides for fields whose value differs from the dataclass default.
        This prevents accidental replacement of YAML values with implicit defaults.
        
        Args:
            override: Configuration object containing override values
        """
        for field_name in self._defaults.keys():
            value = getattr(override, field_name, None)
            
            if self._should_skip_override(field_name, value):
                continue
            
            # Apply the override
            setattr(self.config, field_name, value)
