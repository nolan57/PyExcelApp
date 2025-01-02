from ..interfaces.notification_channel import NotificationChannel
import requests
from typing import Optional
from ..config import settings

class ApiNotifier(NotificationChannel):
    def __init__(self):
        self.api_url = settings.get('api_notifier.url')
        self.api_key = settings.get('api_notifier.api_key')
        self.timeout = settings.get('api_notifier.timeout', 5)
        self.last_error = None

    def notify(self, title: str, message: str, level: str = 'info'):
        """Send notification via API"""
        try:
            payload = {
                'title': title,
                'message': message,
                'level': level
            }
            headers = {
                'Authorization': f"Bearer {self.api_key}",
                'Content-Type': 'application/json'
            }
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
        except Exception as e:
            self.last_error = str(e)
            raise

    def get_status(self) -> Dict:
        return {
            'api_url': self.api_url,
            'timeout': self.timeout,
            'last_error': self.last_error
        }

    def configure(self, config: Dict):
        if 'api_url' in config:
            self.api_url = config['api_url']
        if 'api_key' in config:
            self.api_key = config['api_key']
        if 'timeout' in config:
            self.timeout = config['timeout']

    def test_connection(self) -> bool:
        try:
            response = requests.get(
                self.api_url,
                headers={'Authorization': f"Bearer {self.api_key}"},
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception as e:
            self.last_error = str(e)
            return False

    def get_last_error(self) -> Optional[str]:
        return self.last_error
