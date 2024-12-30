from typing import Optional, Dict, Any

import openpyxl
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QToolBar, QFileDialog, QMessageBox, QTableView, QTabWidget, QInputDialog, QWidget, \
    QHBoxLayout, QProgressDialog

from globals import GlobalState
from plugin_manager.plugins_manager_window import PluginManagerWindow
from utils.error_handler import ErrorHandler
import logging


def get_current_table_view(tab_widget: QTabWidget) -> Optional[QTableView]:
    """获取当前活动的表格视图"""
    current_index = tab_widget.currentIndex()
    current_widget = tab_widget.widget(current_index)
    
    if isinstance(current_widget, QTableView):
        return current_widget
    else:
        return None

class ToolBar(QToolBar):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._open_file_connected = None
        self.plugin_system = None
        self.setMovable(False)
        self._logger = logging.getLogger(__name__)

        # 获取主窗口的插件系统实例
        if parent is not None:
            print("获取主窗口的插件系统实例")
            self.plugin_system = parent.plugin_system
        
        # 打开文件按钮
        self.open_xlsx_action = QAction(QIcon("resources/icons/open.png"), "打开", self)
        self.open_xlsx_action.triggered.connect(self.open_file)
        self.addAction(self.open_xlsx_action)

        # 保存按钮
        self.save_action = QAction(QIcon("resources/icons/save.png"), "保存", self)
        self.save_action.triggered.connect(self.save_file)
        self.addAction(self.save_action)

        # 关闭按钮
        self.close_action = QAction(QIcon("resources/icons/close.png"), "关闭", self)
        self.close_action.triggered.connect(self.close_file)
        self.addAction(self.close_action)

        # 添加插件按钮
        self.plugin_action = QAction(QIcon("resources/icons/+.png"), "插件管理", self)
        self.plugin_action.triggered.connect(self.show_plugin_manager)
        self.addAction(self.plugin_action)
        
        # 插件按钮
        self.update_plugin_buttons()

        self.global_state = GlobalState()
        self.global_state.event_bus.on("plugin.activated", self.on_plugin_activated)
        self.global_state.event_bus.on("plugin.deactivated", self.on_plugin_deactivated)
        self.global_state.event_bus.on("plugin.loaded", self.on_plugin_loaded)
        self.global_state.event_bus.on("plugin.unloaded", self.on_plugin_unloaded)
    
    def show_plugin_manager(self):
        """显示插件管理窗口"""
        plugin_manager = PluginManagerWindow(self.plugin_system, self)
        plugin_manager.exec()

    def update_plugin_buttons(self, data: Dict[str, Any] = None):
        # 清除所有插件按钮，保留初始化按钮
        print("清除所有插件按钮，保留初始化按钮")
        for action in self.actions()[4:]:  # 保留前4个初始化按钮
            self.removeAction(action)

        # 添加插件按钮
        print("激活/停用时更新插件按钮")
        if data is not None:
            plugin_name = data.get('plugin_name')
            plugin_state = self.plugin_system.get_plugin_state(plugin_name)
            print(f"插件{plugin_name}状态：{plugin_state}")
            if plugin_name and plugin_state == 'activated':
                print(f"激活/停用时添加插件按钮：{plugin_name}")
                plugin_action = QAction(QIcon("resources/icons/+.png"), plugin_name, self)
                plugin_action.triggered.connect(lambda checked, name=plugin_name: self.use_plugin(name))
                self.addAction(plugin_action)
                return

        print(f"初始化或加载/卸载时更新插件按钮")
        if len(self.plugin_system.get_all_plugins()) == 0:
            print("无插件")
            return
        for plugin_name, plugin_info in self.plugin_system.get_all_plugins().items():
            if self.plugin_system.get_plugin_state(plugin_name) in ['activated', 'loaded']:
                print(f"初始化或加载/卸载时更新插件按钮：{plugin_name}")
                plugin_action = QAction(QIcon("resources/icons/+.png"), plugin_name, self)
                plugin_action.triggered.connect(lambda checked, name=plugin_name: self.use_plugin(name))
                self.addAction(plugin_action)

    def on_plugin_activated(self, data: Dict[str, Any] = None):
        """处理插件激活事件"""
        print("处理插件激活事件")
        self.update_plugin_buttons(data)
    def on_plugin_deactivated(self, data: Dict[str, Any] = None):
        """处理插件停用事件"""
        print("处理插件停用事件")
        self.update_plugin_buttons(data)
    def on_plugin_loaded(self, data: Dict[str, Any] = None):
        """处理插件加载事件"""
        print("处理插件加载事件")
        self.update_plugin_buttons(None)
    def on_plugin_unloaded(self, data: Dict[str, Any] = None):
        """处理插件卸载事件"""
        print("处理插件卸载事件")
        self.update_plugin_buttons(None)

    def open_file(self):
        try:
            # 如果已有打开的文件，先关闭它
            if self.global_state.workbook.workbook is not None:
                # 检查是否需要保存
                if not self.check_and_save_changes():
                    return  # 用户取消操作
                # 关闭当前文件
                self.close_file()
                # 确保全局状态被清除
                self.global_state.workbook.workbook = None
                self.global_state.workbook.file_path = None
                self.global_state.workbook.activate_sheet = None
                
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "打开Excel文件",
                "",
                "Excel Files (*.xlsx *.xls)"
            )
            
            if file_path:
                # 显示加载进度
                progress = QProgressDialog("正在打开文件...", None, 0, 100, self)
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.setMinimumDuration(0)
                progress.setValue(0)
                
                try:
                    # 使用 read_only=True 和 data_only=True 提高加载速度
                    workbook = openpyxl.load_workbook(
                        file_path,
                        read_only=True,
                        data_only=True
                    )
                    progress.setValue(50)
                    
                    # 获取主窗口的工作簿组件
                    workbook_widget = self.parent().workbook_widget
                    
                    # 加载工作簿到界面
                    workbook_widget.load_workbook(workbook, file_path)
                    workbook_widget.tab_widget.setCurrentIndex(0)
                    workbook_widget.on_tab_changed(0)
                    progress.setValue(100)
                    
                finally:
                    progress.close()
                
        except Exception as e:
            ErrorHandler.handle_error(e, self, "打开文件时发生错误")

    def check_and_save_changes(self) -> bool | None:
        """检查是否有未保存的更改并询问用户是否保存
        
        Returns:
            bool: True 表示可以继续，False 表示用户取消操作
        """
        try:
            workbook_widget = self.parent().workbook_widget
            has_changes = False
            
            # 检查所有标签页是否有更改
            for i in range(workbook_widget.tab_widget.count()):
                tab = workbook_widget.tab_widget.widget(i)
                if isinstance(tab, QTableView):
                    model = tab.model()
                    if model and hasattr(model, 'has_changes') and model.has_changes():
                        has_changes = True
                        break
            
            if has_changes:
                reply = QMessageBox.question(
                    self,
                    "保存更改",
                    "是否保存更改？",
                    QMessageBox.StandardButton.Save | 
                    QMessageBox.StandardButton.Discard | 
                    QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Save
                )
                
                if reply == QMessageBox.StandardButton.Save:
                    return self.save_file()
                elif reply == QMessageBox.StandardButton.Cancel:
                    return False
                    
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "检查文件更改时发生错误")
            return False

    def save_file(self):
        try:
            # 获取主窗口的工作簿组件
            workbook_widget = self.parent().workbook_widget
            
            # 保存工作簿
            if workbook_widget.save_workbook():
                ErrorHandler.handle_info("文件保存成功", self)
            else:
                ErrorHandler.handle_warning("没有可保存的文件", self)
                
        except Exception as e:
            ErrorHandler.handle_error(e, self, "保存文件时发生错误")

    def close_file(self):
        try:
            # 检查是否有未保存的更改
            if not self.check_and_save_changes():
                return  # 用户取消关闭操作
            
            # 获取主窗口的工作簿组件
            workbook_widget = self.parent().workbook_widget
            
            # 清除所有标签页
            workbook_widget.clear_tabs()
            
            # 更新全局状态
            state = GlobalState()
            state.workbook.workbook = None
            state.workbook.file_path = None
            state.workbook.activate_sheet = None
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "关闭文件时发生错误")

    def use_plugin(self, plugin_name: str):
        """使用指定的插件"""
        try:
            # 获取插件实例
            plugin = self.plugin_system.get_plugin(plugin_name)
            if not plugin:
                QMessageBox.warning(self, "警告", f"找不到插件 {plugin_name}")
                return

            # 获取当前活动的表格视图
            current_table_view = GlobalState().get_current_table_view()
            if not current_table_view:
                QMessageBox.warning(self, "警告", "无法获取当前表格视图")
                return

            # 获取插件所需的参数配置
            required_parameters = getattr(plugin, 'get_required_parameters', lambda: {})()
            print(required_parameters)
            
            # 收集用户输入的参数
            parameters = {}
            for param_name, param_config in required_parameters.items():
                if param_name == "table_view":  # 跳过表格视图参数
                    continue
                    
                # 将默认值转换为字符串
                default_value = str(param_config.get("default", ""))

                param_value, ok = QInputDialog.getText(
                    self,
                    f"输入参数 {param_name}",
                    f"请输入 {param_name}:",
                    text=default_value
                )

                if not ok:
                    return  # 用户取消输入

                # 根据参数类型进行转换
                if param_config.get("type") == "int":
                    try:
                        parameters[param_name] = int(param_value)
                    except ValueError:
                        QMessageBox.warning(self, "警告", f"{param_name} 必须是整数")
                        return
                else:
                    parameters[param_name] = param_value

            # 验证参数
            error = plugin.validate_parameters(parameters)
            if error:
                QMessageBox.warning(self, "警告", f"无效的参数: {error}")
                return

            try:
                # 使用插件处理数据，自动传入当前表格视图
                result = plugin.process_data(current_table_view, **parameters)
                
                if result is not None:
                    # QMessageBox.information(self, "成功", f"插件 {plugin_name} 处理完成")
                    self._logger.info(f"插件 {plugin_name} 处理开始")
                
            except Exception as e:
                ErrorHandler.handle_error(e, self, f"插件 {plugin_name} 处理失败")
            
        except Exception as e:
            ErrorHandler.handle_error(e, self, "使用插件时发生错误")
