from typing import Optional
import logging
import traceback
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt

class ErrorHandler:
    @staticmethod
    def log_debug(message: str):
        """
        记录调试信息
        
        Args:
            message: 调试信息
        """
        logging.debug(message)

    @staticmethod
    def handle_error(error: Exception, parent=None, message: Optional[str] = None):
        """
        统一处理异常，显示错误信息
        
        Args:
            error: 捕获的异常
            parent: 父窗口，用于显示消息框
            message: 自定义错误信息，如果为None则使用异常信息
        """
        if isinstance(error, PluginError):
            error_msg = f"插件错误: {message if message else str(error)}"
        else:
            error_msg = message if message else str(error)
        stack_trace = traceback.format_exc()
        ErrorHandler._show_message_box("错误", error_msg, parent, QMessageBox.Icon.Critical)
        ErrorHandler._log_error(error, stack_trace)

    @staticmethod
    def handle_info(message: str, parent=None):
        """
        显示信息提示
        
        Args:
            message: 提示信息
            parent: 父窗口，用于显示消息框
        """
        ErrorHandler._show_message_box("提示", message, parent, QMessageBox.Icon.Information)

    @staticmethod
    def handle_warning(message: str, parent=None):
        """
        显示警告信息
        
        Args:
            message: 警告信息
            parent: 父窗口，用于显示消息框
        """
        ErrorHandler._show_message_box("警告", message, parent, QMessageBox.Icon.Warning)

    @staticmethod
    def _show_message_box(title: str, message: str, parent=None, icon=QMessageBox.Icon.Critical):
        """
        显示消息框
        
        Args:
            title: 消息框的标题
            message: 消息框的内容
            parent: 父窗口，用于显示消息框
            icon: 消息框的图标，默认为 QMessageBox.Critical
        """
        QMessageBox(icon, title, message, QMessageBox.StandardButton.Ok, parent).exec()

    @staticmethod
    def _log_error(error: Exception, stack_trace: str):
        """
        记录错误信息到日志文件
        
        Args:
            error: 捕获的异常
            stack_trace: 异常的堆栈跟踪信息
        """
        logging.error(f"发生错误: {str(error)}")
        logging.error(f"堆栈跟踪信息:\n{stack_trace}")

class PluginError(Exception):
    """插件相关错误"""
    def __init__(self, message, plugin_name=None):
        self.message = message
        self.plugin_name = plugin_name
        super().__init__(self.message)

    @staticmethod
    def handle_plugin_error(error):
        """处理插件错误"""
        if isinstance(error, PluginError):
            plugin_name = error.plugin_name or "未知插件"
            logging.error(f"插件错误 [{plugin_name}]: {error.message}")
            ErrorHandler._show_message_box(
                "插件错误",
                f"插件 {plugin_name} 发生错误: {error.message}",
                icon=QMessageBox.Icon.Critical
            )
        else:
            logging.error(f"未知插件错误: {str(error)}")
            ErrorHandler._show_message_box(
                "插件错误",
                f"插件系统发生未知错误: {str(error)}",
                icon=QMessageBox.Icon.Critical
            )