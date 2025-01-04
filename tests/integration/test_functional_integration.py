"""功能集成测试"""
import pytest
from unittest.mock import MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

# 确保有 QApplication 实例
app = QApplication.instance() or QApplication([])

def simulate_ui_operations(window, operations):
    """模拟UI操作
    
    Args:
        window: 要操作的窗口
        operations: 操作列表，每个操作是一个(action, params)元组
    """
    for action, params in operations:
        if action == "click":
            widget = window.findChild(params["widget_type"], params["widget_name"])
            QTest.mouseClick(widget, Qt.MouseButton.LeftButton)
        elif action == "input":
            widget = window.findChild(params["widget_type"], params["widget_name"])
            QTest.keyClicks(widget, params["text"])
        elif action == "select":
            widget = window.findChild(params["widget_type"], params["widget_name"])
            widget.setCurrentIndex(params["index"])

def create_test_event(event_type, **kwargs):
    """创建测试事件
    
    Args:
        event_type: 事件类型
        **kwargs: 事件参数
        
    Returns:
        dict: 事件数据
    """
    return {
        "type": event_type,
        "timestamp": "2024-01-01T00:00:00",
        "data": kwargs
    }

@pytest.mark.integration
class TestFunctionalIntegration:
    """功能集成测试"""
    
    def test_excel_processing_workflow(self, mock_main_window, sample_excel_data):
        """测试Excel处理工作流"""
        # 模拟打开文件
        operations = [
            ("click", {"widget_type": "QPushButton", "widget_name": "openButton"}),
            ("select", {"widget_type": "QComboBox", "widget_name": "sheetSelect", "index": 0})
        ]
        simulate_ui_operations(mock_main_window, operations)
        
        # 验证数据加载
        assert mock_main_window.table_view.model() is not None
        
        # 模拟数据处理
        operations = [
            ("click", {"widget_type": "QPushButton", "widget_name": "processButton"})
        ]
        simulate_ui_operations(mock_main_window, operations)
        
        # 验证结果
        processed_data = mock_main_window.get_processed_data()
        assert processed_data is not None
        assert len(processed_data) > 0
        
    @pytest.mark.integration
    def test_plugin_integration(self, mock_main_window, mock_plugin):
        """测试插件集成"""
        # 模拟插件操作
        operations = [
            ("click", {"widget_type": "QPushButton", "widget_name": "pluginButton"}),
            ("select", {"widget_type": "QListView", "widget_name": "pluginList", "index": 0})
        ]
        simulate_ui_operations(mock_main_window, operations)
        
        # 验证插件执行
        event = create_test_event("plugin_execute", plugin_id="test_plugin")
        mock_main_window.handle_event(event)
        
        # 验证结果
        assert mock_plugin.process_data.called
        
    @pytest.mark.integration
    def test_monitoring_integration(self, mock_main_window, monitoring_system):
        """测试监控集成"""
        # 创建测试事件
        event = create_test_event("dependency_check", package="test-package")
        
        # 处理事件
        result = monitoring_system.process_and_notify(event)
        assert result is True
        
        # 验证通知
        assert monitoring_system.notification_manager.notify_all.called 