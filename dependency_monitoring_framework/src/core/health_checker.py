from typing import Dict, List
from ..interfaces.health_check_plugin import HealthCheckPlugin
from ..core.event_bus import EventBus
from ..config import settings

class HealthChecker:
    def __init__(self, event_bus: EventBus):
        self.plugins: List[HealthCheckPlugin] = []
        self.event_bus = event_bus
        self._load_plugins()

    def _load_plugins(self):
        """Load configured health check plugins"""
        plugin_configs = settings.get('health_check_plugins', [])
        for config in plugin_configs:
            try:
                plugin_class = self._get_plugin_class(config['type'])
                plugin = plugin_class(self.event_bus)
                plugin.configure(config.get('config', {}))
                self.plugins.append(plugin)
            except Exception as e:
                print(f"Failed to load health check plugin {config['type']}: {str(e)}")

    def _get_plugin_class(self, plugin_type: str):
        """Get health check plugin class by type"""
        if plugin_type == 'version':
            from ..services.version_checker import VersionChecker
            return VersionChecker
        elif plugin_type == 'security':
            from ..services.security_scanner import SecurityScanner
            return SecurityScanner
        elif plugin_type == 'compatibility':
            from ..services.compatibility_checker import CompatibilityChecker
            return CompatibilityChecker
        elif plugin_type == 'integrity':
            from ..services.integrity_verifier import IntegrityVerifier
            return IntegrityVerifier
        else:
            raise ValueError(f"Unknown health check plugin type: {plugin_type}")

    def check_version(self, package_name: str, version: str) -> bool:
        """Check package version"""
        version_checker = next(
            (p for p in self.plugins if isinstance(p, VersionChecker)), None
        )
        if version_checker:
            return version_checker.check(package_name, version)
        return False

    def scan_security(self, package_name: str) -> bool:
        """Scan package for security vulnerabilities"""
        security_scanner = next(
            (p for p in self.plugins if isinstance(p, SecurityScanner)), None
        )
        if security_scanner:
            return security_scanner.scan(package_name)
        return False

    def run_checks(self) -> Dict[str, Dict]:
        """Run all health checks"""
        results = {}
        for plugin in self.plugins:
            try:
                plugin_results = plugin.check()
                results.update(plugin_results)
            except Exception as e:
                print(f"Failed to run health check: {str(e)}")
        return results

    def get_status(self) -> Dict[str, Dict]:
        """Get status of all health check plugins"""
        return {
            'plugins': [plugin.get_status() for plugin in self.plugins]
        }
