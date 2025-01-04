"""插件系统渐进式集成测试"""
import pytest
from plugin_manager.core.plugin_system import PluginSystem
from plugin_manager.core.plugin_interface import PluginInterface
from plugin_manager.features.plugin_permissions import PluginPermission

@pytest.mark.integration
class TestPluginSystemIntegrationLevel1:
    """第一级集成测试：核心功能"""
    
    def test_basic_plugin_operations(self, plugin_system, mock_plugin):
        """测试基本插件操作"""
        # 加载和初始化
        plugin_system.load_plugin('test_plugin')
        assert 'test_plugin' in plugin_system.get_all_plugins()
        
        # 激活
        plugin_system.activate_plugin('test_plugin')
        assert plugin_system.is_plugin_active('test_plugin')

class TestPluginSystemIntegrationLevel2:
    """第二级集成测试：权限和配置"""
    
    def test_plugin_with_permissions(self, plugin_system, mock_plugin):
        """测试带权限的插件操作"""
        # 基本设置
        plugin_system.load_plugin('test_plugin')
        plugin_system.activate_plugin('test_plugin')
        
        # 权限管理
        plugin_system.request_permission('test_plugin', PluginPermission.READ)
        assert plugin_system.has_permission('test_plugin', PluginPermission.READ)
        
        # 配置管理
        plugin_system.set_plugin_config('test_plugin', {'key': 'value'})
        assert plugin_system.get_plugin_config('test_plugin') == {'key': 'value'}

class TestPluginSystemIntegrationLevel3:
    """第三级集成测试：依赖管理"""
    
    def test_plugin_with_dependencies(self, plugin_system, mock_plugin):
        """测试带依赖的插件操作"""
        # 设置依赖
        dependencies = {
            'required_package': '>=1.0.0',
            'optional_package': '>=2.0.0'
        }
        plugin_system.dependency_manager.add_dependencies('test_plugin', dependencies)
        
        # 加载和验证
        plugin_system.load_plugin('test_plugin')
        deps = plugin_system.dependency_manager.get_dependencies('test_plugin')
        assert len(deps) == len(dependencies) 