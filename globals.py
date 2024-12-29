from typing import Optional, Dict, Any
from dataclasses import dataclass
from utils.event_bus import EventBus
from PyQt6.QtWidgets import QTabWidget

@dataclass
class WorkbookState:
    workbook: Optional[Any] = None
    activate_sheet: Optional[Any] = None
    sheet_names: list = None
    tab_widget: Optional[QTabWidget] = None
    file_path: Optional[str] = None

class Settings:
    python_path: str = "/Volumes/TOSHIBAEXT/opt/anaconda3/envs/PyQt/bin/python"

class GlobalState:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalState, cls).__new__(cls)
            cls._instance = super().__new__(cls)
            cls._instance.workbook = WorkbookState()
            cls._instance.settings = Settings()
            cls._instance._event_bus = EventBus()
            cls._instance.current_table_view = None
        return cls._instance

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def workbook(self) -> WorkbookState:
        return self._workbook

    @workbook.setter
    def workbook(self, value: WorkbookState):
        self._workbook = value

    @property
    def settings(self) -> Settings:
        return self._settings

    @settings.setter
    def settings(self, value: Settings):
        self._settings = value

    def set_current_table_view(self, table_view):
        """设置当前活动的表格视图"""
        self.current_table_view = table_view

    def get_current_table_view(self):
        """获取当前活动的表格视图"""
        return self.current_table_view

# 使用示例：
# state = GlobalState()
# state.workbook.file_path = "example.xlsx"
