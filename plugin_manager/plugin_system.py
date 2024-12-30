# plugin_system.py
import json
import os
import importlib.util
import logging
from typing import Dict, Any, Optional, Set, List
from dataclasses import dataclass

from PyQt6.QtWidgets import QMessageBox, QApplication

from plugin_manager.plugin_interface import PluginInterface
from utils.error_handler import ErrorHandler
from plugin_manager.plugin_permissions import PluginPermission, PluginPermissionManager

@dataclass
class PluginInfo:
    """插件信息类"""
    name: str
    version: str
    description: str
    path: str
    instance: PluginInterface

class PluginError(Exception):
    """插件相关错误"""
    pass

class PluginSystem:
    def __init__(self, event_bus=None):
        self._plugins: Dict[str, PluginInfo] = {}
        self._plugin_dir = os.path.join(os.path.dirname(__file__), 'plugins')
        self._logger = logging.getLogger(__name__)
        self._event_bus = event_bus
        
        # 初始化权限管理器
        permission_file = os.path.join(os.path.dirname(__file__), 'plugin_permissions.json')
        self.permission_manager = PluginPermissionManager(permission_file)
        # 确保权限文件存在
        if not os.path.exists(permission_file):
            with open(permission_file, 'w') as f:
                json.dump({}, f)
        
        self._setup_plugin_directory()
        
        # 插件生命周期状态
        self._plugin_states: Dict[str, str] = {}  # 存储插件状态：loaded, initialized, active, stopped
        
        self._dependency_graph = {}  # 存储插件依赖关系
        
    def _setup_plugin_directory(self) -> None:
        """初始化插件目录"""
        if not os.path.exists(self._plugin_dir):
            os.makedirs(self._plugin_dir)
            self._logger.info(f"已创建插件目录: {self._plugin_dir}")
    
    def load_plugin(self, plugin_path: str, show_info: bool = False) -> bool:
        """
        加载单个插件
        
        Args:
            plugin_path: 插件文件路径
            show_info: 是否显示加载信息，默认False
        """
        try:
            plugin_name = os.path.splitext(os.path.basename(plugin_path))[0]
            
            # 检查插件是否已经加载
            if plugin_name in self._plugins:
                self._logger.warning(f"插件 {plugin_name} 已加载")
                return False
            
            # 加载模块
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            if spec is None or spec.loader is None:
                raise PluginError(f"无法加载插件: {plugin_path}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 实例化插件类
            plugin_class = getattr(module, f"{plugin_name.title()}Plugin", None)
            if not plugin_class:
                raise PluginError(f"未在 {plugin_name} 中找到插件类")
            
            plugin_instance = plugin_class()
            # 设置插件系统引用
            plugin_instance.plugin_system = self
            
            # 验证插件接口
            if not isinstance(plugin_instance, PluginInterface):
                raise PluginError(f"插件 {plugin_name} 未实现 PluginInterface")
            
            # 存储插件信息
            self._plugins[plugin_name] = PluginInfo(
                name=plugin_instance.get_name(),
                version=plugin_instance.get_version(),
                description=plugin_instance.get_description(),
                path=plugin_path,
                instance=plugin_instance
            )
            
            # 初始化插件状态
            self._plugin_states[plugin_name] = 'loaded'

            if show_info:
                ErrorHandler.handle_info(f"成功加载插件: {plugin_name} v{plugin_instance.get_version()}")
            return True
            
        except Exception as e:
            if show_info:
                ErrorHandler.handle_error(e, None, f"加载插件 {plugin_path} 时发生错误")
            raise PluginError(f"加载插件失败: {str(e)}")
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """
        获取插件实例，包含权限检查和错误处理
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[PluginInterface]: 插件实例，如果插件不存在则返回 None
            
        Raises:
            PluginError: 当插件访问出错时
        """
        try:
            # 检查插件是否存在
            plugin_info = self._plugins.get(plugin_name)
            if not plugin_info:
                self._logger.warning(f"未找到插件: {plugin_name}")
                return None
            
            # 检查插件状态
            plugin_state = self._plugin_states.get(plugin_name)
            if plugin_state not in ['loaded', 'active']:
                self._logger.warning(f"插件 {plugin_name} 处于无效状态: {plugin_state}")
                return None
            
            return plugin_info.instance
            
        except Exception as e:
            self._logger.error(f"访问插件 {plugin_name} 时出错: {str(e)}")
            raise PluginError(f"访问插件失败: {str(e)}")
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """获取插件信息"""
        return self._plugins.get(plugin_name)
    
    def get_all_plugins(self) -> Dict[str, PluginInfo]:
        """获取所有插件信息"""
        return self._plugins
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        if plugin_name in self._plugins:
            del self._plugins[plugin_name]
            del self._plugin_states[plugin_name]
            self._logger.info(f"已卸载插件: {plugin_name}")
            return True
        return False
    
    def process_data_with_plugin(
        self,
        plugin_name: str,
        table_view: Any,
        parameters: Dict[str, Any]
    ) -> Any:
        """
        用指定插件处理数据
        
        Args:
            plugin_name: 插件名称
            table_view: QTableView实例
            parameters: 处理参数
            
        Returns:
            处理结果
            
        Raises:
            PluginError: 当处理出错时
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise PluginError(f"未找到插件 {plugin_name}")
            
        # 检查插件状态
        if self._plugin_states.get(plugin_name) != 'active':
            raise PluginError(f"插件 {plugin_name} 未激活")
            
        # 验证参数
        error = plugin.validate_parameters(parameters)
        if error:
            raise PluginError(f"无效参数: {error}")
            
        try:
            result = plugin.process_data(table_view, **parameters)

            return result
        except Exception as e:
            self._logger.error(f"使用插件 {plugin_name} 处理数据时出错: {str(e)}")
            raise PluginError(f"插件处理错误: {str(e)}")

    def load_all_plugins(self) -> None:
        """
        加载插件目录中的所有插件

        Returns:
            None

        Raises:
            PluginError: 当加载过程出错时
        """
        try:
            # 确保插件目录存在
            if not os.path.exists(self._plugin_dir):
                self._logger.warning(f"未找到插件目录: {self._plugin_dir}")
                return

            # 遍历插件目录中的所有Python文件
            for filename in os.listdir(self._plugin_dir):
                if filename.endswith('.py') and not filename.startswith('__'):
                    plugin_path = os.path.join(self._plugin_dir, filename)
                    try:
                        # 使用已有的load_plugin方法加载单个插件
                        self.load_plugin(plugin_path)
                    except PluginError as e:
                        self._logger.error(f"加载插件 {filename} 时出错: {str(e)}")
                        # 继续加载其他插件，而不是终止整个过程
                        continue

            self._logger.info(f"成功加载 {len(self._plugins)} 个插件")

        except Exception as e:
            self._logger.error(f"加载插件时出错: {str(e)}")
            raise PluginError(f"加载插件失败: {str(e)}")

    @property
    def plugin_dir(self):
        return self._plugin_dir

    @property
    def plugins(self):
        return self._plugins
        
    def get_plugin_state(self, plugin_name: str) -> Optional[str]:
        """获取插件当前状态"""
        return self._plugin_states.get(plugin_name)
        
    def activate_plugin(self, plugin_name: str) -> bool:
        """激活插件"""
        if plugin_name not in self._plugins:
            return False
        
        try:
            plugin = self._plugins[plugin_name].instance
            
            # 获取插件所需权限
            required_permissions = plugin.get_required_permissions()
            # 获取已授予的权限
            granted_permissions = self.permission_manager.get_granted_permissions(plugin_name)
            
            # 检查缺失的权限
            missing_permissions = required_permissions - granted_permissions
            
            if missing_permissions:
                self._logger.warning(f"插件 {plugin_name} 缺少以下权限: {', '.join(p.value for p in missing_permissions)}")
                return False
            
            # 激活插件
            plugin.activate(granted_permissions)
            self._plugin_states[plugin_name] = 'active'
            
            # 触发插件激活事件
            print("触发插件激活事件")
            if self._event_bus:
                self._event_bus.emit('plugin.activated', {
                    'plugin_name': plugin_name,
                    'plugin_info': self._plugins[plugin_name]
                })
                
            # 确保插件激活后立即返回
            QApplication.processEvents()
            return True
            
        except Exception as e:
            self._logger.error(f"激活插件 {plugin_name} 时出错: {str(e)}")
            self._plugin_states[plugin_name] = 'error'
            return False
        
    def deactivate_plugin(self, plugin_name: str) -> bool:
        """停用插件"""
        if plugin_name not in self._plugins:
            return False
            
        self._plugin_states[plugin_name] = 'loaded'
        
        # 触发插件停用事件
        if self._event_bus:
            self._event_bus.emit('plugin.deactivated', {
                'plugin_name': plugin_name,
                'plugin_info': self._plugins[plugin_name]
            })
            
        return True

    def check_plugin_permission(self, plugin_name: str, permission: PluginPermission) -> bool:
        """检查插件权限"""
        return self.permission_manager.has_permission(plugin_name, permission)
        
    def request_plugin_permissions(self, plugin_name: str, permissions: Set[PluginPermission]) -> bool:
        """请求一组权限"""
        try:
            # 检查已有权限
            missing_permissions = set()
            for permission in permissions:
                if not self.check_plugin_permission(plugin_name, permission):
                    missing_permissions.add(permission)
                
            if not missing_permissions:
                return True
            
            # 显示权限请求对话框
            message = f"插件 {plugin_name} 需要以下权限:\n"
            for perm in missing_permissions:
                message += f"- {PluginPermission.get_permission_description(perm)}\n"
            message += "\n是否授予这些权限？授权后将被永久保存。"
            
            # 使用非模态对话框
            reply = QMessageBox.question(
                None,
                "权限请求",
                message,
                buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                defaultButton=QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                for permission in missing_permissions:
                    self.permission_manager.grant_permission(plugin_name, permission)
                return True
                
            return False
            
        except Exception as e:
            self._logger.error(f"为插件 {plugin_name} 请求权限时出错: {str(e)}")
            return False

    def get_required_permission(self, action_name: str) -> Optional[PluginPermission]:
        """获取执行指定动作所需的权限"""
        permission_mapping = {
            'modify_ui': PluginPermission.UI_MODIFY,
            'access_files': PluginPermission.FILE_READ,
            'write_files': PluginPermission.FILE_WRITE,
            'execute_system': PluginPermission.SYSTEM_EXEC,
            'access_network': PluginPermission.NETWORK
        }
        return permission_mapping.get(action_name)

    def execute_plugin_action(self, plugin_name: str, action_name: str, *args, **kwargs):
        """执行插件动作时检查权限"""
        required_permission = self.get_required_permission(action_name)
        if required_permission and not self.check_plugin_permission(plugin_name, required_permission):
            raise PermissionError(f"插件 {plugin_name} 没有执行 {action_name} 的权限")
        
        plugin = self.get_plugin(plugin_name)
        return getattr(plugin, action_name)(*args, **kwargs)

    def get_plugin_instance(self, plugin_name: str) -> Optional[PluginInterface]:
        """
        获取插件实例（不进行权限检查）
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[PluginInterface]: 插件实例，如果不存在则返回 None
        """
        plugin_info = self._plugins.get(plugin_name)
        return plugin_info.instance if plugin_info else None

    def resolve_dependencies(self, plugin_name: str) -> List[str]:
        """解析插件依赖，返回正确的加载顺序"""
        pass
        
    def check_circular_dependencies(self) -> bool:
        """检查是否存在循环依赖"""
        pass
