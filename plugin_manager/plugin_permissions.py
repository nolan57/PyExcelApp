from enum import Enum
from typing import Set, Dict
import json
import os
import logging

class PluginPermission(Enum):
    """插件权限枚举"""
    FILE_READ = "file_read"         # 文件读取权限
    FILE_WRITE = "file_write"       # 文件写入权限
    NETWORK = "network"             # 网络访问权限
    SYSTEM_EXEC = "system_exec"     # 系统执行权限
    UI_MODIFY = "ui_modify"         # 界面修改权限
    DATA_READ = "data_read"         # 数据读取权限
    DATA_WRITE = "data_write"       # 数据写入权限
    
    @staticmethod
    def get_permission_description(permission) -> str:
        """获取权限的详细描述"""
        descriptions = {
            PluginPermission.FILE_READ: "读取文件",
            PluginPermission.FILE_WRITE: "写入文件",
            PluginPermission.DATA_READ: "读取数据",
            PluginPermission.DATA_WRITE: "写入数据",
            PluginPermission.UI_MODIFY: "修改界面",
            PluginPermission.SYSTEM_EXEC: "执行系统命令",
            PluginPermission.NETWORK: "网络访问"
        }
        return descriptions.get(permission, "未知权限")

class PluginPermissionManager:
    def __init__(self, permission_file: str):
        self.permission_file = permission_file
        self.plugin_permissions: Dict[str, Set[PluginPermission]] = {}
        self._load_permissions()
        
    def _load_permissions(self):
        """加载权限配置"""
        if os.path.exists(self.permission_file):
            try:
                with open(self.permission_file, 'r') as f:
                    data = json.load(f)
                    for plugin_name, perms in data.items():
                        self.plugin_permissions[plugin_name] = {
                            PluginPermission(p) for p in perms
                        }
            except Exception as e:
                logging.error(f"加载权限配置失败: {e}")
                self.plugin_permissions = {}
                
    def save_permissions(self):
        """保存权限配置"""
        try:
            data = {
                plugin_name: [p.value for p in perms]
                for plugin_name, perms in self.plugin_permissions.items()
            }
            os.makedirs(os.path.dirname(self.permission_file), exist_ok=True)
            with open(self.permission_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logging.error(f"保存权限配置失败: {e}")
            
    def grant_permission(self, plugin_name: str, permission: PluginPermission):
        """授予权限"""
        if plugin_name not in self.plugin_permissions:
            self.plugin_permissions[plugin_name] = set()
        self.plugin_permissions[plugin_name].add(permission)
        self.save_permissions()
        
    def revoke_permission(self, plugin_name: str, permission: PluginPermission):
        """撤销权限"""
        if plugin_name in self.plugin_permissions:
            self.plugin_permissions[plugin_name].discard(permission)
            self.save_permissions()
            
    def has_permission(self, plugin_name: str, permission: PluginPermission) -> bool:
        """检查是否有权限"""
        return (plugin_name in self.plugin_permissions and
                permission in self.plugin_permissions[plugin_name])
