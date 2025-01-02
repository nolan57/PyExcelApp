from typing import Dict
from abc import ABC, abstractmethod

class HealthCheckPlugin(ABC):
    @abstractmethod
    def check(self) -> Dict:
        """Run health check and return results"""
        pass

    @abstractmethod
    def get_status(self) -> Dict:
        """Get current status of the health check plugin"""
        pass

    @abstractmethod
    def configure(self, config: Dict):
        """Configure the health check plugin"""
        pass
