"""Configuration management for the dependency monitoring framework.

This module provides a Config class that handles loading and accessing
configuration settings from both a JSON file and environment variables.
"""

import os
import json
from typing import Dict, Any

class Config:
    """Configuration manager for the dependency monitoring framework.
    
    Attributes:
        config_file (str): Path to the configuration file.
        _config (Dict[str, Any]): Internal dictionary storing configuration values.
    """
    def __init__(self):
        self.config_file = os.getenv('CONFIG_FILE', 'config.json')
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or environment variables"""
        config = {}
        if os.path.exists(self.config_file):
            with open(self.config_file, encoding='utf-8') as file:
                config = json.load(file)
        
        # Override with environment variables
        for key, value in os.environ.items():
            if key.startswith('DEPENDENCY_MONITOR_'):
                config_key = key[len('DEPENDENCY_MONITOR_'):].lower()
                config[config_key] = value

        return config

    def get(self, key: str, default=None) -> Any:
        """Get configuration value by key"""
        keys = key.split('.')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split('.')
        current = self._config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

    def save(self):
        """Save configuration to file"""
        with open(self.config_file, 'w', encoding='utf-8') as file:
            json.dump(self._config, file, indent=2)

settings = Config()
