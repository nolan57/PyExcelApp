from ..interfaces.notification_channel import NotificationChannel
import requests
from typing import Dict, Optional
from ..config import settings

class SlackNotifier(NotificationChannel):
    def __init__(self):
        self.webhook_url = settings.get('slack.webhook_url')
        self.channel = settings.get('slack.channel', '#general')
        self.username = settings.get('slack.username', 'Dependency Monitor')
        self.timeout = settings.get('slack.timeout', 5)
        self.last_error = None

    def notify(self, title: str, message: str, level: str = 'info') -> None:
        """发送Slack通知"""
        if not self.webhook_url:
            raise ValueError("Slack webhook URL not configured")

        try:
            payload = {
                'channel': self.channel,
                'username': self.username,
                'text': f"*[{level.upper()}] {title}*\n{message}",
                'icon_emoji': ':warning:'
            }
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
        except Exception as e:
            self.last_error = str(e)
            raise

    def get_status(self) -> Dict:
        return {
            'webhook_url': self.webhook_url,
            'channel': self.channel,
            'username': self.username,
            'timeout': self.timeout,
            'last_error': self.last_error
        }

    def configure(self, config: Dict):
        if 'webhook_url' in config:
            self.webhook_url = config['webhook_url']
        if 'channel' in config:
            self.channel = config['channel']
        if 'username' in config:
            self.username = config['username']
        if 'timeout' in config:
            self.timeout = config['timeout']

    def test_connection(self) -> bool:
        try:
            self.notify('Connection Test', 'Testing Slack connection')
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    def get_last_error(self) -> Optional[str]:
        return self.last_error
