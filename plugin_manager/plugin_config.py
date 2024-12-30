import json
import os
from typing import Dict, Any
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

class PluginConfig:
    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "plugin_configs.json")
        self.signature_file = os.path.join(config_dir, "plugin_signatures.json")
        self._load_configs()
        self._init_crypto()
    
    def _init_crypto(self):
        """初始化加密相关"""
        key_file = os.path.join(self.config_dir, "crypto.key")
        if not os.path.exists(key_file):
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            self.public_key = self.private_key.public_key()
        
    def _load_configs(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.configs = json.load(f)
        else:
            self.configs = {}
            
    def save_config(self, plugin_name: str, config: Dict[str, Any]):
        """保存插件配置"""
        self.configs[plugin_name] = config
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.configs, f, indent=4)
            
    def get_config(self, plugin_name: str) -> Dict[str, Any]:
        """获取插件配置"""
        return self.configs.get(plugin_name, {})
        
    def sign_plugin(self, plugin_path: str) -> str:
        """为插件生成签名"""
        with open(plugin_path, 'rb') as f:
            content = f.read()
        signature = self.private_key.sign(
            content,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')
        
    def verify_signature(self, plugin_path: str, signature: str) -> bool:
        """验证插件签名"""
        try:
            with open(plugin_path, 'rb') as f:
                content = f.read()
            signature_bytes = base64.b64decode(signature)
            self.public_key.verify(
                signature_bytes,
                content,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except:
            return False 

class PluginConfigManager:
    def validate_config(self, plugin_name: str, config: Dict) -> bool:
        """验证配置有效性"""
        pass
        
    def apply_config(self, plugin_name: str, config: Dict) -> None:
        """应用配置并通知相关插件"""
        pass
        
    def watch_config_changes(self, plugin_name: str) -> None:
        """监听配置文件变化"""
        pass 