from typing import Dict, Set, List, Optional, Any, Protocol, Tuple
from dataclasses import dataclass
import logging
import sys
import importlib
import time
import os
import shutil
import hashlib
import json
from datetime import datetime, timedelta
from plugin_manager.utils.plugin_error import PluginError
from packaging import version
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from ..plugin_permissions import PluginPermission
from ...utils.plugin_error import PluginError
from ..environment.virtualenv_manager import VirtualEnvManager

@dataclass(frozen=True)
class PluginDependency:
    """插件依赖信息"""
    name: str
    version: str
    optional: bool = False
    source: str = ""        # 依赖来源
    signature: str = ""     # 依赖签名

    def __hash__(self):
        return hash((self.name, self.version, self.optional, self.source))

    def __eq__(self, other):
        return (self.name, self.version, self.optional, self.source) == \
               (other.name, other.version, other.optional, other.source)

@dataclass
class DependencyInfo:
    """依赖详细信息"""
    name: str                # 依赖包名称
    version: str            # 当前版本
    path: str               # 安装路径
    last_used: datetime     # 最后使用时间
    optional: bool = False  # 是否为可选依赖

class DependencySecurity:
    """依赖安全验证"""
    
    def __init__(self, whitelist_path: str = "plugin_dependencies/whitelist.json",
                 public_key_path: str = "plugin_dependencies/public_key.pem"):
        self.whitelist = self._load_whitelist(whitelist_path)
        self.public_key = self._load_public_key(public_key_path)
        
    def _load_whitelist(self, path: str) -> Set[str]:
        """加载全局依赖白名单"""
        if not os.path.exists(path):
            return set()
        with open(path, 'r') as f:
            return set(json.load(f))
            
    def _load_plugin_whitelist(self, plugin_dir: str) -> Set[str]:
        """加载插件的依赖白名单"""
        whitelist_path = os.path.join(plugin_dir, "dependencies_whitelist.json")
        if not os.path.exists(whitelist_path):
            return set()
            
        with open(whitelist_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("allowed_dependencies", []))
            
    def _load_public_key(self, path: str) -> Any:
        """加载公钥"""
        if not os.path.exists(path):
            return None
        with open(path, 'rb') as f:
            return load_pem_public_key(f.read())
            
    def verify_signature(self, data: bytes, signature: bytes) -> bool:
        """验证依赖签名"""
        if self.public_key is None:
            return False
        try:
            self.public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
            
    def verify_source(self, source: str) -> bool:
        """验证依赖来源"""
        # 实现来源验证逻辑
        return source.startswith("https://trusted.source/")
        
    def check_whitelist(self, dependency_name: str) -> bool:
        """检查依赖是否在白名单中"""
        return dependency_name in self.whitelist

class DependencyDownloadHandler(Protocol):
    """依赖下载处理器接口"""
    """依赖下载处理器接口"""
    
    def __call__(self, dependencies: List['PluginDependency'], target_dir: str) -> None:
        """下载依赖
        
        Args:
            dependencies: 需要下载的依赖列表
            target_dir: 下载的目标目录
        """
        ...

