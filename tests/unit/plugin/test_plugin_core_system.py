"""插件系统核心功能测试"""

import pytest
from unittest.mock import patch, MagicMock
from plugin_manager.core.plugin_system import PluginSystem
from plugin_manager.core.plugin_interface import PluginInterface
from plugin_manager.features.plugin_permissions import PluginPermission
from plugin_manager.utils.plugin_error import PluginError

@pytest.fixture
def plugin_system():
    """创建插件系统实例的fixture"""
    return PluginSystem()

@pytest.fixture
def mock_plugin():
    """创建模拟插件的fixture"""
    plugin = MagicMock(spec=PluginInterface)
    plugin.get_name.return_value = "test_plugin"
    plugin.get_version.return_value = "1.0.0"
    plugin.initialize.return_value = True
    plugin.cleanup.return_value = True
    return plugin

class TestPluginSystemCore:
    """插件系统核心功能测试"""
    
    def test_plugin_loading(self, plugin_system, mock_plugin):
        """测试插件加载"""
        with patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin', 
                  return_value=mock_plugin):
            assert plugin_system.load_plugin('test_plugin')
            assert 'test_plugin' in plugin_system.get_all_plugins()
    
    def test_plugin_activation(self, plugin_system, mock_plugin):
        """测试插件激活"""
        with patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin', 
                  return_value=mock_plugin):
            plugin_system.load_plugin('test_plugin')
            assert plugin_system.activate_plugin('test_plugin')
            assert plugin_system.get_plugin_state('test_plugin') == 'active'
    
    def test_plugin_deactivation(self, plugin_system, mock_plugin):
        """测试插件停用"""
        with patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin', 
                  return_value=mock_plugin):
            plugin_system.load_plugin('test_plugin')
            plugin_system.activate_plugin('test_plugin')
            assert plugin_system.deactivate_plugin('test_plugin')
            assert plugin_system.get_plugin_state('test_plugin') == 'inactive'

class TestPluginSystemOperations:
    """插件系统操作测试"""
    
    def test_plugin_start_stop(self, plugin_system, mock_plugin):
        """测试插件启动和停止"""
        with patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin', 
                  return_value=mock_plugin):
            plugin_system.load_plugin('test_plugin')
            plugin_system.activate_plugin('test_plugin')
            
            assert plugin_system.start_plugin('test_plugin')
            assert plugin_system.is_plugin_running('test_plugin')
            
            assert plugin_system.stop_plugin('test_plugin')
            assert not plugin_system.is_plugin_running('test_plugin')
    
    def test_plugin_reload(self, plugin_system, mock_plugin):
        """测试插件重载"""
        with patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin', 
                  return_value=mock_plugin):
            plugin_system.load_plugin('test_plugin')
            plugin_system.activate_plugin('test_plugin')
            
            assert plugin_system.reload_plugin('test_plugin')
            assert plugin_system.get_plugin_state('test_plugin') == 'loaded'

class TestPluginSystemPermissions:
    """插件系统权限测试"""
    
    def test_permission_management(self, plugin_system, mock_plugin):
        """测试权限管理"""
        with patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin', 
                  return_value=mock_plugin):
            plugin_system.load_plugin('test_plugin')
            
            # 使用正确的权限枚举值
            assert plugin_system.request_permission('test_plugin', PluginPermission.FILE_READ)
            assert PluginPermission.FILE_READ in plugin_system.get_plugin_permissions('test_plugin')
            
            plugin_system.revoke_permission('test_plugin', PluginPermission.FILE_READ)
            assert PluginPermission.FILE_READ not in plugin_system.get_plugin_permissions('test_plugin')
    
    @pytest.mark.parametrize("permission", [
        PluginPermission.FILE_READ,
        PluginPermission.DATA_READ,
        PluginPermission.UI_MODIFY
    ])
    def test_permission_validation(self, plugin_system, mock_plugin, permission):
        """测试权限验证"""
        with patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin', 
                  return_value=mock_plugin):
            plugin_system.load_plugin('test_plugin')
            plugin_system.request_permission('test_plugin', permission)
            
            assert plugin_system.has_permission('test_plugin', permission)

class TestPluginSystemErrorHandling:
    """插件系统错误处理测试"""
    
    def test_invalid_plugin_operations(self, plugin_system):
        """测试无效插件操作"""
        with pytest.raises(PluginError):
            plugin_system.activate_plugin('nonexistent_plugin')
    
    def test_plugin_error_recovery(self, plugin_system, mock_plugin):
        """测试错误恢复"""
        with patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin', 
                  return_value=mock_plugin):
            plugin_system.load_plugin('test_plugin')
            
            # 模拟插件错误
            mock_plugin.activate = MagicMock(side_effect=Exception("Activation error"))
            
            with pytest.raises(PluginError):
                plugin_system.activate_plugin('test_plugin')
            
            assert plugin_system.get_plugin_state('test_plugin') == 'error'
            
            # 测试恢复
            assert plugin_system.reset_plugin('test_plugin')
            assert plugin_system.get_plugin_state('test_plugin') == 'loaded'

@pytest.mark.integration
class TestPluginSystemIntegration:
    """插件系统集成测试"""
    
    def test_plugin_lifecycle(self, plugin_system, mock_plugin):
        """测试完整的插件生命周期"""
        with patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin', 
                  return_value=mock_plugin):
            # 加载
            plugin_system.load_plugin('test_plugin')
            assert 'test_plugin' in plugin_system.get_all_plugins()
            
            # 激活
            plugin_system.activate_plugin('test_plugin')
            assert plugin_system.is_plugin_active('test_plugin')
            
            # 启动
            plugin_system.start_plugin('test_plugin')
            assert plugin_system.is_plugin_running('test_plugin')
            
            # 处理数据
            test_data = {"test": "data"}
            result = plugin_system.process_data('test_plugin', test_data)
            assert result == test_data
            
            # 停止
            plugin_system.stop_plugin('test_plugin')
            assert not plugin_system.is_plugin_running('test_plugin')
            
            # 停用
            plugin_system.deactivate_plugin('test_plugin')
            assert not plugin_system.is_plugin_active('test_plugin')
            
            # 卸载
            plugin_system.unload_plugin('test_plugin')
            assert 'test_plugin' not in plugin_system.get_all_plugins() 