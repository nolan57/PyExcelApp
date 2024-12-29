from typing import Optional
import logging
from PyQt6.QtWidgets import QMessageBox

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
        error_msg = message if message else str(error)
        QMessageBox.critical(parent, "错误", error_msg)
        
    @staticmethod
    def handle_warning(message: str, parent=None):
        """
        显示警告信息
        
        Args:
            message: 警告信息
            parent: 父窗口，用于显示消息框
        """
        QMessageBox.warning(parent, "警告", message)
        
    @staticmethod
    def handle_info(message: str, parent=None):
        """
        显示信息提示
        
        Args:
            message: 提示信息
            parent: 父窗口，用于显示消息框
        """
        QMessageBox.information(parent, "提示", message)
