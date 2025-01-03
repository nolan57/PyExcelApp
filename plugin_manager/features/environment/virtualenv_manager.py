import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict
import logging
import sys

class VirtualEnvManager:
    """管理插件的虚拟环境"""

    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        self.env_path = self._get_env_path()
        self._logger = logging.getLogger(__name__)
        self._is_active = False

    def _get_env_path(self) -> Path:
        """获取虚拟环境路径"""
        return Path(f"plugin_manager/plugins/{self.plugin_name}/.venv")

    def _get_python_executable(self) -> str:
        """获取虚拟环境的Python解释器路径"""
        if os.name == 'nt':  # Windows
            return str(self.env_path / 'Scripts' / 'python.exe')
        return str(self.env_path / 'bin' / 'python')

    def _get_pip_executable(self) -> str:
        """获取虚拟环境的pip路径"""
        if os.name == 'nt':  # Windows
            return str(self.env_path / 'Scripts' / 'pip.exe')
        return str(self.env_path / 'bin' / 'pip')

    def create(self) -> bool:
        """创建虚拟环境"""
        if self.env_path.exists():
            self._logger.info(f"虚拟环境已存在: {self.env_path}")
            return True
            
        try:
            self._logger.info(f"创建虚拟环境: {self.env_path}")
            subprocess.run([sys.executable, "-m", "venv", str(self.env_path)], check=True)
            return True
        except subprocess.CalledProcessError:
            self._logger.error(f"创建虚拟环境失败: {self.env_path}")
            return False

    def activate(self) -> bool:
        """激活虚拟环境"""
        if not self.env_path.exists():
            self._logger.error(f"虚拟环境不存在: {self.env_path}")
            return False
            
        # 设置虚拟环境的Python路径
        os.environ["VIRTUAL_ENV"] = str(self.env_path)
        if os.name == 'nt':  # Windows
            os.environ["PATH"] = f"{self.env_path}\\Scripts;{os.environ['PATH']}"
        else:  # Unix/Linux
            os.environ["PATH"] = f"{self.env_path}/bin:{os.environ['PATH']}"
        
        self._is_active = True
        self._logger.info(f"已激活虚拟环境: {self.env_path}")
        return True

    def install_dependencies(self, requirements: str) -> bool:
        """安装依赖"""
        if not self.env_path.exists():
            self._logger.error(f"虚拟环境不存在: {self.env_path}")
            return False
            
        try:
            self._logger.info(f"安装依赖: {requirements}")
            subprocess.run(
                [self._get_pip_executable(), "install", "-r", requirements],
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            self._logger.error(f"安装依赖失败: {requirements}")
            return False

    def cleanup(self) -> bool:
        """清理虚拟环境"""
        if not self.env_path.exists():
            return True
            
        try:
            self._logger.info(f"清理虚拟环境: {self.env_path}")
            if os.name == 'nt':  # Windows
                subprocess.run(["rmdir", "/s", "/q", str(self.env_path)], check=True)
            else:  # Unix/Linux
                subprocess.run(["rm", "-rf", str(self.env_path)], check=True)
            self._is_active = False
            return True
        except subprocess.CalledProcessError:
            self._logger.error(f"清理虚拟环境失败: {self.env_path}")
            return False

    def is_active(self) -> bool:
        """检查虚拟环境是否激活"""
        return self._is_active
