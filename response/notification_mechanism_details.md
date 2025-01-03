# 通知机制详情

## 事件总线 (`dependency_monitoring_framework/src/core/event_bus.py`)

### 功能概述
事件总线是项目中用于处理系统内事件发布和订阅的核心组件。它允许不同模块之间通过事件进行通信，而不需要直接耦合。

### 主要功能
1. **订阅事件**:
   - `subscribe(event_type: str, callback: Callable)`: 订阅特定类型的事件，并提供一个回调函数，在事件触发时调用。
   
2. **取消订阅事件**:
   - `unsubscribe(event_type: str, callback: Callable)`: 取消对特定事件类型的订阅。
   
3. **发布事件**:
   - `publish(event_type: str, data: Any = None)`: 发布特定类型的事件，并传递相关数据。
   
4. **获取最后一次事件数据**:
   - `get_last_event(event_type: str)`: 获取最后一次发布的事件数据。
   
5. **清除订阅者**:
   - `clear_subscribers(event_type: str = None)`: 清除特定事件类型的订阅者，或清除所有订阅者。
   
6. **获取订阅者数量**:
   - `get_subscriber_count(event_type: str)`: 获取特定事件类型的订阅者数量。
   
7. **获取所有事件类型**:
   - `get_all_event_types()`: 获取所有已注册的事件类型。

### 示例代码
```python
# 订阅事件
def on_plugin_started(data):
    print(f"Plugin started: {data}")

event_bus = EventBus()
event_bus.subscribe('plugin.started', on_plugin_started)

# 发布事件
event_bus.publish('plugin.started', {'plugin_name': 'test_plugin'})
```

### 插件系统中的使用
插件系统利用事件总线来通知主窗口或其他模块关于插件的启动、停止和其他状态变化。以下是一些关键事件：
- `plugin.started`: 当插件启动时触发。
- `plugin.stopped`: 当插件停止时触发。
- `plugin.activated`: 当插件激活时触发。
- `plugin.deactivated`: 当插件停用时触发。
- `plugin.data_processed`: 当插件处理数据时触发。
- `plugin.config_changed`: 当插件配置更改时触发。
- `plugin.permission_revoked`: 当插件权限被撤销时触发。

### 改进建议
1. **增加异步事件处理能力**:
   - 当前事件处理是同步的，可能会阻塞主线程。已经使用`asyncio`库实现了异步事件处理，提高了性能。
   
2. **提供事件优先级机制**:
   - 允许事件具有不同的优先级，确保重要事件能够优先处理。已经通过`PriorityQueue`实现了事件优先级机制。
   
3. **增加事件回调的错误处理**:
   - 在事件回调中增加了详细的错误处理机制，使用装饰器`event_handler_wrapper`来捕获和记录异常。
   
4. **提供事件过滤机制**:
   - 允许订阅者指定过滤条件，只接收符合特定条件的事件。通过在`subscribe`方法中添加`filter_condition`参数实现了这一功能。

## 事件总线 (`utils/event_bus.py`)

### 功能概述
事件总线是项目中用于处理系统内事件发布和订阅的核心组件。它允许不同模块之间通过事件进行通信，而不需要直接耦合。

### 主要功能
1. **订阅事件**:
   - `subscribe(event_type: str, callback: Callable, priority: int = 1)`: 订阅特定类型的事件，并提供一个回调函数，在事件触发时调用。允许指定回调优先级，默认为1（数字越小优先级越高）。
   
2. **取消订阅事件**:
   - `unsubscribe(event_type: str, callback: Callable)`: 取消对特定事件类型的订阅。
   
3. **发布事件**:
   - `publish(event_type: str, data: Any = None, priority: int = 1)`: 发布特定类型的事件，并传递相关数据。允许指定事件优先级，默认为1（数字越小优先级越高）。
   
4. **获取最后一次事件数据**:
   - `get_last_event(event_type: str)`: 获取最后一次发布的事件数据。
   
5. **清除订阅者**:
   - `clear_subscribers(event_type: str = None)`: 清除特定事件类型的订阅者，或清除所有订阅者。
   
