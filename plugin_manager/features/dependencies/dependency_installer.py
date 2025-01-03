import os
import subprocess
from typing import List, Dict, Optional
import logging
from ..plugin_permissions import PluginPermission
from ...utils.plugin_error import PluginError
from ...utils.dependency_downloader import DependencyDownloader
from ..features.dependencies.plugin_dependencies import DependencySecurity

class DependencyInstaller:
    """依赖安装器"""
    
    def __init__(self, plugin_dir: str):
        self.plugin_dir = plugin_dir
        self.logger = logging.getLogger(__name__)
        self.downloader = DependencyDownloader()
        
    def install_dependencies(self, plugin_name: str, dependencies: List[str],
                           trusted_sources: Optional[List[str]] = None) -> bool:
        """安装插件依赖"""
        try:
            # 先下载所有依赖
            downloaded_packages = []
            for dep in dependencies:
                package_path = self.downloader.download_dependency(
                    name=dep,
                    version="latest",  # 或指定版本
                    source=trusted_sources[0] if trusted_sources else "https://pypi.org/simple"
                )
                downloaded_packages.append(package_path)
                
            # 然后安装下载的包
            venv_path = os.path.join(self.plugin_dir, plugin_name, "venv")
            if not os.path.exists(venv_path):
                subprocess.run(["python", "-m", "venv", venv_path], check=True)
                
            pip_cmd = [
                os.path.join(venv_path, "bin", "pip"),
                "install"
            ]
            pip_cmd.extend(downloaded_packages)
            
            subprocess.run(pip_cmd, check=True)
            return True
            
        except Exception as e:
            self.logger.error(f"安装依赖失败: {str(e)}")
            raise 