import logging
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass
from enum import Enum
import time
from PyQt6.QtCore import QRectF
from PyQt6.QtWidgets import QGraphicsItem, QInputDialog
import math

from ..models.workflow_model import Workflow, WorkflowNode, WorkflowType

class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    COMPLETED = "completed"  # 执行完成
    FAILED = "failed"       # 执行失败
    CANCELLED = "cancelled" # 已取消

@dataclass
class NodeExecutionResult:
    """节点执行结果"""
    node_id: str
    status: ExecutionStatus
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0

class WorkflowExecutor:
    """工作流执行器"""
    
    def __init__(self, plugin_system):
        self.plugin_system = plugin_system
        self._logger = logging.getLogger(__name__)
        self._execution_results: Dict[str, Dict[str, NodeExecutionResult]] = {}
        self._current_executions: Dict[str, Dict[str, Future]] = {}
        
    def execute_workflow(self, workflow: Workflow, input_data: Any) -> Dict[str, NodeExecutionResult]:
        """执行工作流"""
        try:
            # 初始化执行结果
            workflow_id = workflow.id
            self._execution_results[workflow_id] = {}
            self._current_executions[workflow_id] = {}
            
            # 根据工作流类型选择执行策略
            if workflow.type == WorkflowType.SEQUENTIAL:
                results = self._execute_sequential(workflow, input_data)
            elif workflow.type == WorkflowType.PARALLEL:
                results = self._execute_parallel(workflow, input_data)
            else:
                results = self._execute_conditional(workflow, input_data)
                
            return results
            
        except Exception as e:
            self._logger.error(f"工作流 {workflow.id} 执行失败: {str(e)}")
            raise
            
    def _execute_sequential(self, workflow: Workflow, data: Any) -> Dict[str, NodeExecutionResult]:
        """串行执行工作流"""
        current_node_id = workflow.entry_node
        current_data = data
        
        while current_node_id:
            node = workflow.nodes[current_node_id]
            try:
                # 执行当前节点
                start_time = time.time()
                result = self.plugin_system.process_data(
                    node.plugin_name,
                    current_data,
                    **node.parameters
                )
                execution_time = time.time() - start_time
                
                # 记录执行结果
                self._execution_results[workflow.id][node.id] = NodeExecutionResult(
                    node_id=node.id,
                    status=ExecutionStatus.COMPLETED,
                    result=result,
                    execution_time=execution_time
                )
                
                # 更新数据和下一个节点
                current_data = result
                current_node_id = node.next_nodes[0] if node.next_nodes else None
                
            except Exception as e:
                self._logger.error(f"节点 {node.id} 执行失败: {str(e)}")
                self._execution_results[workflow.id][node.id] = NodeExecutionResult(
                    node_id=node.id,
                    status=ExecutionStatus.FAILED,
                    error=e
                )
                raise
                
        return self._execution_results[workflow.id]
        
    def _execute_parallel(self, workflow: Workflow, data: Any) -> Dict[str, NodeExecutionResult]:
        """并行执行工作流"""
        with ThreadPoolExecutor() as executor:
            futures = {}
            
            # 提交所有节点执行
            for node_id, node in workflow.nodes.items():
                future = executor.submit(
                    self._execute_node,
                    workflow.id,
                    node,
                    data
                )
                futures[node_id] = future
                self._current_executions[workflow.id][node_id] = future
                
            # 等待所有节点完成
            for node_id, future in futures.items():
                try:
                    result = future.result()
                    self._execution_results[workflow.id][node_id] = result
                except Exception as e:
                    self._logger.error(f"节点 {node_id} 执行失败: {str(e)}")
                    self._execution_results[workflow.id][node_id] = NodeExecutionResult(
                        node_id=node_id,
                        status=ExecutionStatus.FAILED,
                        error=e
                    )
                    
        return self._execution_results[workflow.id]
        
    def _execute_conditional(self, workflow: Workflow, data: Any) -> Dict[str, NodeExecutionResult]:
        """条件执行工作流"""
        entry_node = workflow.nodes[workflow.entry_node]
        
        try:
            # 评估条件
            if entry_node.condition:
                condition_result = eval(
                    entry_node.condition,
                    {"data": data}
                )
                # 根据条件选择下一个节点
                next_node_id = entry_node.next_nodes[0] if condition_result else entry_node.next_nodes[1]
            else:
                next_node_id = entry_node.next_nodes[0]
                
            if next_node_id:
                next_node = workflow.nodes[next_node_id]
                # 执行选中的分支
                start_time = time.time()
                result = self.plugin_system.process_data(
                    next_node.plugin_name,
                    data,
                    **next_node.parameters
                )
                execution_time = time.time() - start_time
                
                self._execution_results[workflow.id][next_node.id] = NodeExecutionResult(
                    node_id=next_node.id,
                    status=ExecutionStatus.COMPLETED,
                    result=result,
                    execution_time=execution_time
                )
                
        except Exception as e:
            self._logger.error(f"条件执行失败: {str(e)}")
            raise
            
        return self._execution_results[workflow.id]
        
    def _execute_node(self, workflow_id: str, node: WorkflowNode, data: Any) -> NodeExecutionResult:
        """执行单个节点"""
        try:
            start_time = time.time()
            result = self.plugin_system.process_data(
                node.plugin_name,
                data,
                **node.parameters
            )
            execution_time = time.time() - start_time
            
            return NodeExecutionResult(
                node_id=node.id,
                status=ExecutionStatus.COMPLETED,
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            self._logger.error(f"节点 {node.id} 执行失败: {str(e)}")
            return NodeExecutionResult(
                node_id=node.id,
                status=ExecutionStatus.FAILED,
                error=e
            )
            
    def cancel_workflow(self, workflow_id: str) -> None:
        """取消工作流执行"""
        if workflow_id in self._current_executions:
            for future in self._current_executions[workflow_id].values():
                future.cancel()
            
            # 更新被取消节点的状态
            for node_id in self._current_executions[workflow_id]:
                self._execution_results[workflow_id][node_id] = NodeExecutionResult(
                    node_id=node_id,
                    status=ExecutionStatus.CANCELLED
                )
                
    def get_execution_status(self, workflow_id: str) -> Dict[str, ExecutionStatus]:
        """获取工作流执行状态"""
        if workflow_id not in self._execution_results:
            return {}
            
        return {
            node_id: result.status
            for node_id, result in self._execution_results[workflow_id].items()
        } 