6. **获取订阅者数量**:
   - `get_subscriber_count(event_type: str)`: 获取特定事件类型的订阅者数量。
   
7. **获取所有事件类型**:
   - `get_all_event_types()`: 获取所有已注册的事件类型。

### 示例代码
```python
# 订阅事件
def on_plugin_started(data):
    print(f"Plugin started: {data}")

event_bus = EventBus()
event_bus.subscribe('plugin.started', on_plugin_started, priority=1)

# 发布事件
event_bus.publish('plugin.started', {'plugin_name': 'test_plugin'}, priority=1)
```

### 插件系统中的使用
插件系统利用事件总线来通知主窗口或其他模块关于插件的启动、停止和其他状态变化。以下是一些关键事件：
- `plugin.started`: 当插件启动时触发。
- `plugin.stopped`: 当插件停止时触发。
- `plugin.activated`: 当插件激活时触发。
- `plugin.deactivated`: 当插件停用时触发。
- `plugin.data_processed`: 当插件处理数据时触发。
- `plugin.config_changed`: 当插件配置更改时触发。
- `plugin.permission_revoked`: 当插件权限被撤销时触发。

### 改进建议
1. **增加异步事件处理能力**:
   - 当前事件处理是同步的，可能会阻塞主线程。已经使用`asyncio`库实现了异步事件处理，提高了性能。
   
2. **提供事件优先级机制**:
   - 允许事件具有不同的优先级，确保重要事件能够优先处理。已经通过`PriorityQueue`实现了事件优先级机制。
   
3. **增加事件回调的错误处理**:
   - 在事件回调中增加了详细的错误处理机制，使用装饰器`event_handler_wrapper`来捕获和记录异常。
   
4. **提供事件过滤机制**:
   - 允许订阅者指定过滤条件，只接收符合特定条件的事件。通过在`subscribe`方法中添加`filter_condition`参数实现了这一功能。

## 插件系统 (`plugin_manager/core/plugin_system.py`)

### 事件发布
插件系统在多个关键操作中发布事件，以通知其他模块。以下是主要事件发布点：
- **插件加载**:
  - `load_plugin(plugin_name: str)`: 发布 `plugin.loaded` 事件。
  
- **插件激活**:
  - `activate_plugin(plugin_name: str)`: 发布 `plugin.activated` 事件。
  
- **插件停用**:
  - `deactivate_plugin(plugin_name: str)`: 发布 `plugin.deactivated` 事件。
  
- **插件启动**:
  - `start_plugin(plugin_name: str)`: 发布 `plugin.started` 事件。
  
- **插件停止**:
  - `stop_plugin(plugin_name: str)`: 发布 `plugin.stopped` 事件。
  
- **插件数据处理**:
  - `process_data(plugin_name: str, table_view, **parameters)`: 发布 `plugin.data_processed` 事件。
  
- **插件配置更改**:
  - `set_plugin_config(plugin_name: str, config: Dict[str, Any])`: 发布 `plugin.config_changed` 事件。
  
- **插件权限撤销**:
  - `revoke_permission(plugin_name: str, permission: PluginPermission)`: 发布 `plugin.permission_revoked` 事件。

### 示例代码
```python
# 订阅插件启动事件
def on_plugin_started(data):
    print(f"Plugin started: {data}")

plugin_system = PluginSystem()
plugin_system._event_bus.subscribe('plugin.started', on_plugin_started, priority=1)

# 启动插件
plugin_system.start_plugin('test_plugin')
```

### 改进建议
1. **增加事件回调的错误处理**:
   - 当前事件回调中的错误会被捕获并打印，但可以提供更详细的错误处理机制，例如记录日志或通知其他模块。
   
2. **提供事件过滤机制**:
   - 允许订阅者指定过滤条件，只接收符合特定条件的事件。通过在`subscribe`方法中添加`filter_condition`参数实现了这一功能。

## 结论
事件总线和插件系统中的通知机制是项目中重要的通信手段。通过优化和扩展这些机制，可以提高系统的灵活性和可维护性。
