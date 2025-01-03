from dependency_monitoring_framework.src.core.event_bus import EventBus as MonitorEventBus
from typing import Callable, Any
import asyncio

class EventBus:
    """事件总线适配器，统一接口"""
    
    def __init__(self):
        self._monitor_bus = MonitorEventBus()
        self._loop = asyncio.get_event_loop()
        
    def emit(self, event_type: str, data: Any = None, source: str = None):
        """兼容旧的同步 emit 接口"""
        asyncio.run_coroutine_threadsafe(
            self._monitor_bus.publish(event_type, data),
            self._loop
        )
        
    def subscribe(self, event_type: str, handler: Callable):
        """兼容旧的订阅接口"""
        self._monitor_bus.subscribe(event_type, handler)
        
    def unsubscribe(self, event_type: str, handler: Callable):
        """兼容旧的取消订阅接口"""
        self._monitor_bus.unsubscribe(event_type, handler) 