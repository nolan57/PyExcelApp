from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QListWidget, QGraphicsView, QGraphicsScene,
                           QDialog, QLabel, QLineEdit, QComboBox, QFormLayout,
                           QMessageBox, QInputDialog)
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPen, QColor, QPainter, QBrush
from PyQt6.QtWidgets import QGraphicsItem

from ..models.workflow_model import Workflow, WorkflowNode, WorkflowType
from ..core.workflow_manager import WorkflowManager
from typing import Dict, Optional
import math

class NodeGraphicsItem(QGraphicsItem):
    """节点图形项"""
    
    def __init__(self, node: WorkflowNode, parent=None):
        super().__init__(parent)
        self.node = node
        self.width = 150
        self.height = 80
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        
    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)
        
    def paint(self, painter: QPainter, option, widget):
        # 绘制节点外框
        pen = QPen(QColor('black'))
        if self.isSelected():
            pen.setWidth(2)
        painter.setPen(pen)
        
        # 根据节点类型设置不同颜色
        if self.node.condition:
            brush = QColor(255, 255, 200)  # 浅黄色表示条件节点
        else:
            brush = QColor(200, 255, 200)  # 浅绿色表示普通节点
        painter.setBrush(brush)
        
        # 绘制圆角矩形
        painter.drawRoundedRect(0, 0, self.width, self.height, 10, 10)
        
        # 绘制节点文本
        painter.drawText(10, 20, self.node.name)
        painter.drawText(10, 40, f"插件: {self.node.plugin_name}")
        if self.node.condition:
            painter.drawText(10, 60, f"条件: {self.node.condition}")

class ConnectionGraphicsItem(QGraphicsItem):
    """连接线图形项"""
    
    def __init__(self, start_node: NodeGraphicsItem, end_node: NodeGraphicsItem):
        super().__init__()
        self.start_node = start_node
        self.end_node = end_node
        
    def boundingRect(self):
        return QRectF(self.start_node.pos(), self.end_node.pos())
        
    def paint(self, painter: QPainter, option, widget):
        # 绘制箭头连接线
        start_pos = self.start_node.pos() + QPointF(self.start_node.width/2, self.start_node.height)
        end_pos = self.end_node.pos() + QPointF(self.end_node.width/2, 0)
        
        painter.setPen(QPen(QColor('black')))
        painter.drawLine(start_pos, end_pos)
        
        # 绘制箭头
        arrow_size = 10
        angle = math.atan2(end_pos.y() - start_pos.y(), end_pos.x() - start_pos.x())
        arrow_p1 = end_pos - QPointF(
            math.cos(angle - math.pi/6) * arrow_size,
            math.sin(angle - math.pi/6) * arrow_size
        )
        arrow_p2 = end_pos - QPointF(
            math.cos(angle + math.pi/6) * arrow_size,
            math.sin(angle + math.pi/6) * arrow_size
        )
        painter.drawLine(end_pos, arrow_p1)
        painter.drawLine(end_pos, arrow_p2)

class NodeEditDialog(QDialog):
    """节点编辑对话框"""
    
    def __init__(self, plugin_system, parent=None):
        super().__init__(parent)
        self.plugin_system = plugin_system
        self.setWindowTitle("编辑节点")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QFormLayout()
        
        # 节点名称
        self.name_edit = QLineEdit()
        layout.addRow("节点名称:", self.name_edit)
        
        # 插件选择
        self.plugin_combo = QComboBox()
        self.plugin_combo.addItems(self.plugin_system.get_all_plugins().keys())
        layout.addRow("选择插件:", self.plugin_combo)
        
        # 条件表达式
        self.condition_edit = QLineEdit()
        layout.addRow("条件表达式:", self.condition_edit)
        
        # 确定取消按钮
        buttons = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)
        
        self.setLayout(layout)

