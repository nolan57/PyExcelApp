from typing import Set, Optional, Any
from PyQt6.QtWidgets import QMessageBox,QTableView
from utils.error_handler import ErrorHandler
from plugin_manager.plugin_interface import PluginInterface, PluginPermission
from globals import GlobalState
from abc import ABC, abstractmethod

class PluginBase(PluginInterface):
    """插件基类，提供通用实现"""
    
    def __init__(self):
        super().__init__()
        self._table_view = None
        self._required_permissions = set()
        self._optional_permissions = set()
        self.plugin_system = None  # 将由 PluginSystem 在加载时设置
        self._active = False  # 添加激活状态标志
        
    def check_permission(self, permission: PluginPermission) -> bool:
        """检查是否拥有某个权限"""
        if not self.plugin_system:
            return False
        return self.plugin_system.permission_manager.has_permission(
            self.get_name(), 
            permission
        )
        
    def request_permission(self, permission: PluginPermission) -> bool:
        """请求某个权限"""
        if not self.plugin_system:
            return False
            
        try:
            # 检查是否已有权限
            if self.check_permission(permission):
                return True
                
            # 检查是否是有效的权限
            if permission not in self.get_required_permissions() and \
               permission not in self.get_optional_permissions():
                return False
                
            # 使用插件系统的权限请求方法，避免重复显示对话框
            return self.plugin_system.request_plugin_permissions(
                self.get_name(),
                {permission}
            )
            
        except Exception as e:
            ErrorHandler.handle_error(e, None, "请求权限时发生错误")
            return False 
        
    def get_table_view(self) -> Optional[QTableView]:
        """获取表格视图，优先使用设置的视图，否则使用全局当前视图"""
        if self._table_view:
            return self._table_view
        
        # 从全局状态获取当前表格视图
        state = GlobalState()
        if state.workbook.tab_widget:
            return state.workbook.tab_widget.currentWidget()
        return None
        
    def set_table_view(self, table_view: QTableView):
        """设置表格视图"""
        self._table_view = table_view
        
    def process_data(self, table_view: Optional[QTableView] = None, **parameters) -> Any:
        """处理数据的基础实现"""
        # 优先使用传入的表格视图，其次使用已设置的视图，最后使用全局当前视图
        view = table_view or self.get_table_view()
        if not view:
            raise ValueError("No table view available")
        return self._process_data(view, **parameters)
        
    @abstractmethod
    def _process_data(self, table_view: QTableView, **parameters) -> Any:
        """具体的数据处理实现"""
        pass 
        
    def is_active(self) -> bool:
        """检查插件是否处于激活状态"""
        return self._active
