from typing import Dict, List
from ..interfaces.notification_channel import NotificationChannel
from ..config import settings

class NotificationManager:
    def __init__(self):
        self.notifiers: List[NotificationChannel] = []
        self._load_channels()

    def add_notifier(self, notifier: NotificationChannel):
        """Add a notification channel"""
        self.notifiers.append(notifier)

    def _load_channels(self):
        """Load configured notification channels"""
        channel_configs = settings.get('notification_channels', [])
        for config in channel_configs:
            try:
                channel_class = self._get_channel_class(config['type'])
                channel = channel_class()
                channel.configure(config.get('config', {}))
                self.notifiers.append(channel)
            except Exception as e:
                print(f"Failed to load notification channel {config['type']}: {str(e)}")

    def _get_channel_class(self, channel_type: str):
        """Get notification channel class by type"""
        if channel_type == 'email':
            from ..channels.email_notifier import EmailNotifier
            return EmailNotifier
        elif channel_type == 'slack':
            from ..channels.slack_notifier import SlackNotifier
            return SlackNotifier
        elif channel_type == 'console':
            from ..channels.console_notifier import ConsoleNotifier
            return ConsoleNotifier
        elif channel_type == 'log':
            from ..channels.log_notifier import LogNotifier
            return LogNotifier
        elif channel_type == 'api':
            from ..channels.api_notifier import ApiNotifier
            return ApiNotifier
        else:
            raise ValueError(f"Unknown notification channel type: {channel_type}")

    def notify_all(self, message: str):
        """Send notification through all channels"""
        for notifier in self.notifiers:
            try:
                notifier.notify(message)
            except Exception as e:
                print(f"Failed to send notification through channel: {str(e)}")

    def get_status(self) -> Dict[str, Dict]:
        """Get status of all notification channels"""
        return {
            'notifiers': [notifier.get_status() for notifier in self.notifiers]
        }
