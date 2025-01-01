from typing import Dict, Any
from dataclasses import dataclass
import json
import os

@dataclass
class PluginDocumentation:
    """插件文档数据类"""
    name: str
    version: str
    description: str
    author: str
    permissions: Dict[str, str]
    config_schema: Dict[str, Any]
    usage: str
    examples: Dict[str, str] 