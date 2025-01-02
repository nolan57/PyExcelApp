from ..interfaces.health_check_plugin import HealthCheckPlugin
from ..core.event_bus import EventBus
import requests
from typing import Dict
from ..config import settings

class VersionChecker(HealthCheckPlugin):
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.base_url = settings.get('version_checker.base_url')
        self.timeout = settings.get('version_checker.timeout', 5)
        self.last_error = None

    def check(self) -> Dict:
        """检查依赖版本"""
        try:
            response = requests.get(
                f"{self.base_url}/versions",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.last_error = str(e)
            self.event_bus.publish('version_check_failed', {'error': str(e)})
            raise

    def get_status(self) -> Dict:
        return {
            'base_url': self.base_url,
            'timeout': self.timeout,
            'last_error': self.last_error
        }

    def configure(self, config: Dict):
        if 'base_url' in config:
            self.base_url = config['base_url']
        if 'timeout' in config:
            self.timeout = config['timeout']
