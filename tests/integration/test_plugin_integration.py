import pytest
from plugin_manager.core.plugin_system import PluginSystem
from plugin_manager.core.plugin_interface import PluginInterface
from plugin_manager.features.plugin_permissions import PluginPermission
from unittest.mock import MagicMock

@pytest.fixture
def plugin_system():
    """创建插件系统实例的fixture"""
    return PluginSystem()

@pytest.fixture
def mock_plugin():
    """创建模拟插件的fixture"""
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
            
        def process_data(self, data):
            return data
    
    return TestPlugin

def test_plugin_lifecycle(plugin_system, mock_plugin):
    """测试插件完整生命周期"""
    # 加载插件
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr('plugin_manager.core.plugin_loader.PluginLoader.load_plugin', 
                  lambda *args: mock_plugin)
        
        # 加载
        assert plugin_system.load_plugin('test_plugin')
        assert 'test_plugin' in plugin_system.get_all_plugins()
        
        # 激活
        assert plugin_system.activate_plugin('test_plugin')
        assert plugin_system.get_plugin_state('test_plugin') == 'active'
        
        # 停用
        assert plugin_system.deactivate_plugin('test_plugin')
        assert plugin_system.get_plugin_state('test_plugin') == 'inactive'
        
        # 卸载
        assert plugin_system.unload_plugin('test_plugin')
        assert 'test_plugin' not in plugin_system.get_all_plugins()

def test_plugin_permissions(plugin_system, mock_plugin):
    """测试插件权限管理"""
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr('plugin_manager.core.plugin_loader.PluginLoader.load_plugin', 
                  lambda *args: mock_plugin)
        
        plugin_system.load_plugin('test_plugin')
        
        # 请求权限
        assert plugin_system.request_permission('test_plugin', PluginPermission.READ)
        assert PluginPermission.READ in plugin_system.get_plugin_permissions('test_plugin')
        
        # 撤销权限
        plugin_system.revoke_permission('test_plugin', PluginPermission.READ)
        assert PluginPermission.READ not in plugin_system.get_plugin_permissions('test_plugin')

def test_plugin_configuration(plugin_system, mock_plugin):
    """测试插件配置管理"""
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr('plugin_manager.core.plugin_loader.PluginLoader.load_plugin', 
                  lambda *args: mock_plugin)
        
        plugin_system.load_plugin('test_plugin')
        
        # 设置配置
        config = {'key': 'value'}
        plugin_system.set_plugin_config('test_plugin', config)
        assert plugin_system.get_plugin_config('test_plugin') == config

def test_plugin_error_handling(plugin_system):
    """测试插件错误处理"""
    # 测试加载不存在的插件
    with pytest.raises(Exception):
        plugin_system.load_plugin('nonexistent_plugin')
    
    # 测试操作未加载的插件
    with pytest.raises(Exception):
        plugin_system.activate_plugin('nonexistent_plugin')

@pytest.mark.integration
def test_plugin_data_processing(plugin_system, mock_plugin, sample_excel_data):
    """测试插件数据处理集成"""
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr('plugin_manager.core.plugin_loader.PluginLoader.load_plugin', 
                  lambda *args: mock_plugin)
        
        plugin_system.load_plugin('test_plugin')
        plugin_system.activate_plugin('test_plugin')
        
        # 处理数据
        result = plugin_system.process_data('test_plugin', sample_excel_data)
        assert result is not None
        assert isinstance(result, type(sample_excel_data))

@pytest.mark.integration
def test_plugin_dependencies(plugin_system, mock_plugin):
    """测试插件依赖管理"""
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr('plugin_manager.core.plugin_loader.PluginLoader.load_plugin', 
                  lambda *args: mock_plugin)
        
        # 添加依赖信息
        plugin_system.dependency_manager.add_dependency('test_plugin', {
            'package': 'test-package',
            'version': '1.0.0'
        })
        
        # 加载插件（应该触发依赖检查）
        assert plugin_system.load_plugin('test_plugin')
        
        # 验证依赖状态
        deps = plugin_system.dependency_manager.get_dependencies('test_plugin')
        assert len(deps) > 0
        assert deps[0]['package'] == 'test-package'

@pytest.mark.integration
def test_plugin_events(plugin_system, mock_plugin):
    """测试插件事件系统"""
    events = []
    
    def event_handler(event):
        events.append(event)
    
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr('plugin_manager.core.plugin_loader.PluginLoader.load_plugin', 
                  lambda *args: mock_plugin)
        
        # 注册事件处理器
        plugin_system.event_manager.register_handler('plugin_loaded', event_handler)
        
        # 触发事件
        plugin_system.load_plugin('test_plugin')
        
        # 验证事件处理
        assert len(events) > 0
        assert events[0]['type'] == 'plugin_loaded'
        assert events[0]['plugin_id'] == 'test_plugin'
