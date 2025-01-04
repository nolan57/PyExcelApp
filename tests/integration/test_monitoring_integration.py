"""监控系统渐进式集成测试"""
import pytest
from dependency_monitoring_framework.src.core.health_checker import HealthChecker
from dependency_monitoring_framework.src.core.notification_manager import NotificationManager

@pytest.mark.integration
class TestMonitoringIntegrationLevel1:
    """第一级集成测试：基本监控"""
    
    def test_basic_health_check(self, health_checker, version_checker):
        """测试基本健康检查"""
        health_checker.register_plugin("version", version_checker)
        results = health_checker.check_health()
        assert "version" in results

class TestMonitoringIntegrationLevel2:
    """第二级集成测试：通知系统"""
    
    def test_monitoring_with_notifications(self, health_checker, notification_manager):
        """测试带通知的监控"""
        # 设置监控
        health_checker.register_plugin("test", mock_health_plugin())
        
        # 设置通知
        notification_manager.add_channel("email", mock_email_channel())
        
        # 执行检查并通知
        results = health_checker.check_health()
        if any(result.get("status") == "error" for result in results.values()):
            notification_manager.notify_all("Error", "Issues detected")

class TestMonitoringIntegrationLevel3:
    """第三级集成测试：完整系统"""
    
    def test_full_monitoring_system(self, health_checker, notification_manager):
        """测试完整监控系统"""
        # 注册所有检查器
        health_checker.register_plugin("version", version_checker())
        health_checker.register_plugin("security", security_scanner())
        health_checker.register_plugin("compatibility", compatibility_checker())
        
        # 注册所有通知渠道
        notification_manager.add_channel("email", email_notifier())
        notification_manager.add_channel("slack", slack_notifier())
        
        # 执行完整检查
        results = health_checker.check_health()
        
        # 处理结果并通知
        self.process_and_notify(results, notification_manager) 