from typing import Dict, List, Any, Callable
from abc import ABC, abstractmethod

class EventBus:
    """事件总线"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """订阅事件"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """取消订阅"""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)
            
    def emit(self, event_type: str, data: Any = None, source: str = None) -> None:
        """触发事件"""
        if event_type in self._subscribers:
            event_data = {
                'type': event_type,
                'data': data,
                'source': source
            }
            for handler in self._subscribers[event_type]:
                handler(event_data)

class PluginEventInterface(ABC):
    """插件事件接口"""
    
    @abstractmethod
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """注册事件处理器"""
        pass
        
    @abstractmethod
    def unregister_event_handler(self, event_type: str, handler: Callable) -> None:
        """注销事件处理器"""
        pass
        
    @abstractmethod
    def emit_event(self, event_type: str, data: Any = None) -> None:
        """发送事件"""
        pass 