## 工作流系统

### 概述
工作流系统允许用户创建和执行由多个插件组成的处理流程。

### 工作流类型
1. 串行工作流
   - 按顺序执行多个插件
   - 前一个插件的输出作为下一个插件的输入

2. 并行工作流
   - 同时执行多个插件
   - 所有插件使用相同的输入数据

3. 条件工作流
   - 根据条件选择执行路径
   - 支持if-else分支处理

### 使用示例
```python
# 创建串行工作流
workflow = workflow_manager.create_workflow(
    name="数据处理流程",
    description="清洗并转换数据",
    workflow_type=WorkflowType.SEQUENTIAL
)

# 添加节点
workflow_manager.add_node(workflow.id, WorkflowNode(
    id="node_1",
    name="数据清洗",
    plugin_name="数据清洗插件"
))

# 执行工作流
executor = WorkflowExecutor(plugin_system)
results = executor.execute_workflow(workflow, input_data)
```
