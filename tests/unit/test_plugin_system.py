import unittest
from plugin_manager.core.plugin_system import PluginSystem

class TestPluginSystem(unittest.TestCase):
    def setUp(self):
        self.plugin_system = PluginSystem()

    def test_load_plugin(self):
        # 测试插件加载功能
        self.plugin_system.load_plugin('test_plugin')
        self.assertIn('test_plugin', self.plugin_system.get_all_plugins())

    def test_activate_plugin(self):
        # 测试插件激活功能
        self.plugin_system.load_plugin('test_plugin')
        self.assertTrue(self.plugin_system.activate_plugin('test_plugin'))
        self.assertEqual(self.plugin_system.get_plugin_state('test_plugin'), 'active')

if __name__ == '__main__':
    unittest.main()
