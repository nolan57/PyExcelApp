from enum import Enum, auto
from typing import Dict, Set, Optional
import json
import os
import logging
from plugin_manager.utils.config_encryption import ConfigEncryption

class PluginPermission(Enum):
    """插件权限枚举"""
    FILE_READ = auto()    # 文件读取权限
    FILE_WRITE = auto()   # 文件写入权限
    DATA_READ = auto()    # 数据读取权限
    DATA_WRITE = auto()   # 数据写入权限
    UI_MODIFY = auto()    # UI修改权限
    NETWORK = auto()      # 网络访问权限
    SYSTEM_EXEC = auto()  # 系统执行权限
    
    @staticmethod
    def get_permission_description(permission) -> str:
        descriptions = {
            PluginPermission.FILE_READ: "文件读取权限",
            PluginPermission.FILE_WRITE: "文件写入权限",
            PluginPermission.NETWORK: "网络访问权限",
            PluginPermission.SYSTEM_EXEC: "系统执行权限",
            PluginPermission.DATA_READ: "数据读取权限",
            PluginPermission.DATA_WRITE: "数据写入权限",
            PluginPermission.UI_MODIFY: "UI修改权限"
        }
        return descriptions.get(permission, "未知权限")

class PluginPermissionManager:
    """插件权限管理器"""
    
    def __init__(self, permission_file: str, encryption: ConfigEncryption = None):
        self.permission_file = permission_file
        self._permissions = {}
        self._logger = logging.getLogger(__name__)
        self.plugin_config = None  # 将在PluginSystem初始化时设置
        self.permission_file = permission_file
        self._encryption = encryption # 加密配置文件
        
        # 如果提供了权限文件路径，则从文件加载权限
        if permission_file and os.path.exists(permission_file):
            try:
                    data=None
                    if self._encryption:
                        with open(permission_file, 'rb') as f:
                            encrypted_data = f.read()
                            data = self._encryption.decrypt_data(encrypted_data)
                    else:
                        with open(permission_file, 'rb') as f:
                            encrypted_data = f.read()
                            data = json.loads(encrypted_data.decode())
                    for plugin_name, perms in data.items():
                        self._permissions[plugin_name] = {
                            PluginPermission[p] for p in perms
                        }
            except Exception as e:
                self._logger.error(f"加载权限配置失败: {str(e)}")
        
        # 确保权限文件目录存在
        if permission_file:
            os.makedirs(os.path.dirname(permission_file), exist_ok=True)
        
    def set_plugin_config(self, plugin_config):
        """设置插件配置管理器"""
        self.plugin_config = plugin_config
        
    def _save_permissions(self) -> None:
        """保存权限配置到权限文件"""
        try:
            if self.permission_file:
                permissions_data = {
                    plugin_name: [p.name for p in perms]
                    for plugin_name, perms in self._permissions.items()
                }
                if self._encryption:
                    with open(self.permission_file, 'wb') as f:
                        encrypted_data = self._encryption.encrypt_data(permissions_data)
                        f.write(encrypted_data)
                else:
                    with open(self.permission_file, 'w', encoding='utf-8') as f:
                        json.dump(permissions_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self._logger.error(f"保存权限配置失败: {str(e)}")
            
    def grant_permission(self, plugin_name: str, permission: PluginPermission) -> None:
        """授予权限"""
        if plugin_name not in self._permissions:
            self._permissions[plugin_name] = set()
        self._permissions[plugin_name].add(permission)
        self._save_permissions()
        
    def revoke_permission(self, plugin_name: str, permission: PluginPermission) -> None:
        """撤销权限"""
        if plugin_name in self._permissions:
            self._permissions[plugin_name].discard(permission)
            self._save_permissions()
            
    def get_granted_permissions(self, plugin_name: str) -> Set[PluginPermission]:
        """获取已授予的权限"""
        return self._permissions.get(plugin_name, set())
