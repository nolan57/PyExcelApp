from typing import Optional, Any, Dict
from dataclasses import dataclass, field
from threading import Lock
from utils.event_bus import EventBus
from PyQt6.QtWidgets import QTabWidget

@dataclass
class WorkbookState:
    workbook: Optional[Any] = None
    activate_sheet: Optional[Any] = None
    sheet_names: list = field(default_factory=list)
    tab_widget: Optional[QTabWidget] = None
    file_path: Optional[str] = None

@dataclass
class Settings:
    python_path: Optional[str] = None

class GlobalState:
    _instance = None
    _lock: Lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GlobalState, cls).__new__(cls)
                cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the global state."""
        self._workbook = WorkbookState()
        self._settings = Settings()
        self._event_bus = EventBus()
        self._current_table_view = None

    @property
    def event_bus(self) -> EventBus:
        """Get the event bus instance."""
        return self._event_bus

    @property
    def workbook(self) -> WorkbookState:
        """Get the workbook state."""
        return self._workbook

    @workbook.setter
    def workbook(self, value: WorkbookState):
        """Set the workbook state and notify listeners."""
        self._workbook = value
        self._event_bus.publish("workbook_updated", value)

    @property
    def settings(self) -> Settings:
        """Get the settings."""
        return self._settings

    @settings.setter
    def settings(self, value: Settings):
        """Set the settings and notify listeners."""
        self._settings = value
        self._event_bus.publish("settings_updated", value)

    def set_current_table_view(self, table_view):
        """Set the current table view and notify listeners."""
        self._current_table_view = table_view
        self._event_bus.publish("table_view_updated", table_view)

    def get_current_table_view(self):
        """Get the current table view."""
        return self._current_table_view

    def reset(self):
        """Reset the global state to its initial values."""
        self._initialize()
        self._event_bus.publish("state_reset")