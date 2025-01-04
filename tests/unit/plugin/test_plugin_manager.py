import pytest
from plugin_manager.core.plugin_manager import PluginManager
from plugin_manager.core.plugin_interface import PluginInterface
from plugin_manager.features.plugin_permissions import PluginPermission
from plugin_manager.utils.plugin_error import PluginError
from unittest.mock import MagicMock, patch

@pytest.fixture
def plugin_manager():
    """创建插件管理器实例的fixture"""
    return PluginManager()

@pytest.fixture
def mock_plugin_class():
    """创建模拟插件类的fixture"""
    class TestPlugin(PluginInterface):
        def __init__(self):
            self.activated = False
            self.config = {}
        
        def activate(self):
            self.activated = True
            return True
            
        def deactivate(self):
            self.activated = False
            return True
            
        def process_data(self, data, **kwargs):
            return data
            
        def get_metadata(self):
            return {
                "name": "Test Plugin",
                "version": "1.0.0",
                "author": "Test Author"
            }
    
    return TestPlugin

class TestPluginManagerBasic:
    """基本插件管理功能测试"""
    
    def test_plugin_registration(self, plugin_manager, mock_plugin_class):
        """测试插件注册"""
        plugin_manager.register_plugin("test_plugin", mock_plugin_class)
        assert "test_plugin" in plugin_manager.get_registered_plugins()
        
    def test_plugin_initialization(self, plugin_manager, mock_plugin_class):
        """测试插件初始化"""
        plugin_manager.register_plugin("test_plugin", mock_plugin_class)
        plugin = plugin_manager.initialize_plugin("test_plugin")
        assert isinstance(plugin, mock_plugin_class)
        
    def test_plugin_activation(self, plugin_manager, mock_plugin_class):
        """测试插件激活"""
        plugin_manager.register_plugin("test_plugin", mock_plugin_class)
        plugin_manager.initialize_plugin("test_plugin")
        assert plugin_manager.activate_plugin("test_plugin")
        assert plugin_manager.is_plugin_active("test_plugin")
        
    def test_plugin_deactivation(self, plugin_manager, mock_plugin_class):
        """测试插件停用"""
        plugin_manager.register_plugin("test_plugin", mock_plugin_class)
        plugin_manager.initialize_plugin("test_plugin")
        plugin_manager.activate_plugin("test_plugin")
        assert plugin_manager.deactivate_plugin("test_plugin")
        assert not plugin_manager.is_plugin_active("test_plugin")

class TestPluginManagerAdvanced:
    """高级插件管理功能测试"""
    
    def test_plugin_configuration(self, plugin_manager, mock_plugin_class):
        """测试插件配置管理"""
        plugin_manager.register_plugin("test_plugin", mock_plugin_class)
        plugin_manager.initialize_plugin("test_plugin")
        
        config = {"setting1": "value1", "setting2": "value2"}
        plugin_manager.configure_plugin("test_plugin", config)
        
        assert plugin_manager.get_plugin_config("test_plugin") == config
        
    def test_plugin_metadata(self, plugin_manager, mock_plugin_class):
        """测试插件元数据获取"""
        plugin_manager.register_plugin("test_plugin", mock_plugin_class)
        plugin = plugin_manager.initialize_plugin("test_plugin")
        
        metadata = plugin_manager.get_plugin_metadata("test_plugin")
        assert metadata["name"] == "Test Plugin"
        assert metadata["version"] == "1.0.0"
        
    @pytest.mark.parametrize("invalid_id", [
        "",
        None,
        "nonexistent_plugin"
    ])
    def test_invalid_plugin_operations(self, plugin_manager, invalid_id):
        """测试无效插件操作"""
        with pytest.raises(PluginError):
            plugin_manager.activate_plugin(invalid_id)
            
    def test_plugin_dependencies(self, plugin_manager, mock_plugin_class):
        """测试插件依赖管理"""
        plugin_manager.register_plugin("test_plugin", mock_plugin_class)
        
        dependencies = {
            "required_package": ">=1.0.0",
            "optional_package": ">=2.0.0"
        }
        
        plugin_manager.set_plugin_dependencies("test_plugin", dependencies)
        assert plugin_manager.get_plugin_dependencies("test_plugin") == dependencies
        
    def test_plugin_error_handling(self, plugin_manager, mock_plugin_class):
        """测试插件错误处理"""
        # 模拟插件激活失败
        mock_plugin_class.activate = MagicMock(side_effect=Exception("Activation failed"))
        
        plugin_manager.register_plugin("test_plugin", mock_plugin_class)
        plugin_manager.initialize_plugin("test_plugin")
        
        with pytest.raises(PluginError):
            plugin_manager.activate_plugin("test_plugin")
            
    @pytest.mark.asyncio
    async def test_async_plugin_operations(self, plugin_manager, mock_plugin_class):
        """测试异步插件操作"""
        plugin_manager.register_plugin("test_plugin", mock_plugin_class)
        
        # 异步初始化
        plugin = await plugin_manager.initialize_plugin_async("test_plugin")
        assert isinstance(plugin, mock_plugin_class)
        
        # 异步激活
        success = await plugin_manager.activate_plugin_async("test_plugin")
        assert success
        
    def test_plugin_hot_reload(self, plugin_manager, mock_plugin_class):
        """测试插件热重载"""
        plugin_manager.register_plugin("test_plugin", mock_plugin_class)
        plugin_manager.initialize_plugin("test_plugin")
        plugin_manager.activate_plugin("test_plugin")
        
        assert plugin_manager.reload_plugin("test_plugin")
        assert plugin_manager.is_plugin_active("test_plugin")
        
    def test_plugin_resource_cleanup(self, plugin_manager, mock_plugin_class):
        """测试插件资源清理"""
        plugin_manager.register_plugin("test_plugin", mock_plugin_class)
        plugin_manager.initialize_plugin("test_plugin")
        plugin_manager.activate_plugin("test_plugin")
        
        # 模拟资源清理
        cleanup_called = False
        def cleanup():
            nonlocal cleanup_called
            cleanup_called = True
            
        plugin_manager.register_cleanup_handler("test_plugin", cleanup)
        plugin_manager.cleanup_plugin("test_plugin")
        
        assert cleanup_called
        assert not plugin_manager.is_plugin_active("test_plugin") 