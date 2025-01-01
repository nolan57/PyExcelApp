from cryptography.fernet import Fernet
import base64
import json
import os

class ConfigEncryption:
    """配置加密管理器"""
    
    def __init__(self, key_file: str = "config.key"):
        self.key_file = key_file
        self._key = self._load_or_generate_key()
        self._fernet = Fernet(self._key)
        
    def _load_or_generate_key(self) -> bytes:
        """加载或生成加密密钥"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return base64.urlsafe_b64decode(f.read())
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(base64.urlsafe_b64encode(key))
            return key
            
    def encrypt_data(self, data: dict) -> bytes:
        """加密数据"""
        json_data = json.dumps(data)
        return self._fernet.encrypt(json_data.encode())
        
    def decrypt_data(self, encrypted_data: bytes) -> dict:
        """解密数据"""
        decrypted_data = self._fernet.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode()) 