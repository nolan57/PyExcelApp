"""功能性集成测试"""
import pytest

@pytest.mark.integration
class TestPluginFunctionalIntegration:
    """插件功能集成测试"""
    
    def test_data_processing_workflow(self, plugin_system, excel_plugin):
        """测试数据处理工作流"""
        # 设置插件
        plugin_system.load_plugin('excel_plugin')
        plugin_system.activate_plugin('excel_plugin')
        
        # 处理数据
        test_data = create_test_data()
        result = plugin_system.process_data('excel_plugin', test_data)
        assert validate_processed_data(result)

    def test_ui_interaction_workflow(self, plugin_system, ui_plugin):
        """测试UI交互工作流"""
        # 设置UI插件
        plugin_system.load_plugin('ui_plugin')
        plugin_system.activate_plugin('ui_plugin')
        
        # 模拟UI操作
        result = simulate_ui_operations(plugin_system, ui_plugin)
        assert validate_ui_results(result)

@pytest.mark.integration
class TestMonitoringFunctionalIntegration:
    """监控功能集成测试"""
    
    def test_dependency_check_workflow(self, monitoring_system):
        """测试依赖检查工作流"""
        # 执行依赖检查
        results = monitoring_system.check_dependencies()
        assert validate_dependency_results(results)

    def test_notification_workflow(self, monitoring_system):
        """测试通知工作流"""
        # 触发通知流程
        event = create_test_event()
        result = monitoring_system.process_and_notify(event)
        assert validate_notification_results(result) 