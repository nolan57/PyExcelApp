"""Unit tests for dependency monitoring framework."""

import unittest
from unittest.mock import MagicMock, patch
from dependency_monitoring_framework.src.core.event_bus import EventBus
from dependency_monitoring_framework.src.services.version_checker import VersionChecker
from dependency_monitoring_framework.src.services.security_scanner import SecurityScanner
from dependency_monitoring_framework.src.services.compatibility_checker import CompatibilityChecker
from dependency_monitoring_framework.src.channels.email_notifier import EmailNotifier
from dependency_monitoring_framework.src.channels.slack_notifier import SlackNotifier

class TestHealthChecker(unittest.TestCase):
    @patch('requests.get')
    def test_check_version(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'status': 'up_to_date'}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        event_bus = EventBus()
        checker = VersionChecker(event_bus)
        result = checker.check()
        self.assertEqual(result['status'], 'up_to_date')

    @patch('requests.get')
    def test_scan_security(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'vulnerabilities': []}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        event_bus = EventBus()
        scanner = SecurityScanner(event_bus)
        result = scanner.check()
        self.assertEqual(result['vulnerabilities'], [])

class TestNotifiers(unittest.TestCase):
    @patch('smtplib.SMTP')
    def test_email_notifier(self, mock_smtp):
        notifier = EmailNotifier()
        notifier.configure({
            'smtp_server': 'test.smtp.com',
            'smtp_port': 587,
            'smtp_user': 'test',
            'smtp_password': 'test',
            'from_email': 'from@test.com',
            'to_email': 'to@test.com'
        })
        notifier.notify('Test', 'Test message')
        mock_smtp.assert_called()

    @patch('requests.post')
    def test_slack_notifier(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        notifier = SlackNotifier()
        notifier.configure({
            'webhook_url': 'https://hooks.slack.com/test',
            'channel': '#test'
        })
        notifier.notify('Test', 'Test message')
        mock_post.assert_called()

class TestServices(unittest.TestCase):
    @patch('requests.get')
    def test_version_checker(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'versions': ['1.0.0', '1.1.0']}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        event_bus = EventBus()
        checker = VersionChecker(event_bus)
        result = checker.check()
        self.assertIn('versions', result)

    @patch('requests.get')
    def test_security_scanner(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'vulnerabilities': []}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        event_bus = EventBus()
        scanner = SecurityScanner(event_bus)
        result = scanner.check()
        self.assertIn('vulnerabilities', result)

    @patch('requests.get')
    def test_compatibility_checker(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'compatible': True}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        event_bus = EventBus()
        checker = CompatibilityChecker(event_bus)
        result = checker.check()
        self.assertIn('compatible', result)

if __name__ == '__main__':
    unittest.main()
