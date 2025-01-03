import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QIcon, QAction
from ui.main_window import MainWindow
from globals import GlobalState
from utils.error_handler import ErrorHandler
from dependency_monitoring_framework.src.core.event_bus import EventBus
from plugin_manager.utils.event_bus_adapter import EventBus as EventBusAdapter
from plugin_manager.core.plugin_system import PluginSystem
from dependency_monitoring_framework.src.services.security_scanner import SecurityScanner
from dependency_monitoring_framework.src.services.version_checker import VersionChecker
from dependency_monitoring_framework.src.services.compatibility_checker import CompatibilityChecker
import logging
from logging_config import LoggingConfig, LogLevel

def main():
    try:
        # 配置日志记录
        log_config = LoggingConfig('logs/app.log')
        log_config.configure_logging(LogLevel.INFO)
        
        # 创建应用程序
        app = QApplication(sys.argv)
        
        # 初始化事件总线
        monitor_event_bus = EventBus()
        event_bus = EventBusAdapter()
        
        # 初始化全局状态
        state = GlobalState()
        state.event_bus = event_bus  # 使用适配后的事件总线
        
        # 初始化依赖监控服务
        security_scanner = SecurityScanner(monitor_event_bus)
        version_checker = VersionChecker(monitor_event_bus)
        compatibility_checker = CompatibilityChecker(monitor_event_bus)
        
        # 初始化插件系统
        plugin_system = PluginSystem(event_bus=event_bus)
        
        # 订阅依赖监控事件
        monitor_event_bus.subscribe('security.vulnerability_found', 
            lambda data: event_bus.emit('dependency.security_check', data))
        monitor_event_bus.subscribe('version.update_available',
            lambda data: event_bus.emit('dependency.update_available', data))
        
        # 加载所有插件
        plugin_system.load_all_plugins()
        
        # 启动定期检查
        security_scanner.check()
        version_checker.check()
        compatibility_checker.check()
        
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
