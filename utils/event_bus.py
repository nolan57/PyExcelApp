# event_bus.py
from typing import Dict, List, Callable, Any
import logging
from collections import defaultdict
from PyQt6.QtCore import QThreadPool, QRunnable, QTimer, Qt, QObject
import traceback


class EventBus(QObject):
    def __init__(self):
        super().__init__()
        self._subscribers = {}
        self._logger = logging.getLogger(__name__)
        self._thread_pool = QThreadPool.globalInstance()
        self._timeout = 5000  # 每个监听器的最大执行时间（毫秒）

    def subscribe(self, event_type: str, callback: Callable):
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        self._logger.debug(f"已订阅事件 {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable):
        """
        取消订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)
            self._logger.debug(f"已取消订阅事件 {event_type}")

    def emit(self, event_type: str, data: Dict = None):
        """
        发送事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                # 创建任务在主线程中执行回调
                class CallbackTask(QRunnable):
                    def __init__(self, callback, data, logger):
                        super().__init__()
                        self.callback = callback
                        self.data = data
                        self.logger = logger
                        self.is_finished = False

                    def run(self):
                        # 确保在主线程中执行回调
                        def execute_in_main_thread():
                            try:
                                if self.data:
                                    self.callback(self.data)
                                else:
                                    self.callback()
                                self.logger.debug(f"事件 {event_type} 处理成功")
                            except Exception as e:
                                self.logger.error(f"处理事件 {event_type} 时出错: {str(e)}")
                                self.logger.debug(traceback.format_exc())
                            finally:
                                self.is_finished = True

                        QTimer.singleShot(0, execute_in_main_thread)

                # 创建并启动任务
                task = CallbackTask(callback, data, self._logger)
                self._thread_pool.start(task)

                # 设置超时检查
                timer = QTimer()
                timer.setSingleShot(True)
                timer.timeout.connect(
                    lambda: self._check_timeout(task, event_type)
                )
                timer.start(self._timeout)

    def _check_timeout(self, task, event_type: str):
        """检查任务是否超时"""
        if not task.is_finished:
            self._logger.warning(f"事件 {event_type} 处理超时 ({self._timeout}ms)")

    def clear(self):
        """清除所有订阅"""
        self._subscribers.clear()
        self._logger.debug("已清除所有事件订阅")

    def shutdown(self):
        """关闭事件总线"""
        self._thread_pool.waitForDone()
        self._logger.debug("事件总线已关闭")
