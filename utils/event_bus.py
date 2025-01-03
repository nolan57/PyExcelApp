# event_bus.py
from typing import Dict, List, Callable, Any, Tuple
import logging
from collections import defaultdict
from queue import PriorityQueue
import asyncio
from PyQt6.QtCore import QThreadPool, QRunnable, QTimer, Qt, QObject
import traceback

class EventBus(QObject):
    def __init__(self):
        super().__init__()
        self._subscribers = defaultdict(list)
        self._last_events = {}
        self._event_queue = PriorityQueue()
        self._processing = False
        self._lock = asyncio.Lock()
        self._logger = logging.getLogger(__name__)
        self._thread_pool = QThreadPool.globalInstance()
        self._timeout = 5000  # 每个监听器的最大执行时间（毫秒）

    def subscribe(self, event_type: str, callback: Callable, priority: int = 1) -> None:
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
            priority: 回调优先级，默认为1（数字越小优先级越高）
        """
        if (priority, callback) not in self._subscribers[event_type]:
            self._subscribers[event_type].append((priority, callback))
            self._subscribers[event_type].sort(key=lambda x: x[0])
        self._logger.debug(f"已订阅事件 {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """
        取消订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                (p, cb) for p, cb in self._subscribers[event_type] if cb != callback
            ]
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]
        self._logger.debug(f"已取消订阅事件 {event_type}")

    async def publish(self, event_type: str, data: Any = None, priority: int = 1) -> None:
        """
        发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            priority: 事件优先级，默认为1（数字越小优先级越高）
        """
        self._last_events[event_type] = data
        async with self._lock:
            self._event_queue.put((priority, (event_type, data)))
            if not self._processing:
                self._processing = True
                asyncio.create_task(self._process_events())

    async def _process_events(self) -> None:
        while not self._event_queue.empty():
            _, (event_type, data) = self._event_queue.get_nowait()
            for _, callback in self._subscribers[event_type]:
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

        self._processing = False

    def _check_timeout(self, task, event_type: str):
        """检查任务是否超时"""
        if not task.is_finished:
            self._logger.warning(f"事件 {event_type} 处理超时 ({self._timeout}ms)")

    def get_last_event(self, event_type: str) -> Any:
        """
        获取最后一次事件数据
        
        Args:
            event_type: 事件类型
            
        Returns:
            最后一次事件的数据，如果没有则返回None
        """
        return self._last_events.get(event_type)

    def clear_subscribers(self, event_type: str = None) -> None:
        """
        清除订阅者
        
        Args:
            event_type: 要清除的事件类型，如果为None则清除所有
        """
        if event_type:
            if event_type in self._subscribers:
                del self._subscribers[event_type]
        else:
            self._subscribers.clear()
        self._logger.debug("已清除所有事件订阅")

    def shutdown(self):
        """关闭事件总线"""
        self._thread_pool.waitForDone()
        self._logger.debug("事件总线已关闭")

    def get_subscriber_count(self, event_type: str) -> int:
        """
        获取订阅者数量
        
        Args:
            event_type: 事件类型
            
        Returns:
            订阅者数量
        """
        return len(self._subscribers.get(event_type, []))

    def get_all_event_types(self) -> List[str]:
        """
        获取所有事件类型
        
        Returns:
            事件类型列表
        """
        return list(self._subscribers.keys())
