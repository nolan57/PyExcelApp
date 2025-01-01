from typing import Any, Dict, List, Optional, Set
from PyQt6.QtWidgets import QTableView, QProgressDialog, QDialog
from PyQt6.QtCore import Qt, QObject, QRunnable, QThreadPool
from PyQt6.QtCore import pyqtSignal as Signal
import logging
from dataclasses import dataclass

from plugin_manager.core.plugin_base import PluginBase
from plugin_manager.features.plugin_lifecycle import PluginState
from plugin_manager.features.plugin_permissions import PluginPermission
from models.table_model import TableModel
from utils.error_handler import ErrorHandler

@dataclass
class ProcessResult:
    """处理结果数据类"""
    success: bool
    message: str
    data: Any = None

class PluginTemplate(PluginBase):
    """插件模板类"""
    
    def __init__(self):
        super().__init__()
        # 初始化日志
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.setLevel(logging.DEBUG)
        self._setup_logging()
        
        # 插件配置
        self._config = {
            'option1': 'default',
            'option2': 123
        }
        
        # 权限配置
        self._required_permissions = {
            PluginPermission.DATA_READ,
            PluginPermission.DATA_WRITE
        }
        
        self._optional_permissions = {
            PluginPermission.UI_MODIFY
        }
        
        # 状态管理
        self._processing = False
        self._error_occurred = False
        
    def _setup_logging(self):
        """设置日志"""
        fh = logging.FileHandler(f'{self.get_name()}.log')
        fh.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self._logger.addHandler(fh)
        
    # 基本信息
    def get_name(self) -> str:
        return "plugin_template"
        
    def get_version(self) -> str:
        return "1.0.0"
        
    def get_description(self) -> str:
        return "插件模板"
        
    def get_dependencies(self) -> List[str]:
        return []
        
    # 配置管理
    def get_configuration(self) -> Dict[str, Any]:
        return self._config.copy()
        
    def validate_parameters(self, parameters: Dict[str, Any]) -> Optional[str]:
        """验证参数"""
        try:
            # 验证参数
            if 'option1' in parameters and not isinstance(parameters['option1'], str):
                return "option1 必须是字符串"
            return None
        except Exception as e:
            self._logger.error(f"参数验证失败: {e}")
            return str(e)
            
    # 生命周期管理
    def activate(self) -> None:
        """激活插件"""
        try:
            self._logger.info("开始激活插件")
            # 检查权限
            missing_permissions = self._required_permissions - self._granted_permissions
            if missing_permissions:
                for permission in missing_permissions:
                    if not self.request_permission(permission):
                        raise PermissionError(f"缺少必要权限: {permission}")
                        
            self._active = True
            self._state = PluginState.ACTIVE
            self._logger.info("插件激活成功")
            
        except Exception as e:
            self._state = PluginState.ERROR
            self._logger.error(f"插件激活失败: {e}")
            raise
            
    def deactivate(self) -> None:
        """停用插件"""
        self._active = False
        self._state = PluginState.LOADED
        self._granted_permissions.clear()
        
    def cleanup(self) -> None:
        """清理资源"""
        try:
            if hasattr(self, 'data_processor'):
                self.data_processor.stop()
            if hasattr(self, 'progress'):
                self.progress.close()
            super().cleanup()
        except Exception as e:
            self._logger.error(f"清理资源失败: {e}")
            
    # 数据处理
    class DataProcessor(QObject):
        finished = Signal()
        progress = Signal(int)
        error = Signal(str)
        
        class Task(QRunnable):
            def __init__(self, processor, data):
                super().__init__()
                self.processor = processor
                self.data = data
                
            def run(self):
                try:
                    # 处理数据
                    result = self.processor.process_item(self.data)
                    if result.success:
                        self.processor.on_item_completed(result)
                except Exception as e:
                    self.processor.error.emit(str(e))
                    
        def __init__(self, plugin):
            super().__init__()
            self.plugin = plugin
            self.thread_pool = QThreadPool.globalInstance()
            self._stop_requested = False
            
        def process(self, data_items):
            try:
                for item in data_items:
                    if self._stop_requested:
                        break
                    task = self.Task(self, item)
                    self.thread_pool.start(task)
            except Exception as e:
                self.error.emit(str(e))
                
        def stop(self):
            self._stop_requested = True
            self.thread_pool.clear()
            self.thread_pool.waitForDone()
            
    def _process_data(self, table_view: QTableView, **parameters) -> Any:
        """处理数据的具体实现"""
        if self._processing:
            return False
            
        self._processing = True
        try:
            # 检查权限
            if not self._active:
                raise RuntimeError("插件未激活")
                
            # 创建进度对话框
            self.progress = QProgressDialog("处理数据中...", "取消", 0, 100)
            self.progress.setWindowModality(Qt.WindowModality.WindowModal)
            
            # 创建数据处理器
            self.data_processor = self.DataProcessor(self)
            self.data_processor.progress.connect(self.progress.setValue)
            self.data_processor.error.connect(self._on_error)
            self.data_processor.finished.connect(self._on_completed)
            
            # 开始处理
            self.data_processor.process(self._get_data_items(table_view))
            
            return not self._error_occurred
            
        except Exception as e:
            self._logger.error(f"数据处理失败: {e}")
            return False
        finally:
            self._processing = False
            
    def _get_data_items(self, table_view: QTableView) -> List[Any]:
        """获取要处理的数据项"""
        raise NotImplementedError
        
    def _on_error(self, error_msg: str):
        """错误处理"""
        self._error_occurred = True
        self._logger.error(f"处理错误: {error_msg}")
        ErrorHandler.handle_error(Exception(error_msg), self.table_view)
        
    def _on_completed(self):
        """处理完成"""
        self._logger.info("处理完成")
        if hasattr(self, 'progress'):
            self.progress.close()
            
    # 测试支持
    def get_test_data(self) -> Dict[str, Any]:
        """获取测试数据"""
        return {
            'processing': self._processing,
            'error_occurred': self._error_occurred,
            'active': self._active,
            'state': self._state
        }
