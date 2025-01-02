"""Unit tests for dependency management functionality."""

import unittest
from unittest.mock import patch, MagicMock
from plugin_manager.features.dependencies.plugin_dependencies import DependencyManager, PluginDependency

class TestDependencyManager(unittest.TestCase):
    def setUp(self):
        self.manager = DependencyManager()

    def test_add_dependency(self):
        """Test adding a dependency."""
        self.manager.add_dependency('test_plugin', 
            PluginDependency(name='test_package', version='1.0.0'))
        deps = self.manager.get_dependencies('test_plugin')
        self.assertEqual(len(deps), 1)
        self.assertEqual(next(iter(deps)).name, 'test_package')

    def test_remove_dependency(self):
        """Test removing a dependency."""
        self.manager.add_dependency('test_plugin',
            PluginDependency(name='test_package', version='1.0.0'))
        self.manager.remove_dependency('test_plugin', 'test_package')
        deps = self.manager.get_dependencies('test_plugin')
        self.assertEqual(len(deps), 0)

    @patch('plugin_manager.features.dependencies.plugin_dependencies.DependencyManager.download_dependencies')
    def test_preload_dependencies(self, mock_download):
        """Test preloading dependencies."""
        self.manager.add_dependency('test_plugin',
            PluginDependency(name='test_package', version='1.0.0'))
        mock_download.return_value = True
        result = self.manager.preload_dependencies('test_plugin')
        self.assertTrue(result)

    def test_get_dependency_status(self):
        """Test getting dependency status."""
        self.manager.add_dependency('test_plugin',
            PluginDependency(name='test_package', version='1.0.0'))
        status = self.manager.get_dependency_status('test_plugin')
        self.assertIn('test_package', status)

    @patch('plugin_manager.features.dependencies.plugin_dependencies.DependencyManager.uninstall_dependency')
    def test_rollback_dependencies(self, mock_uninstall):
        """Test rolling back dependencies."""
        self.manager.add_dependency('test_plugin',
            PluginDependency(name='test_package', version='1.0.0'))
        # 模拟缓存状态
        self.manager._cache = {'test_package': '/path/to/cache'}
        self.manager.rollback_dependencies('test_plugin')
        mock_uninstall.assert_called_once_with('test_plugin', 'test_package')

if __name__ == '__main__':
    unittest.main()
