import unittest
from unittest.mock import patch, MagicMock
from plugin_manager.core.plugin_system import PluginSystem
from plugin_manager.core.plugin_interface import PluginInterface
from plugin_manager.features.plugin_permissions import PluginPermission
from plugin_manager.utils.plugin_error import PluginError

class TestPluginSystem(unittest.TestCase):
    def setUp(self):
        self.plugin_system = PluginSystem()

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_load_plugin_success(self, mock_load_plugin):
        # 模拟加载插件成功
        mock_plugin_class = MagicMock(spec=PluginInterface)
        mock_plugin_instance = MagicMock(spec=PluginInterface)
        mock_plugin_class.return_value = mock_plugin_instance
        mock_load_plugin.return_value = mock_plugin_class

        self.plugin_system.load_plugin('test_plugin')
        self.assertIn('test_plugin', self.plugin_system.get_all_plugins())
        self.assertEqual(self.plugin_system.get_plugin_state('test_plugin'), 'loaded')

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_load_plugin_failure(self, mock_load_plugin):
        # 模拟加载插件失败
        mock_load_plugin.return_value = None

        self.assertFalse(self.plugin_system.load_plugin('test_plugin'))
        self.assertNotIn('test_plugin', self.plugin_system.get_all_plugins())

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_activate_plugin_success(self, mock_load_plugin):
        # 模拟加载插件成功
        mock_plugin_class = MagicMock(spec=PluginInterface)
        mock_plugin_instance = MagicMock(spec=PluginInterface)
        mock_plugin_class.return_value = mock_plugin_instance
        mock_load_plugin.return_value = mock_plugin_class

        self.plugin_system.load_plugin('test_plugin')
        self.assertTrue(self.plugin_system.activate_plugin('test_plugin'))
        self.assertEqual(self.plugin_system.get_plugin_state('test_plugin'), 'active')

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_activate_plugin_failure(self, mock_load_plugin):
        # 模拟加载插件失败
        mock_load_plugin.return_value = None

        with self.assertRaises(PluginError):
            self.plugin_system.activate_plugin('test_plugin')

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_deactivate_plugin_success(self, mock_load_plugin):
        # 模拟加载和激活插件成功
        mock_plugin_class = MagicMock(spec=PluginInterface)
        mock_plugin_instance = MagicMock(spec=PluginInterface)
        mock_plugin_class.return_value = mock_plugin_instance
        mock_load_plugin.return_value = mock_plugin_class

        self.plugin_system.load_plugin('test_plugin')
        self.plugin_system.activate_plugin('test_plugin')
        self.assertTrue(self.plugin_system.deactivate_plugin('test_plugin'))
        self.assertEqual(self.plugin_system.get_plugin_state('test_plugin'), 'inactive')

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_deactivate_plugin_failure(self, mock_load_plugin):
        # 模拟加载插件失败
        mock_load_plugin.return_value = None

        with self.assertRaises(PluginError):
            self.plugin_system.deactivate_plugin('test_plugin')

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_start_plugin_success(self, mock_load_plugin):
        # 模拟加载和激活插件成功
        mock_plugin_class = MagicMock(spec=PluginInterface)
        mock_plugin_instance = MagicMock(spec=PluginInterface)
        mock_plugin_class.return_value = mock_plugin_instance
        mock_load_plugin.return_value = mock_plugin_class

        self.plugin_system.load_plugin('test_plugin')
        self.plugin_system.activate_plugin('test_plugin')
        self.assertTrue(self.plugin_system.start_plugin('test_plugin'))
        self.assertIn('test_plugin', self.plugin_system._running_plugins)

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_start_plugin_failure(self, mock_load_plugin):
        # 模拟加载插件失败
        mock_load_plugin.return_value = None

        with self.assertRaises(PluginError):
            self.plugin_system.start_plugin('test_plugin')

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_stop_plugin_success(self, mock_load_plugin):
        # 模拟加载、激活和启动插件成功
        mock_plugin_class = MagicMock(spec=PluginInterface)
        mock_plugin_instance = MagicMock(spec=PluginInterface)
        mock_plugin_class.return_value = mock_plugin_instance
        mock_load_plugin.return_value = mock_plugin_class

        self.plugin_system.load_plugin('test_plugin')
        self.plugin_system.activate_plugin('test_plugin')
        self.plugin_system.start_plugin('test_plugin')
        self.assertTrue(self.plugin_system.stop_plugin('test_plugin'))
        self.assertNotIn('test_plugin', self.plugin_system._running_plugins)

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_stop_plugin_failure(self, mock_load_plugin):
        # 模拟加载插件失败
        mock_load_plugin.return_value = None

        with self.assertRaises(PluginError):
            self.plugin_system.stop_plugin('test_plugin')

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_unload_plugin_success(self, mock_load_plugin):
        # 模拟加载插件成功
        mock_plugin_class = MagicMock(spec=PluginInterface)
        mock_plugin_instance = MagicMock(spec=PluginInterface)
        mock_plugin_class.return_value = mock_plugin_instance
        mock_load_plugin.return_value = mock_plugin_class

        self.plugin_system.load_plugin('test_plugin')
        self.assertTrue(self.plugin_system.unload_plugin('test_plugin'))
        self.assertNotIn('test_plugin', self.plugin_system.get_all_plugins())

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_unload_plugin_failure(self, mock_load_plugin):
        # 模拟加载插件失败
        mock_load_plugin.return_value = None

        with self.assertRaises(PluginError):
            self.plugin_system.unload_plugin('test_plugin')

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_set_plugin_config_success(self, mock_load_plugin):
        # 模拟加载插件成功
        mock_plugin_class = MagicMock(spec=PluginInterface)
        mock_plugin_instance = MagicMock(spec=PluginInterface)
        mock_plugin_class.return_value = mock_plugin_instance
        mock_load_plugin.return_value = mock_plugin_class

        self.plugin_system.load_plugin('test_plugin')
        self.plugin_system.set_plugin_config('test_plugin', {'key': 'value'})
        self.assertEqual(self.plugin_system.get_plugin_config('test_plugin'), {'key': 'value'})

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_set_plugin_config_failure(self, mock_load_plugin):
        # 模拟加载插件失败
        mock_load_plugin.return_value = None

        with self.assertRaises(PluginError):
            self.plugin_system.set_plugin_config('test_plugin', {'key': 'value'})

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_request_permission_success(self, mock_load_plugin):
        # 模拟加载插件成功
        mock_plugin_class = MagicMock(spec=PluginInterface)
        mock_plugin_instance = MagicMock(spec=PluginInterface)
        mock_plugin_class.return_value = mock_plugin_instance
        mock_load_plugin.return_value = mock_plugin_class

        self.plugin_system.load_plugin('test_plugin')
        self.assertTrue(self.plugin_system.request_permission('test_plugin', PluginPermission.READ))

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_request_permission_failure(self, mock_load_plugin):
        # 模拟加载插件失败
        mock_load_plugin.return_value = None

        with self.assertRaises(PluginError):
            self.plugin_system.request_permission('test_plugin', PluginPermission.READ)

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_revoke_permission_success(self, mock_load_plugin):
        # 模拟加载插件成功
        mock_plugin_class = MagicMock(spec=PluginInterface)
        mock_plugin_instance = MagicMock(spec=PluginInterface)
        mock_plugin_class.return_value = mock_plugin_instance
        mock_load_plugin.return_value = mock_plugin_class

        self.plugin_system.load_plugin('test_plugin')
        self.plugin_system.revoke_permission('test_plugin', PluginPermission.READ)
        self.assertNotIn(PluginPermission.READ, self.plugin_system.permission_manager.get_granted_permissions('test_plugin'))

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_revoke_permission_failure(self, mock_load_plugin):
        # 模拟加载插件失败
        mock_load_plugin.return_value = None

        with self.assertRaises(PluginError):
            self.plugin_system.revoke_permission('test_plugin', PluginPermission.READ)

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_process_data_success(self, mock_load_plugin):
        # 模拟加载和激活插件成功
        mock_plugin_class = MagicMock(spec=PluginInterface)
        mock_plugin_instance = MagicMock(spec=PluginInterface)
        mock_plugin_class.return_value = mock_plugin_instance
        mock_load_plugin.return_value = mock_plugin_class

        self.plugin_system.load_plugin('test_plugin')
        self.plugin_system.activate_plugin('test_plugin')
        result = self.plugin_system.process_data('test_plugin', MagicMock(), key='value')
        self.assertIsNotNone(result)

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_process_data_failure(self, mock_load_plugin):
        # 模拟加载插件失败
        mock_load_plugin.return_value = None

        with self.assertRaises(PluginError):
            self.plugin_system.process_data('test_plugin', MagicMock(), key='value')

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_is_plugin_active_success(self, mock_load_plugin):
        # 模拟加载和激活插件成功
        mock_plugin_class = MagicMock(spec=PluginInterface)
        mock_plugin_instance = MagicMock(spec=PluginInterface)
        mock_plugin_class.return_value = mock_plugin_instance
        mock_load_plugin.return_value = mock_plugin_class

        self.plugin_system.load_plugin('test_plugin')
        self.plugin_system.activate_plugin('test_plugin')
        self.assertTrue(self.plugin_system.is_plugin_active('test_plugin'))

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_is_plugin_active_failure(self, mock_load_plugin):
        # 模拟加载插件失败
        mock_load_plugin.return_value = None

        with self.assertRaises(PluginError):
            self.plugin_system.is_plugin_active('test_plugin')

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_is_plugin_running_success(self, mock_load_plugin):
        # 模拟加载、激活和启动插件成功
        mock_plugin_class = MagicMock(spec=PluginInterface)
        mock_plugin_instance = MagicMock(spec=PluginInterface)
        mock_plugin_class.return_value = mock_plugin_instance
        mock_load_plugin.return_value = mock_plugin_class

        self.plugin_system.load_plugin('test_plugin')
        self.plugin_system.activate_plugin('test_plugin')
        self.plugin_system.start_plugin('test_plugin')
        self.assertTrue(self.plugin_system.is_plugin_running('test_plugin'))

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_is_plugin_running_failure(self, mock_load_plugin):
        # 模拟加载插件失败
        mock_load_plugin.return_value = None

        with self.assertRaises(PluginError):
            self.plugin_system.is_plugin_running('test_plugin')

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_reload_plugin_success(self, mock_load_plugin):
        # 模拟加载和激活插件成功
        mock_plugin_class = MagicMock(spec=PluginInterface)
        mock_plugin_instance = MagicMock(spec=PluginInterface)
        mock_plugin_class.return_value = mock_plugin_instance
        mock_load_plugin.return_value = mock_plugin_class

        self.plugin_system.load_plugin('test_plugin')
        self.plugin_system.activate_plugin('test_plugin')
        self.assertTrue(self.plugin_system.reload_plugin('test_plugin'))
        self.assertEqual(self.plugin_system.get_plugin_state('test_plugin'), 'loaded')

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_reload_plugin_failure(self, mock_load_plugin):
        # 模拟加载插件失败
        mock_load_plugin.return_value = None

        with self.assertRaises(PluginError):
            self.plugin_system.reload_plugin('test_plugin')

