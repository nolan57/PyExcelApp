from enum import Enum
from typing import Dict, List, Any
from dataclasses import dataclass

class WorkflowType(Enum):
    SEQUENTIAL = "sequential"  # 串行执行
    PARALLEL = "parallel"     # 并行执行
    CONDITIONAL = "conditional"  # 条件分支

@dataclass
class WorkflowNode:
    plugin_name: str
    parameters: Dict[str, Any] = None
    condition: str = None  # 条件表达式
    next_nodes: List['WorkflowNode'] = None

class PluginWorkflow:
    """插件工作流管理器"""
    
    def __init__(self, plugin_system):
        self.plugin_system = plugin_system
        self._workflows = {}
        
    def create_workflow(self, name: str, workflow_type: WorkflowType) -> None:
        """创建新的工作流"""
        self._workflows[name] = {
            'type': workflow_type,
            'nodes': []
        }
        
    def add_node(self, workflow_name: str, node: WorkflowNode) -> None:
        """添加工作流节点"""
        if workflow_name in self._workflows:
            self._workflows[workflow_name]['nodes'].append(node)
            
    def execute_workflow(self, workflow_name: str, initial_data: Any) -> Any:
        """执行工作流"""
        workflow = self._workflows.get(workflow_name)
        if not workflow:
            raise ValueError(f"Workflow {workflow_name} not found")
            
        if workflow['type'] == WorkflowType.SEQUENTIAL:
            return self._execute_sequential(workflow['nodes'], initial_data)
        elif workflow['type'] == WorkflowType.PARALLEL:
            return self._execute_parallel(workflow['nodes'], initial_data)
        else:
            return self._execute_conditional(workflow['nodes'], initial_data) 