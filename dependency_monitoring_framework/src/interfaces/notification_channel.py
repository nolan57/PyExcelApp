"""Notification channel interface definition.

This module defines the NotificationChannel abstract base class that all
notification channel implementations must follow.
"""

from typing import Dict, Optional, Any
from abc import ABC, abstractmethod

class NotificationChannel(ABC):
    """Abstract base class defining the interface for notification channels.
    
    This class defines the required methods that all notification channel
    implementations must provide, including sending notifications, getting
    status, and handling configuration.
    """
    @abstractmethod
    def notify(self, title: str, message: str, level: str = 'info') -> None:
        """Send a notification through this channel.
        
        Args:
            title (str): The title/heading of the notification
            message (str): The main content of the notification
            level (str): Severity level ('info', 'warning', 'error')
        """
        raise NotImplementedError

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the notification channel.
        
        Returns:
            Dict[str, Any]: A dictionary containing status information
        """
        raise NotImplementedError

    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the notification channel with new settings.
        
        Args:
            config (Dict[str, Any]): Configuration parameters
        """
        raise NotImplementedError

    @abstractmethod
    def test_connection(self) -> bool:
        """Test the connection to the notification service.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def get_last_error(self) -> Optional[str]:
        """Get the last error message that occurred.
        
        Returns:
            Optional[str]: The error message if available, None otherwise
        """
        raise NotImplementedError
