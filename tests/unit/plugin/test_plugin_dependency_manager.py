import pytest
from unittest.mock import patch, MagicMock
from plugin_manager.features.dependencies.plugin_dependencies import DependencyManager, PluginDependency
from plugin_manager.utils.plugin_error import PluginError

@pytest.fixture
def dependency_manager():
    """创建依赖管理器实例的fixture"""
    return DependencyManager()

@pytest.fixture
def sample_dependency():
    """创建示例依赖的fixture"""
    return PluginDependency(name='test_package', version='1.0.0')

class TestDependencyManagerBasic:
    """基本依赖管理功能测试"""
    
    def test_add_dependency(self, dependency_manager, sample_dependency):
        """测试添加依赖"""
        dependency_manager.add_dependency('test_plugin', sample_dependency)
        deps = dependency_manager.get_dependencies('test_plugin')
        assert len(deps) == 1
        assert next(iter(deps)).name == 'test_package'

    def test_remove_dependency(self, dependency_manager, sample_dependency):
        """测试移除依赖"""
        dependency_manager.add_dependency('test_plugin', sample_dependency)
        dependency_manager.remove_dependency('test_plugin', 'test_package')
        deps = dependency_manager.get_dependencies('test_plugin')
        assert len(deps) == 0

    def test_get_dependency_status(self, dependency_manager, sample_dependency):
        """测试获取依赖状态"""
        dependency_manager.add_dependency('test_plugin', sample_dependency)
        status = dependency_manager.get_dependency_status('test_plugin')
        assert 'test_package' in status

class TestDependencyManagerAdvanced:
    """高级依赖管理功能测试"""
    
    @patch('plugin_manager.features.dependencies.plugin_dependencies.DependencyManager.download_dependencies')
    def test_preload_dependencies(self, mock_download, dependency_manager, sample_dependency):
        """测试预加载依赖"""
        mock_download.return_value = True
        dependency_manager.add_dependency('test_plugin', sample_dependency)
        result = dependency_manager.preload_dependencies('test_plugin')
        assert result
        mock_download.assert_called_once()

    @patch('plugin_manager.features.dependencies.plugin_dependencies.DependencyManager.verify_dependency')
    def test_dependency_verification(self, mock_verify, dependency_manager, sample_dependency):
        """测试依赖验证"""
        mock_verify.return_value = True
        dependency_manager.add_dependency('test_plugin', sample_dependency)
        assert dependency_manager.verify_dependencies('test_plugin')

    def test_dependency_version_check(self, dependency_manager):
        """测试依赖版本检查"""
        # 测试不同版本规范
        dependencies = [
            PluginDependency(name='pkg1', version='>=1.0.0'),
            PluginDependency(name='pkg2', version='~=2.0.0'),
            PluginDependency(name='pkg3', version='==3.0.0')
        ]
        
        for dep in dependencies:
            dependency_manager.add_dependency('test_plugin', dep)
            
        deps = dependency_manager.get_dependencies('test_plugin')
        assert len(deps) == 3
        
        versions = {dep.name: dep.version for dep in deps}
        assert versions['pkg1'] == '>=1.0.0'
        assert versions['pkg2'] == '~=2.0.0'
        assert versions['pkg3'] == '==3.0.0'

    @patch('plugin_manager.features.dependencies.plugin_dependencies.DependencyManager.uninstall_dependency')
    def test_rollback_dependencies(self, mock_uninstall, dependency_manager, sample_dependency):
        """测试依赖回滚"""
        dependency_manager.add_dependency('test_plugin', sample_dependency)
        # 模拟缓存状态
        dependency_manager._cache = {'test_package': '/path/to/cache'}
        
        dependency_manager.rollback_dependencies('test_plugin')
        mock_uninstall.assert_called_once_with('test_plugin', 'test_package')

    def test_circular_dependency_detection(self, dependency_manager):
        """测试循环依赖检测"""
        # 创建循环依赖场景
        dep_a = PluginDependency(name='plugin_a', version='1.0.0')
        dep_b = PluginDependency(name='plugin_b', version='1.0.0')
        
        dependency_manager.add_dependency('plugin_a', dep_b)
        dependency_manager.add_dependency('plugin_b', dep_a)
        
        with pytest.raises(PluginError) as exc_info:
            dependency_manager.verify_dependencies('plugin_a')
        assert "Circular dependency detected" in str(exc_info.value)

    def test_optional_dependencies(self, dependency_manager):
        """测试可选依赖"""
        required_dep = PluginDependency(name='required_pkg', version='1.0.0', required=True)
        optional_dep = PluginDependency(name='optional_pkg', version='1.0.0', required=False)
        
        dependency_manager.add_dependency('test_plugin', required_dep)
        dependency_manager.add_dependency('test_plugin', optional_dep)
        
        deps = dependency_manager.get_dependencies('test_plugin')
        required_deps = [dep for dep in deps if dep.required]
        optional_deps = [dep for dep in deps if not dep.required]
        
        assert len(required_deps) == 1
        assert len(optional_deps) == 1
        assert required_deps[0].name == 'required_pkg'
        assert optional_deps[0].name == 'optional_pkg' 