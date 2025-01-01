import os
import json
from typing import Dict, Any, Optional
import logging
from .plugin_error import PluginConfigError

class PluginConfig:
    """插件配置管理"""
    
    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        self._logger = logging.getLogger(__name__)
        self._configs: Dict[str, Dict[str, Any]] = {}
        os.makedirs(self.config_dir, exist_ok=True)
        
    def _get_config_path(self, plugin_name: str) -> str:
        """获取插件配置文件路径"""
        return os.path.join(self.config_dir, f"{plugin_name}.config.json")
        
    def load_config(self, plugin_name: str) -> Dict[str, Any]:
        """加载插件配置"""
        try:
            config_path = self._get_config_path(plugin_name)
            if os.path.exists(config_path):
                # 检查文件是否为空
                if os.path.getsize(config_path) == 0:
                    self._configs[plugin_name] = {}
                    return self._configs[plugin_name]
                    
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._configs[plugin_name] = json.load(f)
            else:
                self._configs[plugin_name] = {}
                # 创建配置文件并写入空对象
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
            return self._configs[plugin_name]
            
        except Exception as e:
            self._logger.error(f"加载插件 {plugin_name} 配置失败: {str(e)}")
            raise PluginConfigError(f"加载配置失败: {str(e)}")
            
    def save_config(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """保存插件配置到 {plugin_name}.config.json"""
        try:
            config_path = self._get_config_path(plugin_name)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise PluginConfigError(f"保存配置失败: {str(e)}")
            
    def get_config(self, plugin_name: str) -> Dict[str, Any]:
        """获取插件配置"""
        if plugin_name not in self._configs:
            self.load_config(plugin_name)
        return self._configs[plugin_name]
        
    def update_config(self, plugin_name: str, updates: Dict[str, Any]) -> None:
        """更新插件配置"""
        config = self.get_config(plugin_name)
        config.update(updates)
        self.save_config(plugin_name, config)
        
    def validate_config(self, plugin_name: str, schema: Dict[str, Dict[str, Any]]) -> Optional[str]:
        """验证插件配置"""
        try:
            config = self.get_config(plugin_name)
            for key, field_schema in schema.items():
                # 检查必填字段
                if field_schema.get('required', False) and key not in config:
                    return f"缺少必填配置项: {key}"
                    
                # 检查字段类型
                if key in config:
                    expected_type = field_schema.get('type')
                    if expected_type and not isinstance(config[key], expected_type):
                        return f"配置项 {key} 类型错误"
                        
                # 检查取值范围
                if key in config and 'range' in field_schema:
                    value_range = field_schema['range']
                    if config[key] not in value_range:
                        return f"配置项 {key} 的值不在允许范围内"
                        
            return None
            
        except Exception as e:
            self._logger.error(f"验证插件 {plugin_name} 配置失败: {str(e)}")
            raise PluginConfigError(f"验证配置失败: {str(e)}") 