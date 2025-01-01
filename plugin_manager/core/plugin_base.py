from typing import Dict, Set, Any, Optional, Callable
from PyQt6.QtWidgets import QTableView, QWidget, QMessageBox
from .plugin_interface import PluginInterface
from ..features.plugin_permissions import PluginPermission
from ..features.plugin_events import EventBus
from ..utils.plugin_error import ErrorHandler
from ..features.plugin_lifecycle import PluginState
import logging

class PluginBase(PluginInterface):
    """插件基类，提供基础实现"""
    
    def __init__(self):
        self.table_view: Optional[QTableView] = None  # 表格视图引用
        self._logger = logging.getLogger(self.__class__.__name__)  # 日志记录器
        
        self._state = PluginState.UNLOADED
        self._event_bus = EventBus()
        self._config = {}
        self._required_permissions: Set[PluginPermission] = set()
        self._optional_permissions: Set[PluginPermission] = set()
        self._granted_permissions: Set[PluginPermission] = set()
        self.plugin_system = None  # 由插件系统设置
        
    # PluginInterface 实现
    def get_name(self) -> str:
        raise NotImplementedError("插件必须实现 get_name 方法")
        
    def get_version(self) -> str:
        raise NotImplementedError("插件必须实现 get_version 方法")
        
    def get_description(self) -> str:
        raise NotImplementedError("插件必须实现 get_description 方法")
        
    def get_config_schema(self) -> Dict[str, Dict[str, Any]]:
        return {}
        
    def process_data(self, table_view: QTableView, **parameters) -> Any:
        raise NotImplementedError("插件必须实现 process_data 方法")
        
    def validate_parameters(self, parameters: Dict[str, Any]) -> Optional[str]:
        """验证参数，返回错误信息或 None"""
        return None
        
    def get_required_permissions(self) -> Set[PluginPermission]:
        return self._required_permissions
        
    def get_optional_permissions(self) -> Set[PluginPermission]:
        return self._optional_permissions
        
    # PluginLifecycle 实现
    def initialize(self) -> None:
        self._state = PluginState.LOADED
        
    def activate(self, granted_permissions: Set[PluginPermission]) -> None:
        self._granted_permissions = granted_permissions
        self._state = PluginState.ACTIVE
        
    def deactivate(self) -> None:
        self._state = PluginState.INACTIVE
        
    def cleanup(self) -> None:
        self._state = PluginState.UNLOADED
        
    def start(self) -> None:
        if self._state == PluginState.ACTIVE:
            self._state = PluginState.RUNNING
        
    def stop(self) -> None:
        if self._state == PluginState.RUNNING:
            self._state = PluginState.ACTIVE
        
    def is_running(self) -> bool:
        return self._state == PluginState.RUNNING
        
    def save_state(self) -> dict:
        return {
            'config': self._config,
            'state': self._state.value
        }
        
    def restore_state(self, state: dict) -> None:
        self._config = state.get('config', {})
        state_value = state.get('state')
        if state_value:
            self._state = PluginState(state_value)
            
    # PluginEventInterface 实现
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        self._event_bus.subscribe(event_type, handler)
        
    def unregister_event_handler(self, event_type: str, handler: Callable) -> None:
        self._event_bus.unsubscribe(event_type, handler)
        
    def emit_event(self, event_type: str, data: Any = None) -> None:
        self._event_bus.emit(event_type, data, source=self.get_name())
        
    # 错误处理
    def handle_error(self, error: Exception, parent: Optional[QWidget] = None, message: Optional[str] = None) -> None:
        ErrorHandler.handle_error(error, parent, message)
        
    def handle_warning(self, message: str, parent: Optional[QWidget] = None) -> None:
        ErrorHandler.handle_warning(message, parent)
        
    def handle_info(self, message: str, parent: Optional[QWidget] = None) -> None:
        ErrorHandler.handle_info(message, parent)
        
    def set_table_view(self, table_view: QTableView) -> None:
        """设置表格视图"""
        self.table_view = table_view
        
    def request_permission(self, permission: PluginPermission) -> bool:
        """请求权限"""
        try:
            if permission not in self._required_permissions and permission not in self._optional_permissions:
                return False
                
            message = (
                f"插件 {self.get_name()} 请求 {PluginPermission.get_permission_description(permission)}\n"
                f"是否授予此权限？"
            )
            reply = QMessageBox.question(
                self.table_view,
                "权限请求",
                message,
                buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                defaultButton=QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self._granted_permissions.add(permission)
                return True
            return False
            
        except Exception as e:
            self.handle_error(e, None, "请求权限时发生错误")
            return False
            
    def has_permission(self, permission: PluginPermission) -> bool:
        """检查是否有某个权限"""
        return permission in self._granted_permissions 
        
    def get_configuration(self) -> Dict[str, Any]:
        """获取插件配置"""
        if self.plugin_system:
            return self.plugin_system.config.get_config(self.get_name())
        return {} 