# 集成测试
class TestPluginSystemIntegration(unittest.TestCase):
    def setUp(self):
        self.plugin_system = PluginSystem()

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_full_plugin_lifecycle(self, mock_load_plugin):
        # 模拟加载插件成功
        mock_plugin_class = MagicMock(spec=PluginInterface)
        mock_plugin_instance = MagicMock(spec=PluginInterface)
        mock_plugin_class.return_value = mock_plugin_instance
        mock_load_plugin.return_value = mock_plugin_class

        # 加载插件
        self.plugin_system.load_plugin('test_plugin')
        self.assertIn('test_plugin', self.plugin_system.get_all_plugins())
        self.assertEqual(self.plugin_system.get_plugin_state('test_plugin'), 'loaded')

        # 激活插件
        self.assertTrue(self.plugin_system.activate_plugin('test_plugin'))
        self.assertEqual(self.plugin_system.get_plugin_state('test_plugin'), 'active')

        # 启动插件
        self.assertTrue(self.plugin_system.start_plugin('test_plugin'))
        self.assertIn('test_plugin', self.plugin_system._running_plugins)

        # 处理数据
        result = self.plugin_system.process_data('test_plugin', MagicMock(), key='value')
        self.assertIsNotNone(result)

        # 停止插件
        self.assertTrue(self.plugin_system.stop_plugin('test_plugin'))
        self.assertNotIn('test_plugin', self.plugin_system._running_plugins)

        # 卸载插件
        self.assertTrue(self.plugin_system.unload_plugin('test_plugin'))
        self.assertNotIn('test_plugin', self.plugin_system.get_all_plugins())

    @patch('plugin_manager.core.plugin_loader.PluginLoader.load_plugin')
    def test_plugin_with_dependencies(self, mock_load_plugin):
        # 模拟加载插件成功
        mock_plugin_class = MagicMock(spec=PluginInterface)
        mock_plugin_instance = MagicMock(spec=PluginInterface)
        mock_plugin_class.return_value = mock_plugin_instance
        mock_load_plugin.return_value = mock_plugin_class

        # 加载插件
        self.plugin_system.load_plugin('test_plugin')
        self.assertIn('test_plugin', self.plugin_system.get_all_plugins())
        self.assertEqual(self.plugin_system.get_plugin_state('test_plugin'), 'loaded')

        # 激活插件
        self.assertTrue(self.plugin_system.activate_plugin('test_plugin'))
        self.assertEqual(self.plugin_system.get_plugin_state('test_plugin'), 'active')

        # 请求权限
        self.assertTrue(self.plugin_system.request_permission('test_plugin', PluginPermission.READ))
        self.assertIn(PluginPermission.READ, self.plugin_system.permission_manager.get_granted_permissions('test_plugin'))

        # 设置配置
        self.plugin_system.set_plugin_config('test_plugin', {'key': 'value'})
        self.assertEqual(self.plugin_system.get_plugin_config('test_plugin'), {'key': 'value'})

        # 卸载插件
        self.assertTrue(self.plugin_system.unload_plugin('test_plugin'))
        self.assertNotIn('test_plugin', self.plugin_system.get_all_plugins())

if __name__ == '__main__':
    unittest.main()
