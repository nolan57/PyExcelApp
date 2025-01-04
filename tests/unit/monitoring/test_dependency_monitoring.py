"""依赖监控框架的单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from dependency_monitoring_framework.src.core.event_bus import EventBus
from dependency_monitoring_framework.src.services.version_checker import VersionChecker
from dependency_monitoring_framework.src.services.security_scanner import SecurityScanner
from dependency_monitoring_framework.src.services.compatibility_checker import CompatibilityChecker
from dependency_monitoring_framework.src.channels.email_notifier import EmailNotifier
from dependency_monitoring_framework.src.channels.slack_notifier import SlackNotifier

# 添加标记
pytestmark = pytest.mark.monitoring

@pytest.fixture
def event_bus():
    """创建事件总线实例的fixture"""
    return EventBus()

@pytest.fixture
def mock_response():
    """创建模拟响应的fixture"""
    response = MagicMock()
    response.status_code = 200
    return response

class TestVersionMonitoring:
    """版本监控测试"""
    
    @pytest.mark.parametrize("version_data,expected_status", [
        ({"status": "up_to_date"}, "up_to_date"),
        ({"status": "outdated", "latest": "2.0.0"}, "outdated"),
        ({"status": "error"}, "error")
    ])
    def test_version_check(self, event_bus, mock_response, version_data, expected_status):
        """测试版本检查功能"""
        mock_response.json.return_value = version_data
        
        with patch('requests.get', return_value=mock_response):
            checker = VersionChecker(event_bus)
            result = checker.check()
            assert result['status'] == expected_status

class TestSecurityMonitoring:
    """安全监控测试"""
    
    @pytest.mark.parametrize("vulnerability_data", [
        {"vulnerabilities": []},
        {"vulnerabilities": [{"id": "CVE-2023-001", "severity": "high"}]},
        {"vulnerabilities": None}
    ])
    def test_security_scan(self, event_bus, mock_response, vulnerability_data):
        """测试安全扫描功能"""
        mock_response.json.return_value = [vulnerability_data]
        mock_response.status_code = 200
        
        with patch('requests.post', return_value=mock_response):
            scanner = SecurityScanner(event_bus)
            scanner._get_project_dependencies = lambda: [
                {'name': 'test-package', 'version': '1.0.0'}
            ]
            result = scanner.check()
            assert 'vulnerabilities' in result

class TestCompatibilityChecking:
    """兼容性检查测试"""
    
    @pytest.mark.parametrize("compatibility_data,expected_result", [
        ({"compatible": True}, True),
        ({"compatible": False, "reason": "Version mismatch"}, False),
        ({"compatible": None}, None)
    ])
    def test_compatibility_check(self, event_bus, mock_response, compatibility_data, expected_result):
        """测试兼容性检查功能"""
        mock_response.json.return_value = compatibility_data
        
        with patch('requests.get', return_value=mock_response):
            checker = CompatibilityChecker(event_bus)
            result = checker.check()
            assert result.get('compatible') == expected_result

class TestNotificationChannels:
    """通知渠道测试"""
    
    def test_email_notification(self):
        """测试邮件通知"""
        notifier = EmailNotifier()
        config = {
            'smtp_server': 'test.smtp.com',
            'smtp_port': 587,
            'smtp_user': 'test',
            'smtp_password': 'test',
            'from_email': 'from@test.com',
            'to_email': 'to@test.com'
        }
        
        with patch('smtplib.SMTP') as mock_smtp:
            notifier.configure(config)
            notifier.notify('Test', 'Test message')
            mock_smtp.assert_called()
            
    def test_slack_notification(self):
        """测试Slack通知"""
        notifier = SlackNotifier()
        config = {
            'webhook_url': 'https://hooks.slack.com/test',
            'channel': '#test'
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            notifier.configure(config)
            notifier.notify('Test', 'Test message')
            mock_post.assert_called()

class TestIntegratedMonitoring:
    """集成监控测试"""
    
    def test_monitoring_workflow(self, event_bus):
        """测试完整监控工作流"""
        mock_responses = {
            'version': {"status": "up_to_date"},
            'security': [{"vulnerabilities": []}],
            'compatibility': {"compatible": True}
        }
        
        with patch('requests.post') as mock_post, patch('requests.get') as mock_get:
            def mock_response(*args, **kwargs):
                url = args[0]
                response = MagicMock()
                response.status_code = 200
                if 'version' in url:
                    response.json.return_value = mock_responses['version']
                elif 'security' in url:
                    response.json.return_value = mock_responses['security']
                else:
                    response.json.return_value = mock_responses['compatibility']
                return response
            
            mock_get.side_effect = mock_response
            mock_post.side_effect = mock_response
            
            # 模拟依赖列表
            SecurityScanner._get_project_dependencies = lambda self: [
                {'name': 'test-package', 'version': '1.0.0'}
            ]
            
            # 执行所有检查
            version_checker = VersionChecker(event_bus)
            security_scanner = SecurityScanner(event_bus)
            compatibility_checker = CompatibilityChecker(event_bus)
            
            version_result = version_checker.check()
            security_result = security_scanner.check()
            compatibility_result = compatibility_checker.check()
            
            # 验证结果
            assert version_result['status'] == 'up_to_date'
            assert security_result['vulnerabilities'] == []
            assert compatibility_result['compatible'] is True

    @pytest.mark.asyncio
    async def test_async_monitoring(self, event_bus):
        """测试异步监控功能"""
        # 创建一个真实的异步上下文管理器
        class MockResponse:
            def __init__(self):
                self.status = 200
                
            async def json(self):
                return {"status": "up_to_date"}
                
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        
        class MockSession:
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
                
            async def get(self, url, **kwargs):
                return MockResponse()
        
        with patch('aiohttp.ClientSession', return_value=MockSession()):
            checker = VersionChecker(event_bus)
            result = await checker.check_async()
            assert result['status'] == 'up_to_date'
