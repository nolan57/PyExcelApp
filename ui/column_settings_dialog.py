from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QMessageBox, QGridLayout)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor

class ColumnSettingsDialog(QDialog):
    # 定义信号，用于通知外部需要获取单元格位置
    request_cell_position = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置列和行")
        # 设置为非模态对话框，允许与其他窗口交互
        self.setWindowModality(Qt.WindowModality.NonModal)
        # 设置窗口标志，保持在最前面
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        # 初始化属性值
        self.settings = {
            "零件号列": {"value": 2, "type": "column"},
            "零件名列": {"value": 3, "type": "column"},
            "价格列": {"value": 4, "type": "column"},
            "系数列": {"value": 19, "type": "column"},
            "起始行": {"value": 2, "type": "row"}
        }
        
        self.current_setting = None
        self.buttons = {}  # 存储按钮引用
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 添加说明标签
        hint_label = QLabel("点击\"设置\"按钮后，直接点击表格中的目标单元格")
        hint_label.setStyleSheet("color: gray;")
        layout.addWidget(hint_label)
        
        # 创建网格布局用于显示设置项
        grid = QGridLayout()
        
        # 添加标题行
        grid.addWidget(QLabel("设置项"), 0, 0)
        grid.addWidget(QLabel("当前值"), 0, 1)
        grid.addWidget(QLabel("操作"), 0, 2)
        
        # 为每个设置项创建一行
        for row, (name, data) in enumerate(self.settings.items(), 1):
            # 名称标签
            name_label = QLabel(name)
            grid.addWidget(name_label, row, 0)
            
            # 值标签
            value_label = QLabel(str(data["value"]))
            value_label.setObjectName(f"value_{name}")
            grid.addWidget(value_label, row, 1)
            
            # 设置按钮
            set_btn = QPushButton("设置")
            set_btn.setObjectName(f"set_btn_{name}")
            set_btn.setToolTip(f"点击后选择{name}的单元格")
            set_btn.clicked.connect(lambda checked, n=name: self.on_set_clicked(n))
            grid.addWidget(set_btn, row, 2)
            self.buttons[name] = set_btn  # 保存按钮引用
        
        layout.addLayout(grid)
        
        # 添加底部按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.on_cancel)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
    
    def on_set_clicked(self, setting_name):
        """当点击设置按钮时，更新当前设置项并发出信号"""
        # 重置之前按钮的样式
        if self.current_setting and self.current_setting in self.buttons:
            self.buttons[self.current_setting].setStyleSheet("")
        
        self.current_setting = setting_name
        # 高亮当前按钮
        if setting_name in self.buttons:
            self.buttons[setting_name].setStyleSheet(
                "QPushButton { background-color: #4A90E2; color: white; }"
            )
        
        # 发送信号请求单元格位置
        self.request_cell_position.emit(setting_name)
    
    def update_value(self, row, col):
        """更新设置值并重置按钮样式"""
        if self.current_setting and self.current_setting in self.settings:
            setting_type = self.settings[self.current_setting]["type"]
            value = row if setting_type == "row" else col
            self.settings[self.current_setting]["value"] = value
            
            # 更新显示的值
            value_label = self.findChild(QLabel, f"value_{self.current_setting}")
            if value_label:
                value_label.setText(str(value))
            
            # 重置按钮样式
            if self.current_setting in self.buttons:
                self.buttons[self.current_setting].setStyleSheet("")
            
            self.current_setting = None
    
    def on_cancel(self):
        reply = QMessageBox.question(
            self,
            "确认",
            "是否使用默认值？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.accept()
        else:
            self.reject()
    
    def get_values(self):
        return {
            "part_code_column": self.settings["零件号列"]["value"],
            "part_name_column": self.settings["零件名列"]["value"],
            "price_column": self.settings["价格列"]["value"],
            "xs_column": self.settings["系数列"]["value"],
            "start_row": self.settings["起始行"]["value"]
        }
