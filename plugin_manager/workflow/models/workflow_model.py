from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

class WorkflowType(Enum):
    """工作流类型"""
    SEQUENTIAL = "sequential"    # 串行执行
    PARALLEL = "parallel"       # 并行执行
    CONDITIONAL = "conditional" # 条件分支

@dataclass
class WorkflowNode:
    """工作流节点"""
    id: str                     # 节点唯一标识
    name: str                   # 节点名称
    plugin_name: str           # 使用的插件名称
    parameters: Dict[str, Any] = field(default_factory=dict)  # 插件参数
    next_nodes: List[str] = field(default_factory=list)      # 后续节点ID列表
    condition: Optional[str] = None                          # 条件表达式

@dataclass
class Workflow:
    """工作流定义"""
    id: str                    # 工作流唯一标识
    name: str                  # 工作流名称
    description: str           # 工作流描述
    type: WorkflowType        # 工作流类型
    nodes: Dict[str, WorkflowNode] = field(default_factory=dict)  # 节点集合
    entry_node: str = None    # 入口节点ID
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "nodes": {
                node_id: {
                    "id": node.id,
                    "name": node.name,
                    "plugin_name": node.plugin_name,
                    "parameters": node.parameters,
                    "next_nodes": node.next_nodes,
                    "condition": node.condition
                }
                for node_id, node in self.nodes.items()
            },
            "entry_node": self.entry_node
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Workflow':
        """从字典创建工作流"""
        nodes = {
            node_id: WorkflowNode(**node_data)
            for node_id, node_data in data["nodes"].items()
        }
        
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            type=WorkflowType(data["type"]),
            nodes=nodes,
            entry_node=data["entry_node"]
        ) 