from abc import ABC, abstractmethod
from typing import Dict, Set, Any, Optional, List
from PyQt6.QtWidgets import QTableView
from ..features.plugin_permissions import PluginPermission
from ..features.plugin_events import PluginEventInterface
from ..features.plugin_lifecycle import PluginLifecycle

class PluginInterface(PluginEventInterface, PluginLifecycle):
    """插件接口，定义插件必须实现的方法"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        pass
        
    @abstractmethod
    def get_version(self) -> str:
        """获取插件版本"""
        pass
        
    @abstractmethod
    def get_description(self) -> str:
        """获取插件描述"""
        pass
        
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Dict[str, Any]]:
        """获取插件配置模式"""
        pass
        
    @abstractmethod
    def process_data(self, table_view: QTableView, **parameters) -> Any:
        """处理数据"""
        pass
        
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> Optional[str]:
        """验证参数有效性"""
        pass
        
    @abstractmethod
    def get_required_permissions(self) -> Set[PluginPermission]:
        """获取插件所需的必要权限"""
        pass
        
    @abstractmethod
    def get_optional_permissions(self) -> Set[PluginPermission]:
        """获取插件的可选权限"""
        pass
        
    @abstractmethod
    def verify_dependency_signature(self, dependency_name: str, signature: str) -> bool:
        """
        验证依赖包签名
        
        参数：
        - dependency_name: 依赖名称
        - signature: 依赖包签名
        
        返回：
        - bool: 签名是否有效
        """
        pass
        
    @abstractmethod
    def get_trusted_sources(self) -> List[str]:
        """
        获取可信源列表
        
        返回：
        - List[str]: 可信源URL列表
        """
        pass
        
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """获取插件依赖列表
        
        Returns:
            List[str]: 依赖包列表，例如 ["numpy>=1.20.0", "pandas>=1.3.0"]
        """
        pass
