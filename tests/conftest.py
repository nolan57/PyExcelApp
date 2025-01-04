"""
测试配置和共享fixtures

注意：依赖管理测试已迁移到 test_plugin_dependency_manager.py
原 test_dependency_manager.py 已废弃
"""

import pytest
import os
import sys
from PyQt6.QtWidgets import QApplication
import pandas as pd

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 添加依赖监控框架路径
monitoring_path = os.path.join(project_root, 'dependency_monitoring_framework')
sys.path.insert(0, monitoring_path)

# 添加插件管理器路径
plugin_path = os.path.join(project_root, 'plugin_manager')
sys.path.insert(0, plugin_path)

@pytest.fixture(scope="session")
def qapp():
    """创建QApplication实例的fixture"""
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def sample_excel_data():
    """提供示例Excel数据的fixture"""
    return pd.DataFrame({
        'Column1': ['A1', 'A2', 'A3'],
        'Column2': [1, 2, 3],
        'Column3': ['X', 'Y', 'Z']
    })

@pytest.fixture
def temp_excel_file(tmp_path, sample_excel_data):
    """创建临时Excel文件的fixture"""
    file_path = tmp_path / "test.xlsx"
    sample_excel_data.to_excel(file_path, index=False)
    return file_path

@pytest.fixture
def mock_main_window(qapp):
    """模拟主窗口的fixture"""
    from main_window import MainWindow
    window = MainWindow()
    return window

@pytest.fixture
def mock_excel_processor():
    """模拟Excel处理器的fixture"""
    class MockExcelProcessor:
        def process_file(self, file_path):
            return pd.DataFrame({'test': [1, 2, 3]})
            
        def save_file(self, df, file_path):
            return True
    return MockExcelProcessor()

@pytest.fixture
def version_checker():
    """创建版本检查器的fixture"""
    return VersionChecker()

@pytest.fixture
def mock_health_plugin():
    """创建模拟健康检查插件的fixture"""
    class MockHealthPlugin(HealthCheckPlugin):
        def check(self):
            return {"status": "healthy"}
    return MockHealthPlugin()

@pytest.fixture
def mock_email_channel():
    """创建模拟邮件通道的fixture"""
    class MockEmailChannel(NotificationChannel):
        def notify(self, title, message):
            return True
    return MockEmailChannel()

@pytest.fixture
def security_scanner():
    """创建安全扫描器的fixture"""
    return SecurityScanner()

@pytest.fixture
def compatibility_checker():
    """创建兼容性检查器的fixture"""
    return CompatibilityChecker()

@pytest.fixture
def email_notifier():
    """创建邮件通知器的fixture"""
    return EmailNotifier()

@pytest.fixture
def slack_notifier():
    """创建Slack通知器的fixture"""
    return SlackNotifier()

@pytest.fixture
def monitoring_system(health_checker, notification_manager):
    """创建监控系统的fixture"""
    class MonitoringSystem:
        def __init__(self, health_checker, notification_manager):
            self.health_checker = health_checker
            self.notification_manager = notification_manager
            
        def check_dependencies(self):
            return self.health_checker.check_health()
            
        def process_and_notify(self, event):
            results = self.health_checker.check_health()
            if any(r.get("status") == "error" for r in results.values()):
                return self.notification_manager.notify_all(
                    "Error", f"Issue detected: {event}")
            return True
            
    return MonitoringSystem(health_checker, notification_manager)

@pytest.fixture
def create_test_data():
    """创建测试数据的fixture"""
    def _create_data():
        return pd.DataFrame({
            'test_col': range(5),
            'value_col': ['a', 'b', 'c', 'd', 'e']
        })
    return _create_data

@pytest.fixture
def validate_processed_data():
    """验证处理后数据的fixture"""
    def _validate(data):
        return isinstance(data, pd.DataFrame) and not data.empty
    return _validate

@pytest.fixture
def validate_ui_results():
    """验证UI操作结果的fixture"""
    def _validate(result):
        return isinstance(result, dict) and result.get('success') is True
    return _validate

@pytest.fixture
def validate_dependency_results():
    """验证依赖检查结果的fixture"""
    def _validate(results):
        return isinstance(results, dict) and 'status' in results
    return _validate

@pytest.fixture
def validate_notification_results():
    """验证通知结果的fixture"""
    def _validate(result):
        return isinstance(result, bool) and result is True
    return _validate
