from typing import Dict, List, Callable, Any
from collections import defaultdict

class EventBus:
    """事件总线，用于处理系统内的事件发布和订阅"""
    
    def __init__(self):
        self._subscribers = defaultdict(list)
        self._last_events = {}

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数，接收事件数据作为参数
        """
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """取消订阅事件
        
        Args:
            event_type: 事件类型
            callback: 要取消的回调函数
        """
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]

    def publish(self, event_type: str, data: Any = None) -> None:
        """发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        self._last_events[event_type] = data
        for callback in self._subscribers[event_type]:
            try:
                callback(data)
            except Exception as e:
                print(f"Error in event handler: {str(e)}")

    def get_last_event(self, event_type: str) -> Any:
        """获取最后一次事件数据
        
        Args:
            event_type: 事件类型
            
        Returns:
            最后一次事件的数据，如果没有则返回None
        """
        return self._last_events.get(event_type)

    def clear_subscribers(self, event_type: str = None) -> None:
        """清除订阅者
        
        Args:
            event_type: 要清除的事件类型，如果为None则清除所有
        """
        if event_type:
            if event_type in self._subscribers:
                del self._subscribers[event_type]
        else:
            self._subscribers.clear()

    def get_subscriber_count(self, event_type: str) -> int:
        """获取订阅者数量
        
        Args:
            event_type: 事件类型
            
        Returns:
            订阅者数量
        """
        return len(self._subscribers.get(event_type, []))

    def get_all_event_types(self) -> List[str]:
        """获取所有事件类型
        
        Returns:
            事件类型列表
        """
        return list(self._subscribers.keys())
