from enum import Enum
from typing import Dict, Set, Any
from abc import ABC, abstractmethod
from ..features.plugin_permissions import PluginPermission

class PluginState(Enum):
    """插件状态枚举"""
    UNLOADED = "unloaded"    # 未加载
    LOADED = "loaded"        # 已加载
    ACTIVE = "active"        # 已激活
    INACTIVE = "inactive"    # 已停用
    ERROR = "error"          # 错误状态
    RUNNING = "running"      # 运行中

class PluginLifecycle(ABC):
    """插件生命周期接口"""
    
    @abstractmethod
    def initialize(self) -> None:
        """初始化插件"""
        pass
        
    @abstractmethod
    def activate(self, granted_permissions: Set[PluginPermission]) -> None:
        """激活插件"""
        pass
        
    @abstractmethod
    def deactivate(self) -> None:
        """停用插件"""
        pass
        
    @abstractmethod
    def cleanup(self) -> None:
        """清理插件"""
        pass
        
    @abstractmethod
    def start(self) -> None:
        """启动插件"""
        pass
        
    @abstractmethod
    def stop(self) -> None:
        """停止插件"""
        pass
        
    @abstractmethod
    def is_running(self) -> bool:
        """检查是否运行中"""
        pass
        
    @abstractmethod
    def save_state(self) -> dict:
        """保存状态"""
        pass
        
    @abstractmethod
    def restore_state(self, state: dict) -> None:
        """恢复状态"""
        pass 