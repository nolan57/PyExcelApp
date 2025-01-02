import os
import subprocess
from pathlib import Path
from typing import Optional

class VirtualEnvManager:
    """管理插件的虚拟环境"""

    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        self.env_path = self._get_env_path()

    def _get_env_path(self) -> Path:
        """获取虚拟环境路径"""
        return Path(f"plugin_manager/plugins/{self.plugin_name}/.venv")

    def create(self) -> bool:
        """创建虚拟环境"""
        if self.env_path.exists():
            return True
            
        try:
            subprocess.run([sys.executable, "-m", "venv", str(self.env_path)], check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def activate(self) -> bool:
        """激活虚拟环境"""
        if not self.env_path.exists():
            return False
            
        # 设置虚拟环境的Python路径
        os.environ["VIRTUAL_ENV"] = str(self.env_path)
        os.environ["PATH"] = f"{self.env_path}/bin:{os.environ['PATH']}"
        return True

    def install_dependencies(self, requirements: str) -> bool:
        """安装依赖"""
        if not self.env_path.exists():
            return False
            
        try:
            subprocess.run(
                [f"{self.env_path}/bin/pip", "install", "-r", requirements],
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def cleanup(self) -> bool:
        """清理虚拟环境"""
        if not self.env_path.exists():
            return True
            
        try:
            subprocess.run(["rm", "-rf", str(self.env_path)], check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def is_active(self) -> bool:
        """检查虚拟环境是否激活"""
        return "VIRTUAL_ENV" in os.environ and Path(os.environ["VIRTUAL_ENV"]) == self.env_path