class DependencyManager:
    """插件依赖管理"""
    
    def __init__(self, dependencies_dir: str = "plugin_dependencies", 
                 cleanup_interval: int = 7,  # 清理间隔(天)
                 retention_period: int = 30, # 保留期限(天)
                 enable_security: bool = True,  # 是否启用安全验证
                 event_bus = None):            # 事件总线
        self._dependencies: Dict[str, Set[PluginDependency]] = {}
        self._logger = logging.getLogger(__name__)
        self.dependencies_dir = dependencies_dir
        self._environments: Dict[str, VirtualEnvManager] = {}  # 插件环境管理器
        self._cache: Dict[str, str] = {}  # 依赖缓存：{依赖名称: 缓存路径}
        self._callbacks: Dict[str, callable] = {}  # 插件回调：{插件名称: 回调函数}
        self._dependencies_info: Dict[str, DependencyInfo] = {}
        self.cleanup_interval = cleanup_interval
        self.retention_period = retention_period
        self._last_cleanup = datetime.now()
        self._security = DependencySecurity() if enable_security else None
        self._event_bus = event_bus
        os.makedirs(self.dependencies_dir, exist_ok=True)
        
    def register_callback(self, plugin_name: str, callback: callable) -> None:
        """注册下载完成回调
        
        Args:
            plugin_name: 插件名称
            callback: 回调函数，接受插件名称和下载结果作为参数
        """
        if not callable(callback):
            raise PluginError("回调必须是可调用对象")
        self._callbacks[plugin_name] = callback
        
    def set_download_handler(self, plugin_name: str, handler: callable) -> None:
        """设置插件的依赖下载处理器"""
        if not callable(handler):
            raise PluginError("下载处理器必须是可调用对象")
        if not hasattr(self, '_download_handlers'):
            self._download_handlers = {}
        self._download_handlers[plugin_name] = handler
        
    def preload_dependencies(self, plugin_name: str) -> bool:
        """在插件加载前处理依赖"""
        try:
            # 1. 检查并下载依赖
            dependencies = self.get_dependencies(plugin_name)
            if dependencies:
                # 检查缓存，确定需要下载的依赖
                dependencies_to_download = [
                    dep for dep in dependencies
                    if dep.name not in self._cache
                ]
                
                if dependencies_to_download:
                    if not self.download_dependencies(plugin_name):
                        raise PluginError(f"下载插件 {plugin_name} 的依赖失败")
            
            # 2. 创建并激活虚拟环境
            env_manager = VirtualEnvManager(plugin_name)
            if not env_manager.create():
                raise PluginError(f"为插件 {plugin_name} 创建虚拟环境失败")
            self._environments[plugin_name] = env_manager
            
            # 3. 生成requirements.txt并安装依赖
            dependencies = self.get_dependencies(plugin_name)
            if dependencies:
                req_path = os.path.join(self.dependencies_dir, f"{plugin_name}_requirements.txt")
                with open(req_path, 'w') as f:
                    for dep in dependencies:
                        f.write(f"{dep}\n")
                
                if not env_manager.install_dependencies(req_path):
                    raise PluginError(f"安装插件 {plugin_name} 的依赖失败")
                
            return True
            
        except Exception as e:
            self._logger.error(f"预加载插件 {plugin_name} 的依赖失败: {str(e)}")
            return False
        
    def download_dependencies(self, plugin_name: str) -> bool:
        """下载插件的依赖
        
        Returns:
            bool: 是否成功下载所有依赖
        """
        if not hasattr(self, '_download_handlers') or plugin_name not in self._download_handlers:
            raise PluginError(f"插件 {plugin_name} 未设置下载处理器")
            
        dependencies = self.get_dependencies(plugin_name)
        if not dependencies:
            return
            
        # 安全验证
        if self._security:
            for dep in dependencies:
                if not self._security.check_whitelist(dep.name):
                    raise PluginError(f"依赖 {dep.name} 不在白名单中")
                    
        plugin_dir = os.path.join(self.dependencies_dir, plugin_name)
        os.makedirs(plugin_dir, exist_ok=True)
        
        try:
            # 检查缓存，避免重复下载
            dependencies_to_download = []
            for dep in dependencies:
                if dep.name in self._cache:
                    self._logger.info(f"依赖 {dep.name} 已缓存，跳过下载")
                    continue
                dependencies_to_download.append(dep)
                
            if dependencies_to_download:
                # 调用插件提供的下载处理器
                self._download_handlers[plugin_name](dependencies_to_download, plugin_dir)
                
                # 更新缓存
                for dep in dependencies_to_download:
                    dep_path = os.path.join(plugin_dir, dep.name)
                    self._cache[dep.name] = dep_path
                    
            self._logger.info(f"成功处理插件 {plugin_name} 的依赖")
            
            # 调用注册的回调
            if plugin_name in self._callbacks:
                try:
                    self._callbacks[plugin_name](plugin_name, True)
                except Exception as e:
                    self._logger.error(f"调用插件 {plugin_name} 的回调时出错: {str(e)}")
            
            # 记录新下载的依赖信息
            for dep in dependencies:
                if dep.name in self._cache:
                    self._dependencies_info[dep.name] = DependencyInfo(
                        name=dep.name,
                        version=dep.version,
                        path=self._cache[dep.name],
                        last_used=datetime.now(),
                        optional=dep.optional
                    )
        except Exception as e:
            self._logger.error(f"下载插件 {plugin_name} 的依赖时出错: {str(e)}")
            # 调用注册的回调，通知失败
            if plugin_name in self._callbacks:
                try:
                    self._callbacks[plugin_name](plugin_name, False)
                except Exception as e:
                    self._logger.error(f"调用插件 {plugin_name} 的回调时出错: {str(e)}")
            raise PluginError(f"下载依赖失败: {str(e)}")
        
        return True
        
    def add_dependency(self, plugin_name: str, dependency: PluginDependency) -> None:
        """添加插件依赖"""
        if plugin_name not in self._dependencies:
            self._dependencies[plugin_name] = set()
        self._dependencies[plugin_name].add(dependency)
        # 发布依赖添加事件
        if self._event_bus:
            self._event_bus.emit('dependency.added', {
                'plugin_name': plugin_name,
                'dependency': dependency
            })
        
    def remove_dependency(self, plugin_name: str, dependency_name: str) -> None:
        """移除插件依赖"""
        if plugin_name in self._dependencies:
            self._dependencies[plugin_name] = {
                dep for dep in self._dependencies[plugin_name]
                if dep.name != dependency_name
            }
            
    def get_dependencies(self, plugin_name: str) -> Set[PluginDependency]:
        """获取插件的依赖"""
        return self._dependencies.get(plugin_name, set())
        
    def get_dependency_status(self, plugin_name: str) -> Dict[str, str]:
        """获取插件依赖的状态
        
        Returns:
            Dict[str, str]: 依赖名称到状态的映射
        """
        status = {}
        dependencies = self.get_dependencies(plugin_name)
        for dep in dependencies:
            if dep.name in self._cache:
                status[dep.name] = "已安装"
            else:
                status[dep.name] = "未安装"
        return status
        
    def uninstall_dependency(self, plugin_name: str, dependency_name: str) -> None:
        """卸载插件的依赖"""
        if dependency_name in self._cache:
            dep_path = self._cache[dependency_name]
            try:
                if os.path.isdir(dep_path):
                    import shutil
                    shutil.rmtree(dep_path)
                else:
                    os.remove(dep_path)
                del self._cache[dependency_name]
                self._logger.info(f"成功卸载依赖 {dependency_name}")
            except Exception as e:
                raise PluginError(f"卸载依赖 {dependency_name} 失败: {str(e)}")
        
    def import_dependency(self, plugin_name: str, dependency_name: str) -> Any:
        """导入插件的依赖"""
        if dependency_name not in self._cache:
            raise PluginError(f"依赖 {dependency_name} 未找到，请先下载")
            
        dep_path = self._cache[dependency_name]
        if not os.path.exists(dep_path):
            raise PluginError(f"依赖 {dependency_name} 的路径不存在")
            
        try:
            # 将依赖路径添加到sys.path
            if dep_path not in sys.path:
                sys.path.append(dep_path)
                
            # 导入依赖
            module = importlib.import_module(dependency_name)
            # 更新使用时间
            self._update_dependency_usage(dependency_name)
            return module
        except Exception as e:
            raise PluginError(f"导入依赖 {dependency_name} 失败: {str(e)}")
        
    def check_dependencies(self, plugin_name: str, available_plugins: Dict[str, str]) -> Optional[str]:
        """检查插件依赖是否满足"""
        dependencies = self.get_dependencies(plugin_name)
        for dep in dependencies:
            if dep.name not in available_plugins:
                if dep.optional:
                    continue
                return f"缺少必需的依赖插件: {dep.name}"
                
            if dep.version != available_plugins[dep.name]:
                return f"依赖插件 {dep.name} 版本不匹配"
                
        return None
        
    def get_load_order(self, plugins: List[str]) -> List[str]:
        """获取插件的加载顺序"""
        visited = set()
        temp_mark = set()
        order = []
        
        def visit(plugin: str):
            if plugin in temp_mark:
                raise PluginError("检测到循环依赖")
            if plugin in visited:
                return
                
            temp_mark.add(plugin)
            
            # 先处理依赖
            for dep in self.get_dependencies(plugin):
                if not dep.optional and dep.name in plugins:
                    visit(dep.name)
                    
            temp_mark.remove(plugin)
            visited.add(plugin)
            order.append(plugin)
            
        try:
            for plugin in plugins:
                if plugin not in visited:
                    visit(plugin)
            return order
            
        except Exception as e:
            self._logger.error(f"计算插件加载顺序时出错: {str(e)}")
            raise PluginError(f"计算加载顺序失败: {str(e)}")
        
    def compare_versions(self, version1: str, version2: str, operator: str = ">=") -> bool:
        """比较版本号
        
        Args:
            version1: 第一个版本号
            version2: 第二个版本号
            operator: 比较操作符 (>, >=, ==, <=, <)
        """
        v1 = version.parse(version1)
        v2 = version.parse(version2)
        
        if operator == ">":
            return v1 > v2
        elif operator == ">=":
            return v1 >= v2
        elif operator == "==":
            return v1 == v2
        elif operator == "<=":
            return v1 <= v2
        elif operator == "<":
            return v1 < v2
        else:
            raise ValueError(f"不支持的操作符: {operator}")
        
    def resolve_conflicts(self, plugin_name: str, dependencies: Set[PluginDependency]) -> Dict[str, str]:
        """自动解决依赖冲突，返回协商后的版本映射
        
        Args:
            plugin_name: 插件名称
            dependencies: 插件依赖集合
            
        Returns:
            Dict[str, str]: 依赖名称到协商版本的映射
        """
        resolved_versions = {}
        
        for dep in dependencies:
            # 查找所有插件对该依赖的版本要求
            versions = [dep.version]
            for other_plugin, other_deps in self._dependencies.items():
                if other_plugin == plugin_name:
                    continue
                for other_dep in other_deps:
                    if other_dep.name == dep.name:
                        versions.append(other_dep.version)
            
            # 选择最高兼容版本
            resolved_versions[dep.name] = self._find_compatible_version(dep.name, versions)
            
        return resolved_versions
        
    def _find_compatible_version(self, dep_name: str, versions: List[str]) -> str:
        """查找兼容版本，使用pip的依赖解析算法"""
        try:
            from pip._internal.resolution.resolvelib import factory
            from pip._internal.req import InstallRequirement
            from pip._internal.index.package_finder import PackageFinder
            from pip._internal.models.target_python import TargetPython
            from pip._internal.network.session import PipSession
            from pip._internal.utils.temp_dir import global_tempdir_manager
            
            # 创建pip所需的环境
            session = PipSession()
            target_python = TargetPython()
            finder = PackageFinder.create(
                session=session,
                target_python=target_python,
            )
            
            # 将版本要求转换为pip的InstallRequirement格式
            requirements = [
                InstallRequirement.from_line(f"{dep_name}=={v}")
                for v in versions
            ]
            
            # 使用pip的解析器查找最佳版本
            with global_tempdir_manager():
                resolver = factory.make_resolver(
                    finder=finder,
                    ignore_dependencies=True,
                    upgrade_strategy="to-satisfy-only",
                )
                result = resolver.resolve(requirements)
                
            # 返回解析出的最佳版本
            return str(result.mapping[dep_name].specifier)
            
        except ImportError:
            # 如果pip不可用，回退到简单版本选择
            return max(versions, key=lambda v: version.parse(v))
        
    def rollback_dependencies(self, plugin_name: str) -> None:
        """回滚插件的依赖安装
        
        Args:
            plugin_name: 插件名称
        """
        # 获取插件已安装的依赖
        installed_deps = [
            dep for dep in self.get_dependencies(plugin_name)
            if dep.name in self._cache
        ]
        
        # 逐个回滚
        for dep in installed_deps:
            try:
                self.uninstall_dependency(plugin_name, dep.name)
                self._logger.info(f"成功回滚依赖 {dep.name}")
            except Exception as e:
                self._logger.error(f"回滚依赖 {dep.name} 失败: {str(e)}")
                raise PluginError(f"回滚依赖 {dep.name} 失败: {str(e)}")
        
    def _update_dependency_usage(self, dependency_name: str):
        """更新依赖的最后使用时间"""
        if dependency_name in self._dependencies_info:
            self._dependencies_info[dependency_name].last_used = datetime.now()
            
    def _should_cleanup(self) -> bool:
        """检查是否应该执行清理"""
        return (datetime.now() - self._last_cleanup).days >= self.cleanup_interval
        
    def cleanup_unused_dependencies(self, force: bool = False) -> None:
        """清理未使用的依赖
        
        Args:
            force: 是否强制清理，忽略清理间隔
        """
        if not force and not self._should_cleanup():
            return
            
        self._logger.info("开始清理未使用的依赖...")
        now = datetime.now()
        cleaned_count = 0
        
        for plugin_name, env_manager in list(self._environments.items()):
            try:
                # 清理虚拟环境
                if env_manager.cleanup():
                    del self._environments[plugin_name]
                    cleaned_count += 1
                if self._event_bus:
                    self._event_bus.emit('dependency.cleaned', {
                        'plugin_name': plugin_name
                    })
            except Exception as e:
                self._logger.error(f"清理插件 {plugin_name} 的依赖失败: {str(e)}")
                
        self._last_cleanup = now
        self._logger.info(f"依赖清理完成，共清理 {cleaned_count} 个依赖")
        
    def get_dependency_info(self, dependency_name: str) -> Optional[DependencyInfo]:
        """获取依赖信息"""
        return self._dependencies_info.get(dependency_name)
        
    def get_unused_dependencies(self, days: int = None) -> List[str]:
        """获取超过指定天数未使用的依赖列表"""
        if days is None:
            days = self.retention_period
            
        now = datetime.now()
        return [
            dep_name for dep_name, dep_info in self._dependencies_info.items()
            if dep_info.optional and (now - dep_info.last_used).days > days
        ]
        
    def check_security(self, package_name: str) -> bool:
        """检查依赖包的安全性
        
        Args:
            package_name: 依赖包名称
            
        Returns:
            bool: 是否安全
        """
        try:
            # 1. 检查本地安全数据库
            if self._security:
                if not self._security.check_whitelist(package_name):
                    self._logger.warning(f"依赖 {package_name} 不在白名单中")
                    return False
                    
            # 2. 使用已有的安全扫描器
            if hasattr(self, '_scanner'):
                scanner = self._scanner
            else:
                from dependency_monitoring_framework.src.services.security_scanner import SecurityScanner
                self._scanner = SecurityScanner(self._event_bus)
                scanner = self._scanner

            try:
                result = scanner.check()
                vulnerabilities = result.get('vulnerabilities', [])
                if any(v.get('package') == package_name for v in vulnerabilities):
                    self._logger.error(f"依赖 {package_name} 存在已知漏洞")
                    # 发布安全问题事件
                    if self._event_bus:
                        self._event_bus.emit('dependency.security_check', {
                            'package': package_name,
                            'has_vulnerabilities': True,
                            'vulnerabilities': vulnerabilities
                        })
                    return False
            except Exception as e:
                self._logger.warning(f"检查漏洞数据库失败: {str(e)}")
                # 如果检查失败，不阻止依赖使用，但记录警告
                
            return True
            
        except Exception as e:
            self._logger.error(f"检查依赖 {package_name} 安全性时出错: {str(e)}")
            # 如果发生错误，为安全起见返回False
            return False
