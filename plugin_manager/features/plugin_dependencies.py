from typing import Dict, Set, List, Optional
from dataclasses import dataclass
import logging
from ..utils.plugin_error import PluginError

@dataclass
class PluginDependency:
    """插件依赖信息"""
    name: str
    version: str
    optional: bool = False

class DependencyManager:
    """插件依赖管理"""
    
    def __init__(self):
        self._dependencies: Dict[str, Set[PluginDependency]] = {}
        self._logger = logging.getLogger(__name__)
        
    def add_dependency(self, plugin_name: str, dependency: PluginDependency) -> None:
        """添加插件依赖"""
        if plugin_name not in self._dependencies:
            self._dependencies[plugin_name] = set()
        self._dependencies[plugin_name].add(dependency)
        
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