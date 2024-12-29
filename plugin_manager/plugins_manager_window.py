# plugin_manager_window.py
from typing import Optional

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                            QListWidget, QListWidgetItem, QLabel, QFileDialog, QMessageBox,
                            QTabWidget, QTextEdit, QFormLayout, QWidget, QCheckBox, QProgressDialog)
from PyQt6.QtCore import Qt, QTimer
from plugin_manager.plugin_system import PluginSystem
import os
from utils.error_handler import ErrorHandler
import logging
import traceback
from plugin_manager.plugin_config import PluginConfig
import json
from plugin_manager.plugin_permissions import PluginPermission, PluginPermissionManager
from PyQt6.QtGui import QColor
from globals import GlobalState

class PluginManagerWindow(QDialog):
    def __init__(self, plugin_system: PluginSystem, parent=None):
        super().__init__(parent)
        self.plugin_system = plugin_system
        self.setWindowTitle("插件管理")
        self.resize(600, 400)
        
        main_layout = QHBoxLayout()
        
        # 左侧插件列表区域
        left_layout = QVBoxLayout()
        
        self.plugin_list = QListWidget()
        self.plugin_list.itemSelectionChanged.connect(self.on_plugin_selected)
        left_layout.addWidget(self.plugin_list)
        
        button_layout = QHBoxLayout()
        self.load_button = QPushButton("加载插件")
        self.load_button.clicked.connect(self.load_plugin)
        button_layout.addWidget(self.load_button)
        
        self.unload_button = QPushButton("卸载插件")
        self.unload_button.clicked.connect(self.unload_plugin)
        button_layout.addWidget(self.unload_button)
        
        self.activate_button = QPushButton("激活")
        self.activate_button.clicked.connect(self.activate_plugin)
        button_layout.addWidget(self.activate_button)
        
        self.deactivate_button = QPushButton("停用")
        self.deactivate_button.clicked.connect(self.deactivate_plugin)
        button_layout.addWidget(self.deactivate_button)
        
        left_layout.addLayout(button_layout)
        
        # 右侧插件详情区域
        self.tab_widget = QTabWidget()
        
        # 基本信息标签页
        self.info_tab = QWidget()
        self.info_layout = QFormLayout()
        self.info_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.name_label = QLabel()
        self.info_layout.addRow("名称:", self.name_label)
        
        self.version_label = QLabel()
        self.info_layout.addRow("版本:", self.version_label)
        
        self.status_label = QLabel()
        self.info_layout.addRow("状态:", self.status_label)
        
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.info_layout.addRow("描述:", self.description_text)
        
        self.info_tab.setLayout(self.info_layout)
        self.tab_widget.addTab(self.info_tab, "基本信息")
        
        # 配置标签页
        self.config_tab = QWidget()
        self.config_layout = QFormLayout()
        self.config_tab.setLayout(self.config_layout)
        self.tab_widget.addTab(self.config_tab, "配置")
        
        # 添加权限管理标签页
        self.permissions_tab = QWidget()
        self.permissions_layout = QVBoxLayout()
        self.permissions_tab.setLayout(self.permissions_layout)
        self.tab_widget.addTab(self.permissions_tab, "权限管理")
        
        main_layout.addLayout(left_layout, 1)
        main_layout.addWidget(self.tab_widget, 2)
        
        self.setLayout(main_layout)
        # 初始化时加载所有插件
        self.update_plugin_list()
        
        # 添加配置管理器
        self.plugin_config = PluginConfig(os.path.join(self.plugin_system.plugin_dir, "configs"))
        
        # 初始化权限管理器
        self.permission_manager = PluginPermissionManager(
            os.path.join(self.plugin_system.plugin_dir, "permissions.json")
        )
        self.globalState = GlobalState()
        self.update_plugin_list()
    
    def update_plugin_list(self):
        """更新插件列表显示"""
        try:
            # 获取当前列表中的插件
            current_plugins = set(item.text() for item in self.plugin_list.findItems("*", Qt.MatchFlag.MatchWildcard))
            # 获取实际的插件集合
            new_plugins = set(self.plugin_system.get_all_plugins().keys())
            
            # 计算需要添加和删除的插件
            to_add = new_plugins - current_plugins
            to_remove = current_plugins - new_plugins
            
            # 删除不存在的插件
            for plugin_name in to_remove:
                items = self.plugin_list.findItems(plugin_name, Qt.MatchFlag.MatchExactly)
                for item in items:
                    self.plugin_list.takeItem(self.plugin_list.row(item))
            
            # 添加新插件
            for plugin_name in to_add:
                item = QListWidgetItem(plugin_name)
                self.plugin_list.addItem(item)
                
            # 更新所有插件的状态显示（包括新添加的和已存在的）
            for i in range(self.plugin_list.count()):
                item = self.plugin_list.item(i)
                plugin_name = item.text()
                state = self.plugin_system.get_plugin_state(plugin_name)
                
                # 设置背景色以表示状态
                if state == 'active':
                    item.setBackground(QColor(200, 255, 200))  # 浅绿色表示激活
                elif state == 'error':
                    item.setBackground(QColor(255, 200, 200))  # 浅红色表示错误
                else:
                    item.setBackground(QColor(255, 255, 255))  # 白色表示正常加载状态
                    
        except Exception as e:
            ErrorHandler.handle_error(e, self, "更新插件列表时发生错误")
    
    def load_plugin(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择插件文件",
                "",
                "Python Files (*.py)"
            )
            
            if file_path:
                # 创建进度对话框
                progress = QProgressDialog("正在加载插件...", "取消", 0, 100, self)
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.setMinimumDuration(0)
                progress.setValue(0)
                
                try:
                    # 验证插件签名
                    signature = self.get_plugin_signature(file_path)
                    if signature and not self.plugin_config.verify_signature(file_path, signature):
                        progress.setLabelText("插件签名验证失败")
                        progress.setValue(100)
                        return False
                        
                    progress.setLabelText("正在验证插件安全性...")
                    progress.setValue(20)
                    
                    plugin_name = os.path.basename(file_path)
                    target_path = os.path.join(self.plugin_system.plugin_dir, plugin_name)
                    
                    with open(file_path, 'r', encoding='utf-8') as source:
                        plugin_content = source.read()
                        
                    # 添加插件安全检查
                    if not self.verify_plugin_safety(plugin_content):
                        progress.setLabelText("插件安全检查未通过")
                        progress.setValue(100)
                        return False
                        
                    progress.setLabelText("正在复制插件文件...")
                    progress.setValue(40)
                    
                    with open(target_path, 'w', encoding='utf-8') as target:
                        target.write(plugin_content)
                        
                    progress.setLabelText("正在加载插件...")
                    progress.setValue(60)
                    
                    success = self.plugin_system.load_plugin(target_path, show_info=True)
                    
                    if success:
                        progress.setLabelText(f"插件 {plugin_name} 加载成功")
                        self.update_plugin_list()
                        self.update_plugin_details()
                        # 触发插件加载事件
                        print("触发插件加载事件")
                        self.globalState.event_bus.emit("plugin.loaded", {"plugin_name": plugin_name})
                        # 自动选择新加载的插件
                        items = self.plugin_list.findItems(plugin_name, Qt.MatchFlag.MatchExactly)
                        if items:
                            self.plugin_list.setCurrentItem(items[0])
                    else:
                        progress.setLabelText(f"插件 {plugin_name} 加载失败")
                        
                    progress.setValue(100)
                    
                finally:
                    progress.close()
                    
        except Exception as e:
            ErrorHandler.handle_error(e, self, "加载插件时发生错误")
            # 添加详细日志记录
            logging.error(f"Plugin load failed: {str(e)}\nStack trace: {traceback.format_exc()}")
            
    def verify_plugin_safety(self, plugin_content):
        # 检查是否包含危险代码
        dangerous_imports = ['os.system', 'subprocess', 'eval']
        for imp in dangerous_imports:
            if imp in plugin_content:
                return False
        return True
        
    def on_plugin_selected(self):
        """当选择插件时更新详情信息"""
        self.update_plugin_details()
        
    def update_plugin_details(self):
        """更新当前选中插件的详细信息"""
        selected_plugin = self.plugin_list.currentItem()
        if selected_plugin:
            plugin_name = selected_plugin.text()
            plugin_info = self.plugin_system.get_plugin_info(plugin_name)
            plugin_instance = self.plugin_system.get_plugin(plugin_name)
            
            # 更新基本信息
            self.name_label.setText(plugin_info.name)
            self.version_label.setText(plugin_info.version)
            self.status_label.setText(self.plugin_system.get_plugin_state(plugin_name))
            self.description_text.setText(plugin_info.description)
            
            # 更新配置信息
            self.update_config_tab(plugin_instance)
    
    def unload_plugin(self):
        try:
            selected_plugin = self.plugin_list.currentItem()
            if selected_plugin:
                plugin_name = selected_plugin.text()
                if self.plugin_system.unload_plugin(plugin_name):
                    ErrorHandler.handle_info(f"插件 {plugin_name} 已成功卸载", self)
                    self.update_plugin_list()
                    self.clear_plugin_details()
                    print("触发插件卸载事件")
                    self.globalState.event_bus.emit("plugin.unloaded", {"plugin_name": plugin_name})
                else:
                    ErrorHandler.handle_warning(f"插件 {plugin_name} 卸载失败", self)
            else:
                ErrorHandler.handle_warning("请选择一个插件", self)
        except Exception as e:
            ErrorHandler.handle_error(e, self, "卸载插件时发生错误")
            
    def activate_plugin(self):
        """激活选中的插件"""
        selected_plugin = self.plugin_list.currentItem()
        if not selected_plugin:
            ErrorHandler.handle_warning("请选择一个插件", self)
            return
        
        plugin_name = selected_plugin.text()
        try:
            # 获取插件实例
            plugin = self.plugin_system.get_plugin(plugin_name)
            if not plugin:
                ErrorHandler.handle_warning(f"找不到插件 {plugin_name}", self)
                return
            
            # 显示进度对话框
            progress = QProgressDialog("正在激活插件...", None, 0, 0, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setCancelButton(None)  # 禁用取消按钮
            progress.show()
            
            try:
                    # 激活插件
                    if self.plugin_system.activate_plugin(plugin_name):
                        ErrorHandler.handle_info(f"插件 {plugin_name} 已激活", self)
                        # 更新插件状态显示
                        self.update_plugin_list()
                        # 更新插件详情
                        self.update_plugin_details()
                        # 触发插件激活事件
                        print("触发插件激活事件")
                        self.globalState.event_bus.emit('plugin.activated', {'plugin_name': plugin_name})
                    else:
                        ErrorHandler.handle_warning(f"插件 {plugin_name} 激活失败", self)
            finally:
                # 确保关闭进度对话框
                progress.close()
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, f"激活插件 {plugin_name} 时发生错误")

    def deactivate_plugin(self):
        """停用选中的插件"""
        selected_plugin = self.plugin_list.currentItem()
        if not selected_plugin:
            ErrorHandler.handle_warning("请选择一个插件", self)
            return
        
        plugin_name = selected_plugin.text()
        try:
            # 显示进度对话框
            progress = QProgressDialog("正在停用插件...", None, 0, 0, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setCancelButton(None)
            progress.show()
            
            try:
                    # 停用插件
                    if self.plugin_system.deactivate_plugin(plugin_name):
                        ErrorHandler.handle_info(f"插件 {plugin_name} 已停用", self)
                        # 更新插件状态显示
                        self.update_plugin_list()
                        # 更新插件详情
                        self.update_plugin_details()
                        # 触发插件停用事件
                        print("触发插件停用事件")
                        self.globalState.event_bus.emit('plugin.deactivated', {'plugin_name': plugin_name})
                    else:
                        ErrorHandler.handle_warning(f"插件 {plugin_name} 停用失败", self)
            finally:
                # 确保关闭进度对话框
                progress.close()
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, f"停用插件 {plugin_name} 时发生错误")
            
    def update_config_tab(self, plugin_instance):
        """更新配置标签页内容"""
        # 先清除旧的配置项
        while self.config_layout.count():
            item = self.config_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            
        # 如果插件实例存在，添加新的配置项
        if plugin_instance is not None:
            config = plugin_instance.get_configuration()
            for key, value in config.items():
                label = QLabel(str(key))
                value_widget = QTextEdit(str(value))
                value_widget.textChanged.connect(
                    lambda: self.save_plugin_config(plugin_instance, key, value_widget.toPlainText())
                )
                self.config_layout.addRow(label, value_widget)
            
    def save_plugin_config(self, plugin_instance, key, value):
        """保存插件配置"""
        plugin_name = plugin_instance.__class__.__name__
        config = self.plugin_config.get_config(plugin_name)
        config[key] = value
        self.plugin_config.save_config(plugin_name, config)
        
        # 通知插件配置已更新
        if hasattr(plugin_instance, 'on_config_changed'):
            plugin_instance.on_config_changed(key, value)
            
    def clear_plugin_details(self):
        """清除插件详情信息"""
        self.name_label.clear()
        self.version_label.clear()
        self.status_label.clear()
        self.description_text.clear()
        self.update_config_tab(None)

    def check_plugin_dependencies(self, plugin_name):
        # 检查插件依赖关系
        pass

    def get_plugin_signature(self, plugin_path: str) -> Optional[str]:
        """获取插件签名"""
        signature_file = os.path.join(self.plugin_system.plugin_dir, "signatures.json")
        if os.path.exists(signature_file):
            with open(signature_file, 'r') as f:
                signatures = json.load(f)
                return signatures.get(os.path.basename(plugin_path))
        return None
        
    def save_plugin_signature(self, plugin_name: str, signature: str):
        """保存插件签名"""
        signature_file = os.path.join(self.plugin_system.plugin_dir, "signatures.json")
        signatures = {}
        if os.path.exists(signature_file):
            with open(signature_file, 'r') as f:
                signatures = json.load(f)
        signatures[plugin_name] = signature
        with open(signature_file, 'w') as f:
            json.dump(signatures, f, indent=4)

    def update_permissions_tab(self, plugin_name: str):
        """更新权限管理标签页"""
        # 清除现有内容
        while self.permissions_layout.count():
            item = self.permissions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            
        # 添加权限复选框
        for permission in PluginPermission:
            checkbox = QCheckBox(permission.value)
            checkbox.setChecked(
                self.permission_manager.has_permission(plugin_name, permission)
            )
            checkbox.stateChanged.connect(
                lambda state, p=permission: self.on_permission_changed(plugin_name, p, state)
            )
            self.permissions_layout.addWidget(checkbox)
            
    def on_permission_changed(self, plugin_name: str, permission: PluginPermission, state: int):
        """处理权限变更"""
        if state == Qt.CheckState.Checked.value:
            self.permission_manager.grant_permission(plugin_name, permission)
        else:
            self.permission_manager.revoke_permission(plugin_name, permission)
