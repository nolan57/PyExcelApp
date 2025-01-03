import os
import sys
import importlib
import inspect
import logging
from typing import List, Type, Optional, Dict
from ..core.plugin_interface import PluginInterface
from ..core.plugin_base import PluginBase
from .plugin_error import PluginError, PluginLoadError
from ..features.plugin_lifecycle import PluginState

class PluginLoader:
    """插件加载器"""
    
    def __init__(self, plugin_dir: str = "plugin_manager/plugins", plugin_system = None):
        self.plugin_dir = plugin_dir
        self.plugin_system = plugin_system
        self._loaded_modules: Dict[str, Any] = {}
        self._logger = logging.getLogger(__name__)
        self._dependency_cache = {}  # 缓存已验证的依赖
        
    def scan_plugins(self) -> List[str]:
        """扫描插件目录，返回可用的插件名称列表"""
        try:
            if not os.path.exists(self.plugin_dir):
                self._logger.warning(f"插件目录不存在: {self.plugin_dir}")
                return []
            
            plugins = []
            for file in os.listdir(self.plugin_dir):
                if file.endswith('.py') and not file.startswith('__'):
                    plugin_name = file[:-3]  # 移除 .py 后缀
                    plugins.append(plugin_name)
            
            self._logger.info(f"找到 {len(plugins)} 个插件: {plugins}")
            return plugins
            
        except Exception as e:
            self._logger.error(f"扫描插件目录时出错: {str(e)}")
            raise PluginError(f"扫描插件失败: {str(e)}")
        
    def _load_module(self, plugin_name: str, force_reload: bool = False) -> Optional[Type[PluginInterface]]:
        """
        内部方法：加载插件模块
        
        Args:
            plugin_name: 插件名称
            force_reload: 是否强制重新加载
        """
        try:
            # 1. 构建路径
            plugin_path = os.path.join(self.plugin_dir, f"{plugin_name}.py")
            module_path = f"plugin_manager.plugins.{plugin_name}"
            
            # 2. 检查插件文件是否存在
            if not os.path.exists(plugin_path):
                raise PluginLoadError(f"插件文件不存在: {plugin_path}")
            
            # 3. 处理模块加载逻辑
            if module_path in sys.modules:
                if not force_reload:
                    # 如果模块已加载且不需要强制重新加载，直接返回缓存的模块
                    module = sys.modules[module_path]
                else:
                    # 如果需要强制重新加载，先卸载再加载
                    self.unload_plugin(plugin_name)
                    spec = importlib.util.spec_from_file_location(module_path, plugin_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
            else:
                # 首次加载模块
                spec = importlib.util.spec_from_file_location(module_path, plugin_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            
            # 4. 保存到已加载模块
            self._loaded_modules[plugin_name] = module
            
            # 5. 查找插件类
            plugin_class = None
            for item in dir(module):
                obj = getattr(module, item)
                if (inspect.isclass(obj) and 
                    issubclass(obj, (PluginInterface, PluginBase)) and 
                    obj not in (PluginInterface, PluginBase)):
                    plugin_class = obj
                    break
            
            if plugin_class is None:
                raise PluginLoadError(
                    f"插件 {plugin_name} 中未找到有效的插件类。"
                    f"插件类必须实现 PluginInterface 或继承自 PluginBase，且不能是抽象类"
                )
            
            # 验证插件类
            if plugin_class:
                # 验证依赖相关方法
                required_methods = [
                    'get_name', 'get_version', 'get_description',
                    'get_config_schema', 'validate_parameters',
                    'get_dependencies', 'get_trusted_sources',
                    'verify_dependency_signature'
                ]
                
                for method in required_methods:
                    if not hasattr(plugin_class, method):
                        raise PluginLoadError(f"插件类缺少必需的方法: {method}")
                        
                # 验证依赖
                if hasattr(plugin_class, 'get_dependencies'):
                    dependencies = plugin_class.get_dependencies()
                    if dependencies and not self._verify_dependencies(plugin_name, dependencies):
                        raise PluginLoadError(f"插件 {plugin_name} 依赖验证失败")
                        
            return plugin_class
            
        except ImportError as e:
            self._logger.error(f"加载插件 {plugin_name} 失败: {str(e)}")
            raise PluginLoadError(f"加载插件失败: {str(e)}")
        except Exception as e:
            self._logger.error(f"加载插件时发生错误: {str(e)}")
            raise PluginLoadError(f"加载插件时发生错误: {str(e)}")
            
    def load_plugin(self, plugin_name: str) -> Optional[Type[PluginInterface]]:
        """加载插件"""
        return self._load_module(plugin_name, force_reload=False)
            
    def unload_plugin(self, plugin_name: str) -> None:
        """卸载插件"""
        try:
            module_path = f"plugin_manager.plugins.{plugin_name}"
            
            # 从 sys.modules 中移除
            if module_path in sys.modules:
                del sys.modules[module_path]
                
            # 从已加载模块中移除
            if plugin_name in self._loaded_modules:
                del self._loaded_modules[plugin_name]
                
        except Exception as e:
            self._logger.error(f"卸载插件 {plugin_name} 失败: {str(e)}")
            raise PluginError(f"卸载插件失败: {str(e)}")
            
    def reload_plugin(self, plugin_name: str) -> Optional[Type[PluginInterface]]:
        """重新加载插件"""
        try:
            # 1. 保存当前状态（如果需要）
            old_plugin = self.plugin_system.get_plugin(plugin_name)
            saved_state = None
            if old_plugin:
                saved_state = old_plugin.save_state()
            
            # 2. 强制重新加载模块
            plugin_class = self._load_module(plugin_name, force_reload=True)
            
            # 3. 恢复状态（如果需要）
            if plugin_class and saved_state:
                new_plugin = plugin_class()
                new_plugin.restore_state(saved_state)
            
            return plugin_class
            
        except Exception as e:
            self._logger.error(f"重新加载插件失败: {str(e)}")
            raise PluginError(f"重新加载插件失败: {str(e)}")
            
    def get_loaded_plugins(self) -> List[str]:
        """获取已加载的插件列表"""
        return list(self._loaded_modules.keys())

    def validate_plugin_class(self, plugin_class: Type) -> Optional[str]:
        """验证插件类是否正确实现了所有必需的方法"""
        required_methods = [
            'get_name', 'get_version', 'get_description',
            'get_config_schema', 'validate_parameters'
        ]
        
        for method in required_methods:
            if not hasattr(plugin_class, method):
                return f"插件类缺少必需的方法: {method}"
        return None

    def _verify_dependencies(self, plugin_name: str, dependencies: List[str]) -> bool:
        """验证插件依赖"""
        try:
            # 检查缓存
            cache_key = f"{plugin_name}:{','.join(dependencies)}"
            if cache_key in self._dependency_cache:
                return self._dependency_cache[cache_key]
                
            # 验证每个依赖
            for dep in dependencies:
                if not self._verify_single_dependency(plugin_name, dep):
                    return False
                    
            # 缓存结果
            self._dependency_cache[cache_key] = True
            return True
            
        except Exception as e:
            self._logger.error(f"验证插件 {plugin_name} 依赖时出错: {str(e)}")
            return False
            
    def _verify_single_dependency(self, plugin_name: str, dependency: str) -> bool:
        """验证单个依赖
        
        Args:
            plugin_name: 插件名称
            dependency: 依赖包说明，格式如 "package>=1.0.0"
            
        Returns:
            bool: 依赖是否有效
        """
        try:
            # 1. 解析依赖格式
            import re
            pattern = re.compile(r"^([a-zA-Z0-9\-_\.]+)(?:(>=|<=|==|>|<)(.+))?$")
            match = pattern.match(dependency)
            if not match:
                self._logger.error(f"依赖格式无效: {dependency}")
                return False
                
            package_name, operator, version = match.groups()
            
            # 2. 检查包名是否合法
            if not re.match(r"^[a-zA-Z0-9\-_\.]+$", package_name):
                self._logger.error(f"包名不合法: {package_name}")
                return False
                
            # 3. 检查版本号格式（如果指定了版本）
            if version:
                try:
                    from packaging import version as Version
                    Version.parse(version)
                except Exception:
                    self._logger.error(f"版本号格式无效: {version}")
                    return False
                    
            # 4. 检查是否在可信源列表中
            if self.plugin_system:
                plugin = self.plugin_system.get_plugin(plugin_name)
                if plugin:
                    trusted_sources = plugin.get_trusted_sources()
                    if not any(source.endswith(package_name) for source in trusted_sources):
                        self._logger.warning(f"依赖 {package_name} 不在可信源列表中")
                        # 不阻止加载，但记录警告
                        
            # 5. 检查是否有已知的安全漏洞
            if self.plugin_system and hasattr(self.plugin_system, 'dependency_manager'):
                security_check = self.plugin_system.dependency_manager.check_security(package_name)
                if not security_check:
                    self._logger.error(f"依赖 {package_name} 存在安全风险")
                    return False
                    
            return True
            
        except Exception as e:
            self._logger.error(f"验证依赖 {dependency} 时出错: {str(e)}")
            return False
