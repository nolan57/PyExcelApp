from typing import Optional, Any
from abc import ABC, abstractmethod
from PyQt6.QtWidgets import QWidget, QMessageBox
import logging

class PluginError(Exception):
    """插件相关错误的基类"""
    pass

class PluginLoadError(PluginError):
    """插件加载错误"""
    pass

class PluginConfigError(PluginError):
    """插件配置错误"""
    pass

class PluginPermissionError(PluginError):
    """插件权限错误"""
    pass

class PluginRuntimeError(PluginError):
    """插件运行时错误"""
    pass

class ErrorHandler:
    """错误处理工具类"""
    
    _logger = logging.getLogger("PluginSystem")
    
    @staticmethod
    def handle_error(error: Exception, parent: Optional[QWidget] = None, message: Optional[str] = None) -> None:
        """处理错误"""
        error_msg = message or str(error)
        ErrorHandler._logger.error(f"错误: {error_msg}")
        
        if parent:
            QMessageBox.critical(parent, "错误", error_msg)
            
    @staticmethod
    def handle_warning(message: str, parent: Optional[QWidget] = None) -> None:
        """处理警告"""
        ErrorHandler._logger.warning(f"警告: {message}")
        
        if parent:
            QMessageBox.warning(parent, "警告", message)
            
    @staticmethod
    def handle_info(message: str, parent: Optional[QWidget] = None) -> None:
        """处理信息"""
        ErrorHandler._logger.info(message)
        
        if parent:
            QMessageBox.information(parent, "信息", message)

class ErrorHandlerInterface(ABC):
    """错误处理接口"""
    
    @abstractmethod
    def handle_error(self, error: Exception, parent: Optional[QWidget] = None, message: Optional[str] = None) -> None:
        """处理错误"""
        pass
        
    @abstractmethod
    def handle_warning(self, message: str, parent: Optional[QWidget] = None) -> None:
        """处理警告"""
        pass
        
    @abstractmethod
    def handle_info(self, message: str, parent: Optional[QWidget] = None) -> None:
        """处理信息"""
        pass
        
    @abstractmethod
    def on_error(self, error: Exception, context: Optional[Any] = None) -> None:
        """错误回调"""
        pass 