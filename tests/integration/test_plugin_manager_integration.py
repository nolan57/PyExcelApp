import pytest
from plugin_manager.core.plugin_manager import PluginManager
from plugin_manager.core.plugin_interface import PluginInterface
from plugin_manager.features.plugin_permissions import PluginPermission

@pytest.fixture
def complex_plugin():
    """创建复杂插件的fixture"""
    class ComplexPlugin(PluginInterface):
        def __init__(self):
            self.activated = False
            self.config = {}
            self.processed_data = []
            
        def activate(self):
            self.activated = True
            return True
            
        def deactivate(self):
            self.activated = False
            return True
            
        def process_data(self, data, **kwargs):
            self.processed_data.append(data)
            return data
            
        def get_metadata(self):
            return {
                "name": "Complex Plugin",
                "version": "1.0.0",
                "dependencies": {
                    "numpy": ">=1.20.0",
                    "pandas": ">=1.3.0"
                }
            }
    
    return ComplexPlugin

@pytest.mark.integration
class TestPluginManagerIntegration:
    """插件管理器集成测试"""
    
    def test_full_plugin_lifecycle(self, plugin_manager, complex_plugin):
        """测试完整的插件生命周期"""
        # 注册插件
        plugin_manager.register_plugin("complex_plugin", complex_plugin)
        
        # 初始化
        plugin = plugin_manager.initialize_plugin("complex_plugin")
        assert isinstance(plugin, complex_plugin)
        
        # 配置
        config = {"setting": "value"}
        plugin_manager.configure_plugin("complex_plugin", config)
        
        # 激活
        assert plugin_manager.activate_plugin("complex_plugin")
        
        # 处理数据
        test_data = {"test": "data"}
        result = plugin_manager.process_plugin_data("complex_plugin", test_data)
        assert result == test_data
        
        # 停用
        assert plugin_manager.deactivate_plugin("complex_plugin")
        
        # 清理
        plugin_manager.cleanup_plugin("complex_plugin")
        
    def test_plugin_dependency_resolution(self, plugin_manager, complex_plugin):
        """测试插件依赖解析"""
        plugin_manager.register_plugin("complex_plugin", complex_plugin)
        
        # 检查依赖
        deps = plugin_manager.get_plugin_dependencies("complex_plugin")
        assert "numpy" in deps
        assert "pandas" in deps
        
        # 验证依赖版本
        assert deps["numpy"] == ">=1.20.0"
        assert deps["pandas"] == ">=1.3.0"
        
    @pytest.mark.asyncio
    async def test_async_data_processing(self, plugin_manager, complex_plugin):
        """测试异步数据处理"""
        plugin_manager.register_plugin("complex_plugin", complex_plugin)
        await plugin_manager.initialize_plugin_async("complex_plugin")
        await plugin_manager.activate_plugin_async("complex_plugin")
        
        test_data = [{"id": i} for i in range(5)]
        results = await plugin_manager.process_plugin_data_async("complex_plugin", test_data)
        
        assert len(results) == len(test_data)
        
    def test_plugin_error_recovery(self, plugin_manager, complex_plugin):
        """测试插件错误恢复"""
        plugin_manager.register_plugin("complex_plugin", complex_plugin)
        plugin = plugin_manager.initialize_plugin("complex_plugin")
        
        # 模拟错误
        plugin.process_data = lambda x: x/0
        
        # 测试错误处理和恢复
        with pytest.raises(Exception):
            plugin_manager.process_plugin_data("complex_plugin", 1)
            
        # 重置插件
        assert plugin_manager.reset_plugin("complex_plugin")
        
        # 验证恢复
        plugin = plugin_manager.get_plugin("complex_plugin")
        assert isinstance(plugin, complex_plugin)
        assert not plugin.activated 