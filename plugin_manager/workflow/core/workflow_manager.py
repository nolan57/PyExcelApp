import os
import json
import logging
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from ..models.workflow_model import Workflow, WorkflowNode, WorkflowType
from plugin_manager.utils.config_encryption import ConfigEncryption

class WorkflowManager:
    """工作流管理器"""
    
    def __init__(self, plugin_system, workflow_dir: str = "workflows", encryption: ConfigEncryption = None):
        self.plugin_system = plugin_system
        self.workflow_dir = workflow_dir
        self._encryption = encryption
        self._workflows: Dict[str, Workflow] = {}
        self._logger = logging.getLogger(__name__)
        
        # 确保工作流目录存在
        os.makedirs(workflow_dir, exist_ok=True)
        
        # 加载所有工作流
        self._load_workflows()
        
    def _load_workflows(self) -> None:
        """加载所有工作流"""
        for filename in os.listdir(self.workflow_dir):
            if filename.endswith(('.json', '.bin')):
                try:
                    workflow_path = os.path.join(self.workflow_dir, filename)
                    workflow = self.load_workflow(workflow_path)
                    self._workflows[workflow.id] = workflow
                except Exception as e:
                    self._logger.error(f"加载工作流 {filename} 失败: {str(e)}")
                    
    def load_workflow(self, path: str) -> Workflow:
        """加载工作流定义"""
        try:
            if self._encryption and path.endswith('.bin'):
                with open(path, 'rb') as f:
                    encrypted_data = f.read()
                    data = self._encryption.decrypt_data(encrypted_data)
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
            # 转换节点列表为字典格式
            if 'nodes' in data and isinstance(data['nodes'], list):
                nodes_dict = {}
                for node in data['nodes']:
                    nodes_dict[node['id']] = node
                data['nodes'] = nodes_dict
                
            return Workflow.from_dict(data)
        except Exception as e:
            raise ValueError(f"加载工作流失败: {str(e)}")
            
    def save_workflow(self, workflow: Workflow) -> None:
        """保存工作流定义"""
        try:
            data = workflow.to_dict()
            if self._encryption:
                path = os.path.join(self.workflow_dir, f"{workflow.id}.bin")
                with open(path, 'wb') as f:
                    encrypted_data = self._encryption.encrypt_data(data)
                    f.write(encrypted_data)
            else:
                path = os.path.join(self.workflow_dir, f"{workflow.id}.json")
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise ValueError(f"保存工作流失败: {str(e)}")
            
    def create_workflow(self, name: str, description: str, workflow_type: WorkflowType) -> Workflow:
        """创建新工作流"""
        workflow_id = f"workflow_{len(self._workflows) + 1}"
        workflow = Workflow(
            id=workflow_id,
            name=name,
            description=description,
            type=workflow_type
        )
        self._workflows[workflow_id] = workflow
        return workflow
        
    def add_node(self, workflow_id: str, node: WorkflowNode) -> None:
        """添加工作流节点"""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"工作流 {workflow_id} 不存在")
            
        workflow.nodes[node.id] = node
        if not workflow.entry_node:
            workflow.entry_node = node.id
            
    def execute_workflow(self, workflow_id: str, input_data: Any) -> Any:
        """执行工作流"""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"工作流 {workflow_id} 不存在")
            
        if workflow.type == WorkflowType.SEQUENTIAL:
            return self._execute_sequential(workflow, input_data)
        elif workflow.type == WorkflowType.PARALLEL:
            return self._execute_parallel(workflow, input_data)
        else:
            return self._execute_conditional(workflow, input_data)
            
    def _execute_sequential(self, workflow: Workflow, data: Any) -> Any:
        """串行执行工作流"""
        current_node_id = workflow.entry_node
        result = data
        
        while current_node_id:
            node = workflow.nodes[current_node_id]
            try:
                # 执行插件处理
                result = self.plugin_system.process_data(
                    node.plugin_name,
                    result,
                    **node.parameters
                )
                # 获取下一个节点
                current_node_id = node.next_nodes[0] if node.next_nodes else None
            except Exception as e:
                self._logger.error(f"节点 {node.name} 执行失败: {str(e)}")
                raise
                
        return result
        
    def _execute_parallel(self, workflow: Workflow, data: Any) -> List[Any]:
        """并行执行工作流"""
        with ThreadPoolExecutor() as executor:
            futures = []
            for node_id in workflow.nodes:
                node = workflow.nodes[node_id]
                future = executor.submit(
                    self.plugin_system.process_data,
                    node.plugin_name,
                    data,
                    **node.parameters
                )
                futures.append(future)
                
        return [f.result() for f in futures]
        
    def _execute_conditional(self, workflow: Workflow, data: Any) -> Any:
        """条件执行工作流"""
        current_node = workflow.nodes[workflow.entry_node]
        
        # 评估条件
        if current_node.condition:
            condition_result = eval(
                current_node.condition,
                {"data": data}
            )
            # 根据条件选择下一个节点
            next_node_id = current_node.next_nodes[0] if condition_result else current_node.next_nodes[1]
        else:
            next_node_id = current_node.next_nodes[0]
            
        if next_node_id:
            next_node = workflow.nodes[next_node_id]
            return self.plugin_system.process_data(
                next_node.plugin_name,
                data,
                **next_node.parameters
            )
        return data 