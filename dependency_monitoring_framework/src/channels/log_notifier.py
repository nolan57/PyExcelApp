from ..interfaces.notification_channel import NotificationChannel
import logging
from typing import Optional

class LogNotifier(NotificationChannel):
    def __init__(self):
        self.logger = logging.getLogger('dependency_monitoring')
        self.last_error = None

    def notify(self, title: str, message: str, level: str = 'info'):
        """Log notification message"""
        try:
            log_level = getattr(logging, level.upper(), logging.INFO)
            self.logger.log(log_level, f"{title}: {message}")
        except Exception as e:
            self.last_error = str(e)
            raise

    def get_status(self) -> Dict:
        return {
            'log_level': self.logger.level,
            'last_error': self.last_error
        }

    def configure(self, config: Dict):
        if 'log_level' in config:
            self.logger.setLevel(config['log_level'])

    def test_connection(self) -> bool:
        return True  # Logging is always available

    def get_last_error(self) -> Optional[str]:
        return self.last_error
