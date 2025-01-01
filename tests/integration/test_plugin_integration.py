import unittest
from plugin_manager.core.plugin_system import PluginSystem
from tests.test_plugins.test_plugin import TestPlugin

class TestPluginIntegration(unittest.TestCase):
    def setUp(self):
        self.plugin_system = PluginSystem()

    def test_plugin_lifecycle(self):
        # 测试插件完整生命周期
        self.plugin_system.load_plugin('test_plugin')
        self.assertIsInstance(self.plugin_system.get_plugin('test_plugin'), TestPlugin)
        
        self.assertTrue(self.plugin_system.activate_plugin('test_plugin'))
        self.assertEqual(self.plugin_system.get_plugin_state('test_plugin'), 'active')
        
        self.assertTrue(self.plugin_system.deactivate_plugin('test_plugin'))
        self.assertEqual(self.plugin_system.get_plugin_state('test_plugin'), 'inactive')
        
        self.plugin_system.unload_plugin('test_plugin')
        self.assertNotIn('test_plugin', self.plugin_system.get_all_plugins())

if __name__ == '__main__':
    unittest.main()