class WorkflowEditorWindow(QMainWindow):
    """工作流编辑器窗口"""
    
    def __init__(self, workflow_manager: WorkflowManager):
        super().__init__()
        self.workflow_manager = workflow_manager
        self.current_workflow: Optional[Workflow] = None
        self.node_items: Dict[str, NodeGraphicsItem] = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("工作流编辑器")
        self.resize(800, 600)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        layout = QHBoxLayout(central_widget)
        
        # 左侧工作流列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.workflow_list = QListWidget()
        self.workflow_list.itemClicked.connect(self.on_workflow_selected)
        left_layout.addWidget(self.workflow_list)
        
        # 工作流操作按钮
        workflow_buttons = QHBoxLayout()
        new_workflow_btn = QPushButton("新建工作流")
        new_workflow_btn.clicked.connect(self.create_new_workflow)
        delete_workflow_btn = QPushButton("删除工作流")
        delete_workflow_btn.clicked.connect(self.delete_workflow)
        workflow_buttons.addWidget(new_workflow_btn)
        workflow_buttons.addWidget(delete_workflow_btn)
        left_layout.addLayout(workflow_buttons)
        
        layout.addWidget(left_panel)
        
        # 右侧节点编辑区域
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 节点操作按钮
        node_buttons = QHBoxLayout()
        add_node_btn = QPushButton("添加节点")
        add_node_btn.clicked.connect(self.add_node)
        delete_node_btn = QPushButton("删除节点")
        delete_node_btn.clicked.connect(self.delete_node)
        node_buttons.addWidget(add_node_btn)
        node_buttons.addWidget(delete_node_btn)
        right_layout.addLayout(node_buttons)
        
        # 节点图形视图
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        right_layout.addWidget(self.view)
        
        layout.addWidget(right_panel)
        
        # 更新工作流列表
        self.update_workflow_list()
        
    def update_workflow_list(self):
        """更新工作流列表"""
        self.workflow_list.clear()
        for workflow in self.workflow_manager._workflows.values():
            self.workflow_list.addItem(workflow.name)
            
    def create_new_workflow(self):
        """创建新工作流"""
        name, ok = QInputDialog.getText(self, "新建工作流", "工作流名称:")
        if ok and name:
            workflow = self.workflow_manager.create_workflow(
                name=name,
                description="",
                workflow_type=WorkflowType.SEQUENTIAL
            )
            self.update_workflow_list()
            
    def add_node(self):
        """添加新节点"""
        if not self.current_workflow:
            QMessageBox.warning(self, "警告", "请先选择工作流")
            return
            
        dialog = NodeEditDialog(self.workflow_manager.plugin_system, self)
        if dialog.exec():
            node = WorkflowNode(
                id=f"node_{len(self.current_workflow.nodes) + 1}",
                name=dialog.name_edit.text(),
                plugin_name=dialog.plugin_combo.currentText(),
                condition=dialog.condition_edit.text() or None
            )
            self.workflow_manager.add_node(self.current_workflow.id, node)
            self.update_node_view()
            
    def update_node_view(self):
        """更新节点视图"""
        self.scene.clear()
        self.node_items.clear()
        
        if not self.current_workflow:
            return
            
        # 创建节点图形项
        for node in self.current_workflow.nodes.values():
            node_item = NodeGraphicsItem(node)
            self.scene.addItem(node_item)
            self.node_items[node.id] = node_item
            
        # 创建连接线
        for node in self.current_workflow.nodes.values():
            for next_node_id in node.next_nodes:
                if next_node_id in self.node_items:
                    connection = ConnectionGraphicsItem(
                        self.node_items[node.id],
                        self.node_items[next_node_id]
                    )
                    self.scene.addItem(connection)
                    
        # 自动布局节点
        self.layout_nodes()
        
    def layout_nodes(self):
        """简单的自动布局"""
        x, y = 50, 50
        for node_item in self.node_items.values():
            node_item.setPos(x, y)
            x += 200
            if x > 600:
                x = 50
                y += 150 