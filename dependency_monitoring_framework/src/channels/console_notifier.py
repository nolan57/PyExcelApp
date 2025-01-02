from ..interfaces.notification_channel import NotificationChannel
from typing import Dict, Optional

class ConsoleNotifier(NotificationChannel):
    def __init__(self):
        self.last_error = None

    def notify(self, message: str):
        """Print notification to console"""
        try:
            print(message)
        except Exception as e:
            self.last_error = str(e)
            raise

    def get_status(self) -> Dict:
        return {
            'last_error': self.last_error
        }

    def configure(self, config: Dict):
        pass  # No configuration needed for console output

    def test_connection(self) -> bool:
        return True  # Console is always available

    def get_last_error(self) -> Optional[str]:
        return self.last_error
