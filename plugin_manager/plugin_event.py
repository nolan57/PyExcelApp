from dataclasses import dataclass
from typing import Any, Dict, Callable

@dataclass
class PluginEvent:
    type: str
    source: str
    data: Dict[str, Any]
    
class PluginEventBus:
    def subscribe(self, event_type: str, callback: Callable):
        pass
        
    def publish(self, event: PluginEvent):
        pass 