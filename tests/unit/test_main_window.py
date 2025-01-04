import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QMenu
from ui.main_window import MainWindow


@pytest.fixture
def mock_main_window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    return window

def test_main_window_init(mock_main_window):
    """测试主窗口初始化"""
    assert mock_main_window.windowTitle() == "PyExcel App"
    assert mock_main_window.isVisible() == False

def test_file_menu_actions(mock_main_window):
    """测试文件菜单动作"""
    file_menu = mock_main_window.menuBar().findChild(QMenu, "fileMenu")
    assert file_menu is not None
    
    # 测试打开文件动作
    open_action = file_menu.findChild(QAction, "openAction")
    assert open_action is not None
    assert open_action.text() == "打开"

def test_table_view(mock_main_window, sample_excel_data):
    """测试表格视图"""
    mock_main_window.load_data(sample_excel_data)
    table_view = mock_main_window.table_view
    
    assert table_view.model() is not None
    assert table_view.model().rowCount() == len(sample_excel_data)
    assert table_view.model().columnCount() == len(sample_excel_data.columns)

@pytest.mark.parametrize("key,expected", [
    (Qt.Key.Key_Delete, ""),
    (Qt.Key.Key_A, "A"),
    (Qt.Key.Key_1, "1")
])
def test_keyboard_input(mock_main_window, key, expected):
    """测试键盘输入"""
    table_view = mock_main_window.table_view
    table_view.setCurrentIndex(table_view.model().index(0, 0))
    QTest.keyClick(table_view, key)
    current_value = table_view.model().data(table_view.currentIndex(), Qt.ItemDataRole.DisplayRole)
    assert current_value == expected 