from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QMenuBar, QMenu
from PyQt6.QtGui import QAction
from ui.toolbar import ToolBar
from ui.workbook import WorkbookWidget
from plugin_manager.plugin_system import PluginSystem
from utils.event_bus import EventBus
from globals import GlobalState
from utils.error_handler import ErrorHandler
import logging

class MainWindow(QMainWindow):
    def __init__(self, plugin_system=None):

        self.global_state = None
        self.workbook_widget = None
        self.toolbar = None
        self.plugin_system = None
        try:
            super().__init__()
            
            # 初始化事件总线
            self.event_bus = GlobalState().event_bus

            # 初始化插件系统
            print("获取插件系统")  # 调试日志
            if plugin_system is not None:
                print("插件系统已初始化")  # 调试日志
                self.plugin_system = plugin_system
            
            # 初始化日志
            self._logger = logging.getLogger(__name__)
            
            # 初始化UI
            self.init_ui()
            
        except Exception as e:
            ErrorHandler.handle_error(e)
        
    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle('Excel 处理工具')
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建垂直布局
        layout = QVBoxLayout(central_widget)
        
        # 创建工具栏
        self.toolbar = ToolBar(self)
        self.addToolBar(self.toolbar)
        
        # 创建工作簿组件
        self.workbook_widget = WorkbookWidget(self)
        layout.addWidget(self.workbook_widget)
        
        # 更新全局状态
        self.global_state = GlobalState()
        self.global_state.workbook.tab_widget = self.workbook_widget.tab_widget
        
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 清理插件系统
        self.plugin_system = None
        event.accept()

