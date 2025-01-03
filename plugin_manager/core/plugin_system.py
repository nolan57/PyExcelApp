import os
from typing import Dict, Any, Optional, List, Callable
import logging
from dataclasses import dataclass
from functools import wraps

from .plugin_interface import PluginInterface
from ..features.plugin_permissions import PluginPermission, PluginPermissionManager
from ..utils.plugin_loader import PluginLoader
from ..utils.plugin_error import PluginError, ErrorHandler
from ..utils.plugin_config import PluginConfig
from plugin_manager.features.dependencies.plugin_dependencies import DependencyManager
from ..features.plugin_lifecycle import PluginState
from ..utils.config_encryption import ConfigEncryption
from ..features.plugin_workflow import PluginWorkflow
from ..utils.event_bus_adapter import EventBus

@dataclass
class PluginInfo:
    """插件信息类"""
    name: str
    version: str
    description: str
    path: str
    instance: PluginInterface

def event_handler_wrapper(func: Callable) -> Callable:
    """事件回调的装饰器，用于处理异常"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except Exception as e:
            logging.getLogger(__name__).error(f"Error in event handler {func.__name__}: {str(e)}")
            ErrorHandler.handle_error(e)
    return wrapper

class PluginSystem:
    """插件系统核心类"""
    
    def __init__(self, event_bus=None, plugin_dir="plugin_manager/plugins"):
        # 设置插件目录和配置目录
        self.plugin_dir = plugin_dir
        self.config_dir = os.path.join(self.plugin_dir, 'configs')  # 插件配置目录
        self.permission_file = os.path.join(self.plugin_dir, 'permissions.json')
        
        # 初始化事件总线
        self._event_bus = event_bus or EventBus()
        
        # 确保目录结构
        os.makedirs(self.plugin_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 初始化配置加密
        key_file = os.path.join(self.plugin_dir, 'configs/config.key')
        self.config_encryption = ConfigEncryption(key_file)
        
        # 初始化组件
        self.config = PluginConfig(self.config_dir, self.config_encryption)
        self.loader = PluginLoader(plugin_dir=self.plugin_dir, plugin_system=self)
        self.permission_manager = PluginPermissionManager(self.permission_file)
        self.permission_manager.set_plugin_config(self.config)
        
        # 初始化依赖管理器
        self.dependency_manager = DependencyManager(
            dependencies_dir=os.path.join(plugin_dir, "dependencies"),
            cleanup_interval=7,   # 每7天检查一次
            retention_period=30,  # 保留30天未使用的依赖
            event_bus=self._event_bus  # 传入事件总线
        )
        
        # 内部状态
        self._plugins: Dict[str, PluginInfo] = {}
        self._plugin_states: Dict[str, PluginState] = {}
        self._running_plugins = {}
        self._logger = logging.getLogger(__name__)
        
        # 初始化工作流管理器
        self.workflow = PluginWorkflow(self)
        
        # 订阅依赖相关事件
        self._event_bus.subscribe('dependency.security_check', self._on_security_check)
        self._event_bus.subscribe('dependency.update_available', self._on_update_available)
        
    def _on_security_check(self, data: Dict):
        """处理依赖安全检查事件"""
        if data.get('has_vulnerabilities'):
            self._logger.warning(f"发现依赖安全问题: {data}")
            # 通知相关插件
            affected_plugins = self._find_affected_plugins(data.get('package'))
            for plugin in affected_plugins:
                plugin.handle_dependency_security_issue(data)
                
    def _on_update_available(self, data: Dict):
        """处理依赖更新事件"""
        self._logger.info(f"依赖更新可用: {data}")
        # 可以在这里实现自动更新逻辑
        
    def _find_affected_plugins(self, package_name: str) -> List[PluginInterface]:
        """查找使用指定依赖的插件"""
        affected = []
        for plugin_info in self._plugins.values():
            if package_name in plugin_info.instance.get_dependencies():
                affected.append(plugin_info.instance)
        return affected
        
    async def process_data(self, plugin_name: str, table_view, **parameters) -> Any:
        """使用插件处理数据"""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise PluginError(f"未找到插件 {plugin_name}")
            
        # 获取插件配置
        config = self.config.get_config(plugin_name)
        # 将配置合并到参数中
        parameters.update(config)
        
        # 检查插件状态
        if self._plugin_states.get(plugin_name) != PluginState.ACTIVE:
            raise PluginError(f"插件 {plugin_name} 未激活")
            
        # 验证参数
        error = plugin.validate_parameters(parameters)
        if error:
            raise PluginError(f"无效参数: {error}")
            
        try:
            # 设置表格视图
            plugin.set_table_view(table_view)
            
            # 处理数据，传入合并后的参数
            result = plugin.process_data(table_view, **parameters)
            
            # 触发事件
            if self._event_bus:
                await self._event_bus.publish('plugin.data_processed', {
                    'plugin_name': plugin_name,
                    'parameters': parameters,
                    'result': result
                })
                
            return result
            
        except Exception as e:
            self._logger.error(f"使用插件 {plugin_name} 处理数据时出错: {str(e)}")
            raise PluginError(f"插件处理错误: {str(e)}")
            
    async def deactivate_plugin(self, plugin_name: str) -> bool:
        """停用插件"""
        if plugin_name not in self._plugins:
            return False
            
        try:
            plugin = self._plugins[plugin_name].instance
            plugin.deactivate()
            self._plugin_states[plugin_name] = PluginState.INACTIVE
            
            # 触发事件
            if self._event_bus:
                await self._event_bus.publish('plugin.deactivated', {
                    'plugin_name': plugin_name
                })
                
            return True
            
        except Exception as e:
            self._logger.error(f"停用插件 {plugin_name} 失败: {str(e)}")
            return False
            
    async def start_plugin(self, plugin_name: str) -> bool:
        """启动插件"""
        if not self.is_plugin_active(plugin_name):
            return False
            
        try:
            plugin = self._plugins[plugin_name].instance
            plugin.start()
            self._running_plugins[plugin_name] = plugin
            
            # 触发事件
            if self._event_bus:
                await self._event_bus.publish('plugin.started', {
                    'plugin_name': plugin_name
                })
                
            return True
            
        except Exception as e:
            self._logger.error(f"启动插件 {plugin_name} 失败: {str(e)}")
            return False
            
    async def stop_plugin(self, plugin_name: str) -> bool:
        """停止插件"""
        plugin = self._running_plugins.get(plugin_name)
        if plugin:
            try:
                plugin.stop()
                del self._running_plugins[plugin_name]
                
                # 触发事件
                if self._event_bus:
                    await self._event_bus.publish('plugin.stopped', {
                        'plugin_name': plugin_name
                    })
                    
                return True
                
            except Exception as e:
                self._logger.error(f"停止插件 {plugin_name} 失败: {str(e)}")
                return False
        return False
        
    def is_plugin_running(self, plugin_name: str) -> bool:
        """检查插件是否正在运行"""
        return plugin_name in self._running_plugins
        
    def get_plugin_state(self, plugin_name: str) -> Optional[PluginState]:
        """获取插件状态"""
        return self._plugin_states.get(plugin_name)
        
    async def load_plugin(self, plugin_name: str, show_info: bool = False) -> bool:
        """加载单个插件"""
        try:
            # 使用 loader 加载插件类
            plugin_class = self.loader.load_plugin(plugin_name)
            if not plugin_class:
                return False
                
            # 处理插件依赖
            dependencies = plugin_class.get_dependencies()
            if dependencies:
                for dep in dependencies:
                    self.dependency_manager.add_dependency(plugin_name, dep)
                
                # 预加载依赖
                if not self.dependency_manager.preload_dependencies(plugin_name):
                    raise PluginError(f"插件 {plugin_name} 依赖预加载失败")

            # 实例化并初始化插件
            plugin = plugin_class()
            plugin.plugin_system = self
            plugin.initialize()
            
            # 保存插件信息
            plugin_info = PluginInfo(
                name=plugin.get_name(),
                version=plugin.get_version(),
                description=plugin.get_description(),
                path=f"{self.plugin_dir}/{plugin_name}.py",
                instance=plugin
            )
            
            self._plugins[plugin_name] = plugin_info
            self._plugin_states[plugin_name] = PluginState.LOADED
            
            # 触发事件
            if self._event_bus:
                await self._event_bus.publish('plugin.loaded', {
                    'plugin_name': plugin_name,
                    'plugin_info': plugin_info
                })
                
            # 检查是否需要清理依赖
            self.dependency_manager.cleanup_unused_dependencies()
            
            return True
            
        except Exception as e:
            self._logger.error(f"加载插件 {plugin_name} 失败: {str(e)}")
            self._plugin_states[plugin_name] = PluginState.ERROR
            if show_info:
                raise PluginError(f"加载插件失败: {str(e)}")
            return False
            
    def load_all_plugins(self) -> None:
        """加载所有可用插件"""
        available_plugins = self.loader.scan_plugins()
        
        # 获取依赖顺序
        try:
            load_order = self.dependency_manager.get_load_order(available_plugins)
        except PluginError as e:
            self._logger.error(f"计算插件加载顺序失败: {str(e)}")
            load_order = available_plugins
            
        # 按顺序加载插件
        for plugin_name in load_order:
            try:
                self.load_plugin(plugin_name)
            except Exception as e:
                self._logger.error(f"加载插件 {plugin_name} 失败: {str(e)}")
                continue
                
    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        if plugin_name in self._plugins:
            try:
                plugin = self._plugins[plugin_name].instance
                plugin.cleanup()
                del self._plugins[plugin_name]
                self.loader.unload_plugin(plugin_name)
                return True
            except Exception as e:
                self._logger.error(f"卸载插件 {plugin_name} 失败: {str(e)}")
                return False
        return False
        
    async def activate_plugin(self, plugin_name: str) -> bool:
        """激活插件"""
        if plugin_name not in self._plugins:
            return False
            
        try:
            plugin = self._plugins[plugin_name].instance
            
            # 激活插件的虚拟环境
            env_manager = self.dependency_manager._environments.get(plugin_name)
            if env_manager and not env_manager.activate():
                raise PluginError(f"激活插件 {plugin_name} 的虚拟环境失败")
            
            # 检查依赖
            error = self.dependency_manager.check_dependencies(
                plugin_name,
                {name: info.version for name, info in self._plugins.items()}
            )
            if error:
                self._logger.warning(f"插件 {plugin_name} 依赖检查失败: {error}")
                return False
                
            # 获取并检查权限
            required_permissions = plugin.get_required_permissions()
            granted_permissions = self.permission_manager.get_granted_permissions(plugin_name)
            
            missing_permissions = required_permissions - granted_permissions
            if missing_permissions:
                self._logger.warning(f"插件 {plugin_name} 缺少必要权限: {missing_permissions}")
                return False
                
            # 激活插件
            plugin.activate(granted_permissions)
            self._plugin_states[plugin_name] = PluginState.ACTIVE
            
            # 触发事件
            if self._event_bus:
                await self._event_bus.publish('plugin.activated', {
                    'plugin_name': plugin_name,
                    'plugin_info': self._plugins[plugin_name]
                })
                
            return True
            
        except Exception as e:
            self._plugin_states[plugin_name] = PluginState.ERROR
            ErrorHandler.handle_error(e)
            return False
            
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """获取插件实例"""
        plugin_info = self._plugins.get(plugin_name)
        return plugin_info.instance if plugin_info else None
        
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """获取插件信息"""
        return self._plugins.get(plugin_name)
        
    def get_all_plugins(self) -> Dict[str, PluginInfo]:
        """获取所有插件信息"""
        return self._plugins
        
    def is_plugin_active(self, plugin_name: str) -> bool:
        """检查插件是否已激活"""
        return self._plugin_states.get(plugin_name) == PluginState.ACTIVE 
        
    async def reload_plugin(self, plugin_name: str) -> bool:
        """重新加载插件"""
        try:
            # 1. 保存状态
            old_state = None
            if plugin_name in self._plugins:
                old_state = self._plugins[plugin_name].instance.save_state()
                self.unload_plugin(plugin_name)
                
            # 2. 重新加载
            await self.load_plugin(plugin_name)
            
            # 3. 恢复状态
            if old_state and plugin_name in self._plugins:
                self._plugins[plugin_name].instance.restore_state(old_state)
                
            # 4. 触发事件
            if self._event_bus:
                await self._event_bus.publish('plugin.reloaded', {
                    'plugin_name': plugin_name,
                    'plugin_info': self._plugins.get(plugin_name)
                })
                
            return True
            
        except Exception as e:
            self._logger.error(f"重新加载插件 {plugin_name} 失败: {str(e)}")
            return False
            
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """获取插件配置"""
        return self.config.get_config(plugin_name)
        
    async def set_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """设置插件配置"""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise PluginError(f"未找到插件 {plugin_name}")
            
        # 验证配置
        schema = plugin.get_config_schema()
        error = self.config.validate_config(plugin_name, schema)
        if error:
            raise PluginError(f"配置验证失败: {error}")
            
        # 保存配置
        self.config.save_config(plugin_name, config)
    
        # 触发事件
        if self._event_bus:
            await self._event_bus.publish('plugin.config_changed', {
                'plugin_name': plugin_name,
                'config': config
            })
            
    def request_permission(self, plugin_name: str, permission: PluginPermission) -> bool:
        """请求插件权限"""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return False
            
        return plugin.request_permission(permission)
        
    async def revoke_permission(self, plugin_name: str, permission: PluginPermission) -> None:
        """撤销插件权限"""
        self.permission_manager.revoke_permission(plugin_name, permission)
        
        # 触发事件
        if self._event_bus:
            await self._event_bus.publish('plugin.permission_revoked', {
                'plugin_name': plugin_name,
                'permission': permission
            })

    def subscribe(self, event_type: str, callback: Callable, filter_condition: Callable = None) -> None:
        """订阅特定类型的事件，并提供一个回调函数，在事件触发时调用。

        Args:
            event_type: 事件类型
            callback: 回调函数，接收事件数据作为参数
            filter_condition: 过滤条件函数，返回True表示接收事件，False表示忽略事件
        """
        if filter_condition:
            wrapped_callback = event_handler_wrapper(lambda data: callback(data) if filter_condition(data) else None)
        else:
            wrapped_callback = event_handler_wrapper(callback)
        
        if self._event_bus:
            self._event_bus.subscribe(event_type, wrapped_callback)
