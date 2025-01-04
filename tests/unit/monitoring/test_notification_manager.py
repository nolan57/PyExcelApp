"""通知管理器测试"""
import pytest
from unittest.mock import MagicMock
from dependency_monitoring_framework.src.core.notification_manager import NotificationManager
from dependency_monitoring_framework.src.interfaces.notification_channel import NotificationChannel

@pytest.fixture
def mock_notification_channel():
    class MockChannel(NotificationChannel):
        def notify(self, title, message):
            return True
    return MockChannel()

@pytest.fixture
def notification_manager():
    return NotificationManager()

class TestNotificationManager:
    def test_add_channel(self, notification_manager, mock_notification_channel):
        """测试添加通知渠道"""
        notification_manager.add_channel("test", mock_notification_channel)
        assert "test" in notification_manager.get_channels()

    def test_send_notification(self, notification_manager, mock_notification_channel):
        """测试发送通知"""
        notification_manager.add_channel("test", mock_notification_channel)
        result = notification_manager.notify_all("Test", "Test message")
        assert result["test"] is True

    def test_remove_channel(self, notification_manager, mock_notification_channel):
        """测试移除通知渠道"""
        notification_manager.add_channel("test", mock_notification_channel)
        notification_manager.remove_channel("test")
        assert "test" not in notification_manager.get_channels() 