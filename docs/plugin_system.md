```python:plugin_manager/docs/plugin_docs.py
from typing import Dict, Any
from dataclasses import dataclass
import json
import os

@dataclass
class PluginDocumentation:
    """插件文档数据类"""
    name: str
    version: str
    description: str
    author: str
    permissions: Dict[str, str]
    config_schema: Dict[str, Any]
    usage: str
    examples: Dict[str, str]
```

```markdown:docs/plugin_system.md
# 插件系统文档

## 目录
1. [系统概述](#系统概述)
2. [插件开发指南](#插件开发指南)
3. [API 参考](#api-参考)
4. [最佳实践](#最佳实践)

## 系统概述

插件系统提供了一个灵活的框架，允许开发者通过插件扩展应用程序的功能。

### 主要特性
- 插件生命周期管理
- 权限系统
- 事件系统
- 配置管理
- 依赖管理

## 插件开发指南

### 创建新插件

1. 继承基类
```python
from plugin_manager.core.plugin_base import PluginBase

class MyPlugin(PluginBase):
    def __init__(self):
        super().__init__()
```docs/plugin_system.md

2. 实现必需方法
```python
def get_name(self) -> str:
    return "我的插件"
    
def get_version(self) -> str:
    return "1.0.0"
    
def get_description(self) -> str:
    return "这是一个示例插件"
```

3. 定义配置模式
```python:docs/plugin_system.md
def get_config_schema(self) -> Dict[str, Dict[str, Any]]:
    return {
        'option_name': {
            'type': str,
            'required': True,
            'default': 'default_value',
            'description': '选项描述'
        }
    }
```

### 权限管理

插件可以请求以下权限：
- FILE_READ: 文件读取权限
- FILE_WRITE: 文件写入权限
- DATA_READ: 数据读取权限
- DATA_WRITE: 数据写入权限
- UI_MODIFY: UI修改权限

```python
def __init__(self):
    super().__init__()
    self._required_permissions = {
        PluginPermission.FILE_READ,
        PluginPermission.DATA_WRITE
    }
```

### 事件系统

订阅和发送事件：
```python
# 订阅事件
self.register_event_handler('event.name', self.handle_event)

# 发送事件
self.emit_event('event.name', data={'key': 'value'})
```

### 生命周期管理

插件状态：
- UNLOADED: 未加载
- LOADED: 已加载
- ACTIVE: 已激活
- INACTIVE: 已停用
- ERROR: 错误状态
- RUNNING: 运行中

生命周期方法：
```python
def initialize(self) -> None:
    """初始化插件"""
    pass
    
def activate(self, granted_permissions: Set[PluginPermission]) -> None:
    """激活插件"""
    pass
    
def deactivate(self) -> None:
    """停用插件"""
    pass
```

## API 参考

### PluginInterface

核心接口定义：
```python
class PluginInterface(ABC):
    @abstractmethod
    def get_name(self) -> str: ...
    
    @abstractmethod
    def get_version(self) -> str: ...
    
    @abstractmethod
    def get_description(self) -> str: ...
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Dict[str, Any]]: ...
```

### PluginBase

基类提供的功能：
- 基础插件实现
- 事件处理
- 权限管理
- 状态管理
- 错误处理

### PluginSystem

系统核心功能：
- 插件加载和卸载
- 插件激活和停用
- 配置管理
- 权限管理
- 依赖管理

## 最佳实践

1. 错误处理
```python
try:
    # 操作代码
except Exception as e:
    self.handle_error(e, "操作失败")
```

2. 配置管理
```python
def get_config_schema(self) -> Dict[str, Dict[str, Any]]:
    return {
        'option': {
            'type': str,
            'required': True,
            'default': 'value',
            'description': '描述'
        }
    }
```

3. 权限使用
```python
if self.has_permission(PluginPermission.FILE_WRITE):
    # 执行需要权限的操作
else:
    # 请求权限
    if self.request_permission(PluginPermission.FILE_WRITE):
        # 权限获取成功
```

4. 事件处理
```python
def initialize(self):
    self.register_event_handler('data.changed', self.on_data_changed)
    
def on_data_changed(self, event_data):
    # 处理事件
```

5. 状态管理
```python
def process_data(self):
    if self._state != PluginState.ACTIVE:
        raise PluginError("插件未激活")
```

## 示例插件

完整的示例插件实现：

```python
from plugin_manager.core.plugin_base import PluginBase
from plugin_manager.features.plugin_permissions import PluginPermission

class ExamplePlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._required_permissions = {
            PluginPermission.DATA_READ,
            PluginPermission.DATA_WRITE
        }
        
    def get_name(self) -> str:
        return "示例插件"
        
    def get_version(self) -> str:
        return "1.0.0"
        
    def get_description(self) -> str:
        return "这是一个示例插件"
        
    def get_config_schema(self) -> Dict[str, Dict[str, Any]]:
        return {
            'option': {
                'type': str,
                'required': True,
                'default': 'default',
                'description': '示例选项'
            }
        }
        
    def initialize(self) -> None:
        self.register_event_handler('data.changed', self.on_data_changed)
        
    def on_data_changed(self, event_data):
        self._logger.info(f"数据变更: {event_data}")
        
    def process_data(self, data: Any) -> Any:
        if not self.has_permission(PluginPermission.DATA_WRITE):
            raise PermissionError("需要数据写入权限")
        return self._process(data)
```
```
我来补充 plugin_system.md 中关于加密配置和权限的内容：

```markdown:plugin_manager/docs/plugin_system.md
# 插件系统设计文档

...

## 配置管理

### 配置加密存储
插件系统支持将配置文件进行加密存储，以保护敏感配置信息的安全。

#### 加密机制
- 使用 Fernet 对称加密算法
- 密钥文件存储在 `plugins/configs/config.key`
- 加密后的配置文件使用 `.bin` 扩展名
- 未加密的配置文件使用 `.json` 扩展名

#### 配置文件格式
1. 加密模式
```python
# 二进制格式存储加密后的配置
encrypted_data = encryption.encrypt_data(config_dict)
with open('plugin.config.bin', 'wb') as f:
    f.write(encrypted_data)
```

2. 非加密模式
```python
# JSON格式存储原始配置
with open('plugin.config.json', 'w') as f:
    json.dump(config_dict, f, indent=4)
```

### 权限管理

#### 权限存储
权限配置同样支持加密存储机制：

1. 加密模式下存储为二进制文件
```python
permissions_data = {
    "plugin_name": ["FILE_READ", "FILE_WRITE"]
}
encrypted_data = encryption.encrypt_data(permissions_data)
```

2. 非加密模式下存储为 JSON 文件
```python
{
    "plugin_name": ["FILE_READ", "FILE_WRITE"]
}
```

#### 安全性考虑
- 配置文件加密可以防止未经授权的访问和修改
- 权限数据加密可以防止权限被篡改
- 密钥文件需要妥善保管，避免泄露

### 使用示例

```python
# 初始化加密管理器
key_file = os.path.join(plugin_dir, 'configs/config.key')
encryption = ConfigEncryption(key_file)

# 创建配置管理器
config = PluginConfig(config_dir, encryption)

# 创建权限管理器
permission_manager = PluginPermissionManager(permission_file, encryption)
```

### 注意事项
1. 加密和非加密模式可以共存，由是否提供加密管理器决定
2. 更改加密模式后，需要重新保存所有配置
3. 密钥文件丢失将导致无法解密已加密的配置
4. 建议定期备份密钥文件
