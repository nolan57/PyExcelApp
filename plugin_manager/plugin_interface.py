# plugins/plugin_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Set
from enum import Enum
from .plugin_permissions import PluginPermission
from PyQt6.QtWidgets import QTableView


class PluginState(Enum):
    """插件状态枚举"""
    UNLOADED = "unloaded"
    LOADED = "loaded"
    ACTIVE = "active"
    ERROR = "error"

class PluginInterface(ABC):
    """插件接口基类"""
    
    @abstractmethod
    def get_name(self) -> str:
        """
        获取插件名称
        
        Returns:
            str: 插件名称
        """
        pass
        
    @abstractmethod
    def get_version(self) -> str:
        """
        获取插件版本
        
        Returns:
            str: 插件版本号
        """
        pass
        
    @abstractmethod
    def get_description(self) -> str:
        """
        获取插件描述
        
        Returns:
            str: 插件描述信息
        """
        pass
        
    @abstractmethod
    def get_configuration(self) -> Dict[str, Any]:
        """
        获取插件配置
        
        Returns:
            Dict[str, Any]: 插件配置字典
        """
        pass
        
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> Optional[str]:
        """
        验证参数有效性
        
        Args:
            parameters: 参数字典
            
        Returns:
            Optional[str]: 错误信息，���果验证通过则返回None
        """
        pass
        
    @abstractmethod
    def process_data(self, table_view: Optional[QTableView] = None, **parameters) -> Any:
        """
        处理数据
        
        Args:
            table_view: 表格视图实例，如果为None则使用当前活动表格
            parameters: 处理参数
            
        Returns:
            Any: 处理结果
        """
        pass
        
    @abstractmethod
    def activate(self) -> None:
        """
        激活插件
        """
        pass
        
    @abstractmethod
    def deactivate(self) -> None:
        """
        停用插件
        """
        pass
        
    @abstractmethod
    def on_config_changed(self, key: str, value: Any) -> None:
        """
        配置变更回调
        
        Args:
            key: 配置项键名
            value: 新的配置值
        """
        pass
        
    @abstractmethod
    def get_required_permissions(self) -> Set[PluginPermission]:
        """
        获取插件所需的所有权限
        
        Returns:
            Set[PluginPermission]: 权限集合
        """
        pass
        
    @abstractmethod
    def get_optional_permissions(self) -> Set[PluginPermission]:
        """
        获取插件的可选权限（增强功能所需）
        
        Returns:
            Set[PluginPermission]: 可选权限集合
        """
        pass
        
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """
        获取插件依赖列表
        
        Returns:
            List[str]: 依赖的其他插件名称列表
        """
        pass
        
    @abstractmethod
    def check_permission(self, permission: PluginPermission) -> bool:
        """检查是否拥有某个权限"""
        pass
        
    @abstractmethod
    def request_permission(self, permission: PluginPermission) -> bool:
        """请求某个权限"""

    def cleanup(self) -> None:
        """
        清理资源（可选实现）
        """
        pass
        
    def on_error(self, error: Exception) -> None:
        """
        错误处理回调（可选实现）
        
        Args:
            error: 异常对象
        """
        pass
        
    def get_state(self) -> PluginState:
        """
        获取插件状态（可选实现）
        
        Returns:
            PluginState: 插件当前状态
        """
        return PluginState.LOADED

    @abstractmethod
    def get_required_parameters(self) -> Dict[str, Dict[str, Any]]:
        """
        获取插件处理数据所需的参数配置
        
        Returns:
            Dict[str, Dict[str, Any]]: 参数字典，key为参数名，value为参数配置
        """
        pass

    @abstractmethod
    def is_active(self) -> bool:
        """
        检查插件是否处于激活状态
        
        Returns:
            bool: 插件是否激活
        """
        pass
