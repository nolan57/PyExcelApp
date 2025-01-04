from ..interfaces.health_check_plugin import HealthCheckPlugin
from ..core.event_bus import EventBus
import requests
from typing import Dict
from ..config import settings
import aiohttp

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

    async def check_async(self) -> Dict:
        """异步检查版本"""
        try:
            async with aiohttp.ClientSession() as session:
                async with await session.get(
                    f"{self.base_url}/versions",
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, dict) and 'status' in data:
                            return data
                        return {'status': 'error', 'error': 'Invalid response format'}
                    return {'status': 'error', 'error': f'HTTP {response.status}'}
        except Exception as e:
            if self.event_bus:
                self.event_bus.emit('version_check_error', {'error': str(e)})
            return {'status': 'error', 'error': str(e)}
