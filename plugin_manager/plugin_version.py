from dataclasses import dataclass
from semver import VersionInfo

@dataclass
class PluginVersion:
    version: VersionInfo
    min_system_version: VersionInfo
    dependencies: Dict[str, VersionInfo]
    
class PluginVersionManager:
    def check_compatibility(self, plugin_version: PluginVersion) -> bool:
        pass 