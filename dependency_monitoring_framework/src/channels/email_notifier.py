from ..interfaces.notification_channel import NotificationChannel
import smtplib
from email.mime.text import MIMEText
from typing import Dict, Optional
from ..config import settings

class EmailNotifier(NotificationChannel):
    def __init__(self):
        self.smtp_server = settings.get('email.smtp_server')
        self.smtp_port = settings.get('email.smtp_port', 587)
        self.smtp_user = settings.get('email.smtp_user')
        self.smtp_password = settings.get('email.smtp_password')
        self.from_email = settings.get('email.from_email')
        self.to_email = settings.get('email.to_email')
        self.timeout = settings.get('email.timeout', 5)
        self.last_error = None

    def notify(self, title: str, message: str, level: str = 'info') -> None:
        """发送邮件通知"""
        try:
            msg = MIMEText(message)
            msg['Subject'] = f"[{level.upper()}] {title}"
            msg['From'] = self.from_email
            msg['To'] = self.to_email

            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.timeout) as server:
                server.ehlo()  # 可选的 EHLO 命令
                server.starttls()  # 启用 TLS
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
        except Exception as e:
            self.last_error = str(e)
            raise

    def get_status(self) -> Dict:
        return {
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port,
            'from_email': self.from_email,
            'to_email': self.to_email,
            'timeout': self.timeout,
            'last_error': self.last_error
        }

    def configure(self, config: Dict):
        if 'smtp_server' in config:
            self.smtp_server = config['smtp_server']
        if 'smtp_port' in config:
            self.smtp_port = config['smtp_port']
        if 'smtp_user' in config:
            self.smtp_user = config['smtp_user']
        if 'smtp_password' in config:
            self.smtp_password = config['smtp_password']
        if 'from_email' in config:
            self.from_email = config['from_email']
        if 'to_email' in config:
            self.to_email = config['to_email']
        if 'timeout' in config:
            self.timeout = config['timeout']

    def test_connection(self) -> bool:
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.timeout) as server:
                server.ehlo()
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    def get_last_error(self) -> Optional[str]:
        return self.last_error
