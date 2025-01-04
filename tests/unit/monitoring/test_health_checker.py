"""健康检查器测试"""
import pytest
from unittest.mock import MagicMock
from dependency_monitoring_framework.src.core.health_checker import HealthChecker
from dependency_monitoring_framework.src.interfaces.health_check_plugin import HealthCheckPlugin

@pytest.fixture
def mock_health_plugin():
    class MockHealthPlugin(HealthCheckPlugin):
        def check(self):
            return {"status": "healthy"}
    return MockHealthPlugin()

@pytest.fixture
def health_checker():
    return HealthChecker()

class TestHealthChecker:
    def test_register_plugin(self, health_checker, mock_health_plugin):
        """测试注册健康检查插件"""
        health_checker.register_plugin("test", mock_health_plugin)
        assert "test" in health_checker.get_plugins()

    def test_check_health(self, health_checker, mock_health_plugin):
        """测试健康检查"""
        health_checker.register_plugin("test", mock_health_plugin)
        result = health_checker.check_health()
        assert result["test"]["status"] == "healthy"

    def test_remove_plugin(self, health_checker, mock_health_plugin):
        """测试移除插件"""
        health_checker.register_plugin("test", mock_health_plugin)
        health_checker.remove_plugin("test")
        assert "test" not in health_checker.get_plugins() 