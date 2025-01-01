# plugin_manager_window.py
from typing import Optional

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                            QListWidget, QListWidgetItem, QLabel, QFileDialog, QMessageBox,
                            QTabWidget, QTextEdit, QFormLayout, QWidget, QCheckBox, QProgressDialog,
                            QSpinBox, QDoubleSpinBox, QLineEdit, QMainWindow)
from PyQt6.QtCore import Qt, QTimer
from ..core.plugin_system import PluginSystem
import os
from utils.error_handler import ErrorHandler
import logging
import traceback
from plugin_manager.utils.plugin_config import PluginConfig
import json
from plugin_manager.features.plugin_permissions import PluginPermission, PluginPermissionManager
from PyQt6.QtGui import QColor
from globals import GlobalState
import logging
from ..workflow.ui.workflow_editor import WorkflowEditorWindow
from ..workflow.core.workflow_manager import WorkflowManager

class PluginManagerWindow(QDialog):
    def __init__(self, plugin_system: PluginSystem, parent=None):
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self.plugin_system = plugin_system
        self.setWindowTitle("插件管理")
        self.resize(600, 400)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # === 插件管理选项卡 ===
        plugin_tab = QWidget()
        plugin_layout = QHBoxLayout(plugin_tab)  # 使用水平布局
        
        # 左侧插件列表区域
        left_layout = QVBoxLayout()
        
        self.plugin_list = QListWidget()
        self.plugin_list.itemSelectionChanged.connect(self.on_plugin_selected)
        left_layout.addWidget(self.plugin_list)
        
        # 插件操作按钮
        button_layout = QHBoxLayout()
        self.load_button = QPushButton("加载插件")
        self.load_button.clicked.connect(self.load_plugin)
        button_layout.addWidget(self.load_button)
        
        self.unload_button = QPushButton("卸载插件")
        self.unload_button.clicked.connect(self.unload_selected_plugin)
        button_layout.addWidget(self.unload_button)
        
        self.activate_button = QPushButton("激活")
        self.activate_button.clicked.connect(self.activate_plugin)
        button_layout.addWidget(self.activate_button)
        
        self.deactivate_button = QPushButton("停用")
        self.deactivate_button.clicked.connect(self.deactivate_plugin)
        button_layout.addWidget(self.deactivate_button)
        
        left_layout.addLayout(button_layout)
        plugin_layout.addLayout(left_layout, 1)
        
        # 右侧插件详情区域
        right_layout = QVBoxLayout()
        
        # 插件详情选项卡
        self.detail_tab_widget = QTabWidget()
        
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
        self.detail_tab_widget.addTab(self.info_tab, "基本信息")
        
        # 配置标签页
        self.config_tab = QWidget()
        self.config_layout = QFormLayout()
        self.config_tab.setLayout(self.config_layout)
        self.detail_tab_widget.addTab(self.config_tab, "配置")
        
        # 权限管理标签页
        self.permissions_tab = QWidget()
        self.permissions_layout = QVBoxLayout()
        self.permissions_tab.setLayout(self.permissions_layout)
        self.detail_tab_widget.addTab(self.permissions_tab, "权限管理")
        
        right_layout.addWidget(self.detail_tab_widget)
        plugin_layout.addLayout(right_layout, 2)
        
        self.tab_widget.addTab(plugin_tab, "插件管理")
        
        # === 工作流选项卡 ===
        workflow_tab = QWidget()
        workflow_layout = QVBoxLayout(workflow_tab)
        
        # 工作流列表
        self.workflow_list = QListWidget()
        workflow_layout.addWidget(self.workflow_list)
        
        # 工作流操作按钮
        workflow_buttons = QHBoxLayout()
        
        new_workflow_btn = QPushButton("新建工作流")
        new_workflow_btn.clicked.connect(self.create_workflow)
        workflow_buttons.addWidget(new_workflow_btn)
        
        edit_workflow_btn = QPushButton("编辑工作流")
        edit_workflow_btn.clicked.connect(self.edit_workflow)
        workflow_buttons.addWidget(edit_workflow_btn)
        
        execute_workflow_btn = QPushButton("执行工作流")
        execute_workflow_btn.clicked.connect(self.execute_workflow)
        workflow_buttons.addWidget(execute_workflow_btn)
        
        delete_workflow_btn = QPushButton("删除工作流")
        delete_workflow_btn.clicked.connect(self.delete_workflow)
        workflow_buttons.addWidget(delete_workflow_btn)
        
        workflow_layout.addLayout(workflow_buttons)
        self.tab_widget.addTab(workflow_tab, "工作流")
        
        # 初始化工作流管理器
        self.workflow_manager = WorkflowManager(
            plugin_system=plugin_system,
            workflow_dir=f"{plugin_system.plugin_dir}/workflows",
            encryption=plugin_system.config_encryption
        )
        
        # 初始化时加载所有插件
        self.update_plugin_list()
        self.update_workflow_list()
        
        # 添加配置管理器
        self.plugin_config = PluginConfig(os.path.join(self.plugin_system.plugin_dir, "configs"))
        
        # 使用插件系统的权限管理器
        self.permission_manager = self.plugin_system.permission_manager
        self.permission_manager.set_plugin_config(self.plugin_config)
        
        # 订阅插件事件
        self.plugin_system._event_bus.subscribe('plugin.started', self._on_plugin_started)
        self.plugin_system._event_bus.subscribe('plugin.stopped', self._on_plugin_stopped)
    
    def _on_plugin_started(self, event_data):
        """插件启动时的处理"""
        plugin_name = event_data['plugin_name']
        # 更新UI状态
        self._update_plugin_status(plugin_name, "running")
        
    def _on_plugin_stopped(self, event_data):
        """插件停止时的处理"""
        plugin_name = event_data['plugin_name']
        # 更新UI状态
        self._update_plugin_status(plugin_name, "stopped")
    
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
        """加载新插件"""
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
                    
                    # 获取不带.py后缀的插件名
                    plugin_name = os.path.splitext(os.path.basename(file_path))[0]
                    target_path = os.path.join(self.plugin_system.plugin_dir, f"{plugin_name}.py")
                    
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
                    
                    success = self.plugin_system.load_plugin(plugin_name)
                    
                    if success:
                        progress.setLabelText(f"插件 {plugin_name} 加载成功")
                        self.update_plugin_list()
                        self.update_plugin_details()
                        # 触发插件加载事件
                        self._logger.info("触发插件加载事件")
                        self.globalState.event_bus.emit("plugin.loaded", {"plugin_name": plugin_name})
                        # 自动选择新加载的插件
                        items = self.plugin_list.findItems(plugin_name, Qt.MatchFlag.MatchExactly)
                        if items:
                            self._logger.debug(f"Selecting newly loaded plugin: {plugin_name}")
                            self.plugin_list.setCurrentItem(items[0])
                            self.plugin_list.scrollToItem(items[0])
                            self._logger.debug("New plugin selected and scrolled into view")
                    else:
                        progress.setLabelText(f"插件 {plugin_name} 加载失败")
                finally:
                    # 确保关闭进度对话框
                    progress.close()
        except Exception as e:
            ErrorHandler.handle_error(e, self, "加载插件失败")
    
    def verify_plugin_safety(self, plugin_content):
        # 检查是否包含危险代码
        dangerous_imports = ['os.system', 'subprocess', 'eval']
        for imp in dangerous_imports:
            if imp in plugin_content:
                return False
        return True
        
    def on_plugin_selected(self):
        """当选择插件时更新详情信息"""
        self._logger.debug("on_plugin_selected called")
        self.update_plugin_details()
        
    def update_plugin_details(self):
        """更新当前选中插件的详细信息"""
        self._logger.debug("update_plugin_details called")
        selected_plugin = self.plugin_list.currentItem()
        if selected_plugin:
            plugin_name = selected_plugin.text()
            self._logger.debug(f"Selected plugin: {plugin_name}")
            
            plugin_info = self.plugin_system.get_plugin_info(plugin_name)
            plugin_instance = self.plugin_system.get_plugin(plugin_name)
            
            # 更新基本信息
            self._logger.debug("Updating basic info...")
            self.name_label.setText(plugin_info.name)
            self.version_label.setText(plugin_info.version)
            plugin_state = self.plugin_system.get_plugin_state(plugin_name)
            self.status_label.setText(plugin_state.value if plugin_state else "未知")
            self.description_text.setText(plugin_info.description)
            
            # 更新配置信息
            self._logger.debug("Updating config tab...")
            self.update_config_tab(plugin_instance)
            
            # 更新权限信息
            self._logger.debug("Updating permissions tab...")
            config = self.plugin_system.get_plugin_config(plugin_name)
            self._logger.debug(f"Plugin config: {config}")
            self.update_permissions_tab(plugin_name)
            self._logger.debug("Permissions tab updated")
        else:
            self._logger.debug("No plugin selected")
    
    def unload_selected_plugin(self):
        """卸载选中的插件"""
        current_item = self.plugin_list.currentItem()
        if current_item:
            plugin_name = current_item.text()
            try:
                if self.plugin_system.unload_plugin(plugin_name):
                    ErrorHandler.handle_info(f"插件 {plugin_name} 已卸载", self)
                    # 从列表中移除
                    self.plugin_list.takeItem(self.plugin_list.row(current_item))
                    # 清除详情
                    self.clear_plugin_details()
                else:
                    ErrorHandler.handle_warning(f"卸载插件 {plugin_name} 失败", self)
            except Exception as e:
                ErrorHandler.handle_error(e, self, f"卸载插件 {plugin_name} 时发生错误")
    
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
                # 检查插件所需权限，只提示尚未通过复选框授予的权限
                required_permissions = plugin.get_required_permissions()
                self._logger.info(f"激活插件时检查 插件 {plugin_name} 所需权限: {required_permissions}")
                self._logger.info(f"激活插件时检查 插件 {plugin_name} 已授予权限: {self.permission_manager.get_granted_permissions(plugin_name)}")
                missing_permissions = [
                    perm for perm in required_permissions
                    if not perm in self.permission_manager.get_granted_permissions(plugin_name)
                ]
                
                if missing_permissions:
                    ErrorHandler.handle_info(
                        f"插件 {plugin_name} 需要以下权限: {', '.join(p.name for p in missing_permissions)}", 
                        self
                    )
                
                # 激活插件
                if self.plugin_system.activate_plugin(plugin_name):
                    # ErrorHandler.handle_info(f"插件 {plugin_name} 已激活", self)
                    self._logger.info(f"插件 {plugin_name} 激活成功")
                    progress.setLabelText(f"插件 {plugin_name} 激活成功")
                    progress.setValue(100)
                    progress.close()
                    # 更新插件状态显示
                    self.update_plugin_list()
                    # 更新插件详情
                    self.update_plugin_details()
                    # 触发插件激活事件
                    self._logger.info("触发插件激活事件")
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
                        self._logger.info("触发插件停用事件")
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
            config = plugin_instance.get_config_schema()
            current_config = plugin_instance.get_configuration()
            
            # 确保所有必需的配置项都有默认值
            for key, field_schema in config.items():
                if field_schema.get('required', False) and key not in current_config:
                    current_config[key] = field_schema.get('default')
            
            for key, field_schema in config.items():
                label = QLabel(field_schema.get('description', key))
                current_value = current_config.get(key, field_schema.get('default', ''))
                
                # 根据字段类型创建合适的输入控件
                if field_schema.get('type') == int:
                    value_widget = QSpinBox()
                    value_widget.setValue(int(current_value))
                elif field_schema.get('type') == float:
                    value_widget = QDoubleSpinBox()
                    value_widget.setValue(float(current_value))
                else:
                    value_widget = QLineEdit(str(current_value))
                
                # 连接信号
                value_widget.textChanged.connect(
                    lambda text, k=key: self.save_plugin_config(plugin_instance, k, text)
                )
                self.config_layout.addRow(label, value_widget)
        
    def save_plugin_config(self, plugin_instance, key, value):
        """保存插件配置"""
        try:
            config = self.plugin_system.config.get_config(plugin_instance.get_name())
            # 获取配置模式
            schema = plugin_instance.get_config_schema()
            
            # 确保所有必需的配置项都存在
            for field_key, field_schema in schema.items():
                if field_schema.get('required', False) and field_key not in config:
                    config[field_key] = field_schema.get('default')
            
            # 更新当前配置项
            config[key] = value
            
            # 转换类型
            if schema[key].get('type') == int:
                config[key] = int(value)
            elif schema[key].get('type') == float:
                config[key] = float(value)
            
            self.plugin_system.set_plugin_config(plugin_instance.get_name(), config)
            
            # 通知插件配置已更新
            if hasattr(plugin_instance, 'on_config_changed'):
                plugin_instance.on_config_changed(key, value)
            
            ErrorHandler.handle_info("配置已保存", self)
        except Exception as e:
            ErrorHandler.handle_error(e, self, "保存配置时发生错误")

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
        
        # 获取插件当前的权限状态
        saved_permissions = self.plugin_system.permission_manager.get_granted_permissions(plugin_name)
        
        # 按组显示权限
        permission_groups = {
            "文件操作": [
                PluginPermission.FILE_READ,
                PluginPermission.FILE_WRITE,
            ],
            "数据操作": [
                PluginPermission.DATA_READ,
                PluginPermission.DATA_WRITE,
            ],
            "其他": [
                PluginPermission.UI_MODIFY,
                PluginPermission.NETWORK,
                PluginPermission.SYSTEM_EXEC,
            ]
        }
        
        # 添加分组和权限复选框
        for group_name, permissions in permission_groups.items():
            group_label = QLabel(f"<b>{group_name}</b>")
            self.permissions_layout.addWidget(group_label)
            
            for permission in permissions:
                checkbox = QCheckBox(permission.name)
                checkbox.setChecked(
                    permission in saved_permissions
                )
                checkbox.stateChanged.connect(
                    lambda state, p=permission: self.on_permission_changed(plugin_name, p, state)
                )
                # 添加权限描述
                description = QLabel(f"<small>{self.get_permission_description(permission)}</small>")
                description.setWordWrap(True)
                self.permissions_layout.addWidget(checkbox)
                self.permissions_layout.addWidget(description)
        
        # 添加间隔
        self.permissions_layout.addStretch()
            
    def on_permission_changed(self, plugin_name: str, permission: PluginPermission, state: int):
        """处理权限变更"""
        try:
            if state == Qt.CheckState.Checked.value:
                self.plugin_system.permission_manager.grant_permission(plugin_name, permission)
                ErrorHandler.handle_info(f"已为插件 {plugin_name} 授予 {permission.name} 权限", self)
            else:
                self.plugin_system.permission_manager.revoke_permission(plugin_name, permission)
                ErrorHandler.handle_info(f"已为插件 {plugin_name} 撤销 {permission.name} 权限", self)
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "保存权限更改时发生错误")
            
    def get_permission_description(self, permission: PluginPermission) -> str:
        """获取权限描述"""
        return PluginPermission.get_permission_description(permission)

    def _setup_config_tab(self, plugin_name: str):
        """设置配置标签页"""
        self.config_tab = QWidget()
        config_layout = QFormLayout()
        self.config_tab.setLayout(config_layout)
        
        # 获取插件配置模式
        plugin = self.plugin_system.get_plugin(plugin_name)
        if not plugin:
            return
            
        schema = plugin.get_config_schema()
        # 获取当前配置
        current_config = self.plugin_system.config.get_config(plugin_name)
        
        # 为每个配置项创建输入控件
        for key, field_schema in schema.items():
            label = QLabel(field_schema.get('description', key))
            
            # 根据字段类型创建不同的输入控件
            if field_schema.get('type') == int:
                input_widget = QSpinBox()
                input_widget.setValue(current_config.get(key, field_schema.get('default', 0)))
            elif field_schema.get('type') == float:
                input_widget = QDoubleSpinBox()
                input_widget.setValue(current_config.get(key, field_schema.get('default', 0.0)))
            else:
                input_widget = QLineEdit()
                input_widget.setText(str(current_config.get(key, field_schema.get('default', ''))))
            
            # 保存对应的配置键名
            input_widget.setProperty('config_key', key)
            input_widget.setProperty('config_type', field_schema.get('type', str))
            
            # 连接信号
            if isinstance(input_widget, (QSpinBox, QDoubleSpinBox)):
                input_widget.valueChanged.connect(
                    lambda value, w=input_widget: self._on_config_changed(plugin_name, w)
                )
            else:
                input_widget.textChanged.connect(
                    lambda text, w=input_widget: self._on_config_changed(plugin_name, w)
                )
            
            config_layout.addRow(label, input_widget)
            
        # 添加保存按钮
        save_button = QPushButton("保存配置")
        save_button.clicked.connect(lambda: self._save_plugin_config(plugin_name))
        config_layout.addRow("", save_button)
        
    def _on_config_changed(self, plugin_name: str, widget: QWidget):
        """处理配置变更"""
        try:
            key = widget.property('config_key')
            value_type = widget.property('config_type')
            
            # 获取值
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                value = widget.value()
            else:
                value = widget.text()
                # 转换类型
                if value_type == int:
                    value = int(value)
                elif value_type == float:
                    value = float(value)
            
            # 更新配置
            config = self.plugin_system.config.get_config(plugin_name)
            config[key] = value
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "更新配置时发生错误")
            
    def _save_plugin_config(self, plugin_name: str):
        """保存插件配置"""
        try:
            config = self.plugin_system.config.get_config(plugin_name)
            self.plugin_system.set_plugin_config(plugin_name, config)
            ErrorHandler.handle_info("配置已保存", self)
        except Exception as e:
            ErrorHandler.handle_error(e, self, "保存配置时发生错误")
        
    def update_workflow_list(self):
        """更新工作流列表"""
        self.workflow_list.clear()
        for workflow in self.workflow_manager._workflows.values():
            self.workflow_list.addItem(workflow.name)
            
    def create_workflow(self):
        """创建新工作流"""
        editor = WorkflowEditorWindow(self.workflow_manager)
        if editor.exec():
            self.update_workflow_list()
            
    def edit_workflow(self):
        """编辑选中的工作流"""
        current_item = self.workflow_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择工作流")
            return
            
        workflow_name = current_item.text()
        workflow = next(
            (w for w in self.workflow_manager._workflows.values() 
             if w.name == workflow_name),
            None
        )
        
        if workflow:
            editor = WorkflowEditorWindow(self.workflow_manager)
            editor.load_workflow(workflow)
            if editor.exec():
                self.update_workflow_list()
                
    def execute_workflow(self):
        """执行选中的工作流"""
        current_item = self.workflow_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择工作流")
            return
            
        workflow_name = current_item.text()
        workflow = next(
            (w for w in self.workflow_manager._workflows.values() 
             if w.name == workflow_name),
            None
        )
        
        if workflow:
            from ..workflow.ui.workflow_execution import WorkflowExecutionWindow
            execution_window = WorkflowExecutionWindow(
                self.workflow_manager.executor,
                workflow.id
            )
            execution_window.show()
            
    def delete_workflow(self):
        """删除选中的工作流"""
        current_item = self.workflow_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择工作流")
            return
            
        workflow_name = current_item.text()
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除工作流 {workflow_name} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            workflow = next(
                (w for w in self.workflow_manager._workflows.values() 
                 if w.name == workflow_name),
                None
            )
            if workflow:
                self.workflow_manager.delete_workflow(workflow.id)
                self.update_workflow_list()
