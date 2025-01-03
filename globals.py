from typing import Optional, Any, Dict
from dataclasses import dataclass, field
from threading import Lock
from utils.event_bus import EventBus
from PyQt6.QtWidgets import QTabWidget

@dataclass
class WorkbookState:
    workbook: Optional[Any] = None  # 当前的工作簿对象
    activate_sheet: Optional[Any] = None  # 当前激活的工作表
    sheet_names: list = field(default_factory=list)  # 工作簿中所有工作表的名称列表
    tab_widget: Optional[QTabWidget] = None  # 用于显示工作表的选项卡控件
    file_path: Optional[str] = None  # 工作簿文件的路径

@dataclass
class Settings:
    python_path: Optional[str] = None  # Python 解释器的路径

class GlobalState:
    _instance = None
    _lock: Lock = Lock()  # 用于线程安全的锁

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GlobalState, cls).__new__(cls)
                cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化全局状态"""
        self._workbook = WorkbookState()
        self._settings = Settings()
        self._event_bus = EventBus()
        self._current_table_view = None

    @property
    def event_bus(self) -> EventBus:
        """获取事件总线实例"""
        return self._event_bus
    @event_bus.setter
    def event_bus(self, value: EventBus):
        """设置事件总线实例"""
        self._event_bus = value

    @property
    def workbook(self) -> WorkbookState:
        """获取工作簿状态"""
        return self._workbook

    @workbook.setter
    def workbook(self, value: WorkbookState):
        """设置工作簿状态并通知监听器"""
        self._workbook = value
        self._event_bus.publish("workbook_updated", value)

    @property
    def settings(self) -> Settings:
        """获取设置"""
        return self._settings

    @settings.setter
    def settings(self, value: Settings):
        """设置设置并通知监听器"""
        self._settings = value
        self._event_bus.publish("settings_updated", value)

    def set_current_table_view(self, table_view):
        """设置当前表格视图并通知监听器"""
        self._current_table_view = table_view
        self._event_bus.publish("table_view_updated", table_view)

    def get_current_table_view(self):
        """获取当前表格视图"""
        return self._current_table_view

    def reset(self):
        """重置全局状态到初始值"""
        self._initialize()
        self._event_bus.publish("state_reset")