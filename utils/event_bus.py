# event_bus.py
from typing import Dict, List, Callable, Any
import logging
from collections import defaultdict
from PyQt6.QtCore import QThreadPool, QRunnable, QTimer
import traceback


class EventBus:
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = defaultdict(list)
        self._logger = logging.getLogger(__name__)
        self._thread_pool = QThreadPool.globalInstance()
        self._timeout = 5000  # 每个监听器的最大执行时间（毫秒）
        # 确保在主线程初始化
        from PyQt6.QtCore import QCoreApplication
        if QCoreApplication.instance() is None:
            raise RuntimeError("EventBus must be initialized after QApplication is created")
        print("EventBus已使用QApplication实例初始化")  # 调试日志

    def on(self, event: str, listener: Callable) -> None:
        """
        注册事件监听器
        
        Args:
            event: 事件名称
            listener: 事件处理函数
        """
        self._listeners[event].append(listener)
        self._logger.debug(f"Registered listener for event: {event}")
        print(f"注册事件: {event} 的事件处理函数: {listener}")  # 调试日志

    def off(self, event: str, listener: Callable) -> None:
        """
        移除事件监听器
        
        Args:
            event: 事件名称
            listener: 事件处理函数
        """
        if event in self._listeners:
            self._listeners[event] = [l for l in self._listeners[event] if l != listener]
            self._logger.debug(f"Removed listener for event: {event}")

    def emit(self, event: str, data: Dict[str, Any] = None) -> None:
        """
        触发事件
        
        Args:
            event: 事件名称
            data: 事件数据
        """
        self._logger.debug(f"Emitting event: {event}")
        for listener in self._listeners[event]:
            print(f"事件{event}正在被监听器{listener}处理")

        for listener in self._listeners[event]:
            print(f"触发事件 {event}到: {listener}")  # 调试日志
            class ListenerTask(QRunnable):
                def __init__(self, listener, data, logger):
                    super().__init__()
                    self.listener = listener
                    self.data = data
                    self.logger = logger

                def run(self):
                    from PyQt6.QtCore import QTimer
                    def execute_in_main_thread():
                        print("进入主线程执行")  # 调试日志
                        try:
                            print(f"在主线程执行处理函数: {self.listener}")  # 调试日志
                            if self.data:
                                print(f"传入数据: {self.data}")  # 调试日志
                                self.listener(self.data)
                            else:
                                print("无法数据执行")  # 调试日志
                                self.listener()
                            print(f"事件处理函数 {self.listener} 成功在主线程内执行")  # 调试日志
                        except Exception as e:
                            print(f"执行事件处理函数出错 : {str(e)}")  # 调试日志
                            self.logger.error(f"执行事件处理函数出错: {str(e)}")
                            self.logger.debug(traceback.format_exc())
                    print(f"事件处理函数 {self.listener} 队列中")  # 调试日志
                    QTimer.singleShot(0, execute_in_main_thread)
                    print(f"事件处理函数 {self.listener} 进入主线程")  # 调试日志
                    print(f"QTimer.singleShot 调用事件处理函数 {self.listener}")  # 调试日志

            task = ListenerTask(listener, data, self._logger)
            self._thread_pool.start(task)

            # 设置超时检查
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self._check_timeout(task, event))
            timer.start(self._timeout)

    def _check_timeout(self, task: QRunnable, event: str) -> None:
        """检查任务是否超时"""
        if not task.isFinished():
            self._logger.warning(f"事件 {event} 处理超时 {self._timeout}ms")

    def clear(self, event: str = None) -> None:
        """
        清除事件监听器
        
        Args:
            event: 事件名称，如果为None则清除所有事件
        """
        if event:
            self._listeners[event].clear()
            self._logger.debug(f"Cleared listeners for event: {event}")
        else:
            self._listeners.clear()
            self._logger.debug("Cleared all event listeners")

    def shutdown(self) -> None:
        """关闭事件总线，释放资源"""
        self._thread_pool.waitForDone()
        self._logger.debug("EventBus shutdown completed")
