"""插件管理器测试模块"""
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication, QListView, QDialog
from PyQt6.QtCore import Qt
from plugin_manager import (
    PluginInterface, 
    PluginBase,
    PluginSystem,
    PluginPermission,
    PluginManagerWindow
)
from plugin_manager.utils.plugin_error import PluginError

# 确保有 QApplication 实例
app = QApplication.instance() or QApplication([])

@pytest.fixture
def plugin_system():
    """创建插件系统实例"""
    return PluginSystem()

@pytest.fixture
def plugin_manager_window(plugin_system):
    """创建插件管理器窗口实例"""
    return PluginManagerWindow(plugin_system)

@pytest.fixture
def mock_plugin():
    """创建模拟插件"""
    class TestPlugin(PluginBase):
        def __init__(self):
            super().__init__()
            self.initialized = False
            
        def initialize(self):
            self.initialized = True
            
        def cleanup(self):
            self.initialized = False
            
        def get_name(self) -> str:
            return "Test Plugin"
            
        def get_version(self) -> str:
            return "1.0.0"
            
        def get_description(self) -> str:
            return "Test Description"
            
        def get_author(self) -> str:
            return "Test Author"
            
        def get_permissions(self) -> set:
            return {PluginPermission.FILE_READ}
            
    return TestPlugin()

class TestPluginManagerWindow:
    """插件管理器窗口测试"""
    
    def test_window_initialization(self, plugin_manager_window):
        """测试窗口初始化"""
        assert isinstance(plugin_manager_window.plugin_listview, QListView)
        assert plugin_manager_window.windowTitle() == "插件管理器"
        
    def test_plugin_list_display(self, plugin_manager_window, mock_plugin):
        """测试插件列表显示"""
        plugin_manager_window.plugin_system.register_plugin("test", mock_plugin)
        model = plugin_manager_window.plugin_listview.model()
        assert model.rowCount() > 0
        
    def test_plugin_operations(self, plugin_manager_window, mock_plugin):
        """测试插件操作"""
        plugin_manager_window.plugin_system.register_plugin("test", mock_plugin)
        
        # 启用插件
        with patch.object(mock_plugin, 'initialize') as mock_init:
            plugin_manager_window.enable_selected_plugin()
            mock_init.assert_called_once()
            
        # 禁用插件
        with patch.object(mock_plugin, 'cleanup') as mock_cleanup:
            plugin_manager_window.disable_selected_plugin()
            mock_cleanup.assert_called_once()
            
    def test_plugin_settings(self, plugin_manager_window, mock_plugin):
        """测试插件设置"""
        plugin_manager_window.plugin_system.register_plugin("test", mock_plugin)
        
        # 模拟设置对话框
        with patch('PyQt6.QtWidgets.QDialog.exec') as mock_exec:
            mock_exec.return_value = QDialog.DialogCode.Accepted
            plugin_manager_window.show_plugin_settings_dialog()
            mock_exec.assert_called_once()
            
    def test_error_handling(self, plugin_manager_window):
        """测试错误处理"""
        # 测试无效插件操作
        with pytest.raises(PluginError):
            plugin_manager_window.enable_selected_plugin()
            
        with pytest.raises(PluginError):
            plugin_manager_window.load_plugin_from_file("nonexistent.py")
            
    def test_plugin_info_display(self, plugin_manager_window, mock_plugin):
        """测试插件信息显示"""
        plugin_manager_window.plugin_system.register_plugin("test", mock_plugin)
        
        # 显示插件信息
        with patch('PyQt6.QtWidgets.QMessageBox.information') as mock_info:
            plugin_manager_window.show_plugin_info_dialog()
            mock_info.assert_called_once() 