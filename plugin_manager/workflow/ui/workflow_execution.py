# plugin_manager/workflow/ui/workflow_execution_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QPushButton, QProgressBar, QLabel)
from ..core.workflow_executor import WorkflowExecutor, ExecutionStatus

class WorkflowExecutionWindow(QMainWindow):
    """工作流执行窗口"""
    
    def __init__(self, workflow_executor: WorkflowExecutor, workflow_id: str):
        super().__init__()
        self.workflow_executor = workflow_executor
        self.workflow_id = workflow_id
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("工作流执行")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 状态显示
        self.status_label = QLabel("准备执行...")
        layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # 节点状态列表
        self.node_status_layout = QVBoxLayout()
        layout.addLayout(self.node_status_layout)
        
        # 控制按钮
        self.cancel_button = QPushButton("取消执行")
        self.cancel_button.clicked.connect(self.cancel_execution)
        layout.addWidget(self.cancel_button)