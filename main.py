import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QIcon, QAction
from ui.main_window import MainWindow
from logging_config import setup_logging
from globals import GlobalState
from utils.error_handler import ErrorHandler
from utils.event_bus import EventBus
from plugin_manager.core.plugin_system import PluginSystem
import logging

def main():
    try:
        setup_logging()
        app = QApplication(sys.argv)
        
        # 初始化全局状态
        state = GlobalState()

        # 初始化插件系统
        plugin_system = PluginSystem(state.event_bus)

        # 加载所有插件
        plugin_system.load_all_plugins()
        
        # 确保全局状态已初始化
        state = GlobalState()
        
        # 初始化主窗口
        window = MainWindow(plugin_system)
        window.show()

        # 应用程序退出时清理
        def cleanup():
            state.event_bus.clear()
            logging.info("应用程序清理完成")
            
        app.aboutToQuit.connect(cleanup)
        
        sys.exit(app.exec())
    except Exception as e:
        ErrorHandler.handle_error(e)

if __name__ == '__main__':
    main()
