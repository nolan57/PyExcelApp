import os
import logging
import requests
import hashlib
import subprocess
from typing import List, Optional, Dict
from pathlib import Path
from dataclasses import dataclass
from .plugin_dependencies import PluginDependency
from ...utils.plugin_error import PluginError

@dataclass
class DownloadResult:
    """下载结果"""
    success: bool
    path: Optional[str] = None
    error: Optional[str] = None

class DependencyDownloader:
    """依赖下载器"""
    
    def __init__(self, cache_dir: str = "plugin_manager/dependencies/cache"):
        self._logger = logging.getLogger(__name__)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._download_cache: Dict[str, str] = {}  # 包名 -> 缓存路径
        
    def download(self, dependency: PluginDependency) -> DownloadResult:
        """下载单个依赖
        
        Args:
            dependency: 依赖信息
            
        Returns:
            DownloadResult: 下载结果
        """
        try:
            # 1. 检查缓存
            cache_key = f"{dependency.name}-{dependency.version}"
            if cache_key in self._download_cache:
                self._logger.info(f"使用缓存的依赖: {cache_key}")
                return DownloadResult(True, self._download_cache[cache_key])
                
            # 2. 构建下载URL
            if dependency.source:
                download_url = dependency.source
            else:
                # 默认使用PyPI
                download_url = f"https://pypi.org/simple/{dependency.name}"
                
            # 3. 下载依赖
            self._logger.info(f"开始下载依赖: {dependency.name}")
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            # 4. 保存文件
            file_path = self.cache_dir / f"{cache_key}.whl"
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            # 5. 验证签名（如果有）
            if dependency.signature:
                if not self._verify_signature(file_path, dependency.signature):
                    os.remove(file_path)
                    return DownloadResult(False, error="签名验证失败")
                    
            # 6. 更新缓存
            self._download_cache[cache_key] = str(file_path)
            self._logger.info(f"依赖下载完成: {dependency.name}")
            
            return DownloadResult(True, str(file_path))
            
        except requests.RequestException as e:
            error_msg = f"下载依赖 {dependency.name} 失败: {str(e)}"
            self._logger.error(error_msg)
            return DownloadResult(False, error=error_msg)
        except Exception as e:
            error_msg = f"处理依赖 {dependency.name} 时出错: {str(e)}"
            self._logger.error(error_msg)
            return DownloadResult(False, error=error_msg)
            
    def download_many(self, dependencies: List[PluginDependency]) -> Dict[str, DownloadResult]:
        """批量下载依赖
        
        Args:
            dependencies: 依赖列表
            
        Returns:
            Dict[str, DownloadResult]: 依赖名称到下载结果的映射
        """
        results = {}
        for dep in dependencies:
            results[dep.name] = self.download(dep)
        return results
        
    def _verify_signature(self, file_path: Path, signature: str) -> bool:
        """验证文件签名
        
        Args:
            file_path: 文件路径
            signature: 期望的签名
            
        Returns:
            bool: 签名是否有效
        """
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash == signature
        except Exception as e:
            self._logger.error(f"验证签名时出错: {str(e)}")
            return False
            
    def clear_cache(self, days: int = 30) -> None:
        """清理指定天数前的缓存
        
        Args:
            days: 保留最近几天的缓存
        """
        try:
            import time
            now = time.time()
            for file_path in self.cache_dir.glob("*.whl"):
                if (now - file_path.stat().st_mtime) > (days * 86400):
                    os.remove(file_path)
                    # 从缓存字典中移除
                    self._download_cache = {
                        k: v for k, v in self._download_cache.items()
                        if v != str(file_path)
                    }
        except Exception as e:
            self._logger.error(f"清理缓存时出错: {str(e)}")
            
    def get_cached_path(self, dependency_name: str, version: str) -> Optional[str]:
        """获取依赖的缓存路径
        
        Args:
            dependency_name: 依赖名称
            version: 依赖版本
            
        Returns:
            Optional[str]: 缓存路径，如果不存在则返回None
        """
        cache_key = f"{dependency_name}-{version}"
        return self._download_cache.get(cache_key)
        
    def download_from_github(self, repo_url: str, ref: str = "main") -> str:
        """从GitHub仓库下载依赖"""
        repo_name = repo_url.split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        target_dir = self.cache_dir / repo_name
        
        try:
            # 克隆或更新仓库
            if target_dir.exists():
                subprocess.check_call(["git", "-C", str(target_dir), "pull"])
            else:
                subprocess.check_call(["git", "clone", repo_url, str(target_dir)])
                
            # 切换到指定分支/标签
            subprocess.check_call(["git", "-C", str(target_dir), "checkout", ref])
            self._logger.info(f"成功从GitHub下载 {repo_url}@{ref}")
            return str(target_dir)
        except subprocess.CalledProcessError as e:
            raise PluginError(f"从GitHub下载 {repo_url} 失败: {str(e)}")
            
    def download_from_url(self, url: str, filename: str) -> str:
        """从URL下载文件"""
        target_dir = self.cache_dir / "files"
        target_dir.mkdir(exist_ok=True)
        file_path = target_dir / filename
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            self._logger.info(f"成功从URL下载 {filename}")
            return str(file_path)
        except Exception as e:
            raise PluginError(f"从URL下载 {filename} 失败: {str(e)}")
            
    def download_custom(self, handler: callable, *args, **kwargs) -> str:
        """使用自定义处理器下载依赖
        
        Args:
            handler: 自定义下载处理函数
            args: 传递给处理函数的位置参数
            kwargs: 传递给处理函数的关键字参数
            
        Returns:
            str: 下载文件的路径
            
        Raises:
            PluginError: 下载失败时抛出
        """
        if not callable(handler):
            raise PluginError("下载处理器必须是可调用对象")
            
        try:
            result = handler(*args, **kwargs)
            self._logger.info("自定义下载处理器执行成功")
            return result
        except Exception as e:
            raise PluginError(f"自定义下载处理器执行失败: {str(e)}")
            
    def verify_dependency(self, dependency_path: str, checksum: Optional[str] = None) -> bool:
        """验证下载的依赖完整性
        
        Args:
            dependency_path: 依赖文件路径
            checksum: 期望的校验和（可选）
            
        Returns:
            bool: 验证是否通过
        """
        if not os.path.exists(dependency_path):
            return False
            
        if checksum:
            with open(dependency_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash == checksum
        
        return True
