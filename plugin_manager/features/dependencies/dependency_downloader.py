import os
import sys
import logging
import subprocess
from typing import Dict, List, Optional
from plugin_manager.utils.plugin_error import PluginError

class DependencyDownloader:
    """依赖下载器"""
    
    def __init__(self, cache_dir: str = "plugin_dependencies"):
        self.cache_dir = cache_dir
        self._logger = logging.getLogger(__name__)
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def download_from_pypi(self, package_name: str, version: str) -> str:
        """从PyPI下载Python包"""
        target_dir = os.path.join(self.cache_dir, package_name)
        os.makedirs(target_dir, exist_ok=True)
        
        try:
            # 使用pip安装到指定目录
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                f"{package_name}=={version}",
                "--target", target_dir,
                "--disable-pip-version-check",
                "--no-warn-script-location"
            ])
            self._logger.info(f"成功从PyPI下载 {package_name}=={version}")
            return target_dir
        except subprocess.CalledProcessError as e:
            raise PluginError(f"从PyPI下载 {package_name} 失败: {str(e)}")
            
    def download_from_github(self, repo_url: str, ref: str = "main") -> str:
        """从GitHub仓库下载依赖"""
        repo_name = repo_url.split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        target_dir = os.path.join(self.cache_dir, repo_name)
        
        try:
            # 克隆或更新仓库
            if os.path.exists(target_dir):
                subprocess.check_call(["git", "-C", target_dir, "pull"])
            else:
                subprocess.check_call(["git", "clone", repo_url, target_dir])
                
            # 切换到指定分支/标签
            subprocess.check_call(["git", "-C", target_dir, "checkout", ref])
            self._logger.info(f"成功从GitHub下载 {repo_url}@{ref}")
            return target_dir
        except subprocess.CalledProcessError as e:
            raise PluginError(f"从GitHub下载 {repo_url} 失败: {str(e)}")
            
    def download_from_url(self, url: str, filename: str) -> str:
        """从URL下载文件"""
        target_dir = os.path.join(self.cache_dir, "files")
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, filename)
        
        try:
            # 使用curl或wget下载文件
            if sys.platform == "win32":
                subprocess.check_call(["curl", "-o", file_path, url])
            else:
                subprocess.check_call(["wget", "-O", file_path, url])
            self._logger.info(f"成功从URL下载 {filename}")
            return file_path
        except subprocess.CalledProcessError as e:
            raise PluginError(f"从URL下载 {filename} 失败: {str(e)}")
            
    def download_custom(self, handler: callable, *args, **kwargs) -> str:
        """使用自定义处理器下载依赖"""
        if not callable(handler):
            raise PluginError("下载处理器必须是可调用对象")
            
        try:
            result = handler(*args, **kwargs)
            self._logger.info("自定义下载处理器执行成功")
            return result
        except Exception as e:
            raise PluginError(f"自定义下载处理器执行失败: {str(e)}")
            
    def verify_dependency(self, dependency_path: str, checksum: Optional[str] = None) -> bool:
        """验证下载的依赖完整性"""
        if not os.path.exists(dependency_path):
            return False
        
        if checksum:
            import hashlib
            with open(dependency_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash == checksum
        
        return True
