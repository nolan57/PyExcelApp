from typing import Any, Dict, List, Optional, Set
from PyQt6.QtWidgets import QTableView, QApplication, QMessageBox, QDialog, QProgressDialog
from PyQt6.QtCore import QModelIndex, Qt, QThreadPool, QRunnable, QObject, pyqtSignal as Signal, QAbstractTableModel, \
    QMetaObject, QThread, QEventLoop, Q_ARG
from PyQt6.QtGui import QColor
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import threading

from utils.mouse_operations import MouseOperations
from ui.column_settings_dialog import ColumnSettingsDialog
from utils.common import safe_float_convert
from utils.error_handler import ErrorHandler
from plugin_manager.plugin_interface import PluginInterface, PluginState
from plugin_manager.plugin_permissions import PluginPermission
from plugin_manager.plugin_base import PluginBase
from models.table_model import TableModel
import logging

@dataclass
class PartTarget:
    row: int
    value: float
    color: QColor

class XzltxsPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler('plugin.log')
        fh.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self._logger.addHandler(fh)
        self.table_view = None  # 使用基类的表格视图管理
        self.sp_disk_price = 150
        self._config = {
            'part_code_column': 2,
            'part_name_column': 3,
            'xs_column': 19,
            'price_column': 4,
            'start_row': 2
        }
        self._active = False
        # 零件配置
        self.parts_config = [
            {
                'name': 'TIRE',  # 普通轮胎
                'code': '42751',
                'is_special': False,
                'has_price': False,
                'rules': {
                    1: {'value': 4.0},
                    2: {'value': 2.0, 'apply_to_all': True},
                    3: {'values': [1.0, 1.0, 2.0]},
                    4: {'value': 1.0, 'apply_to_all': True},
                    'default': {
                        'total': 4.0,
                        'distribute': 'average_with_remainder'
                    }
                },
                'rules2': {
                    'total': 4.0,
                    'prefer_integer': True,  # 优先使用整数
                    'method': 'proportional'  # 按比例分配
                }
            },
            {
                'name': 'TIRE',  # SP轮胎
                'code': '42751',
                'is_special': True,
                'special_key': 'D',
                'has_price': False,
                'rules': {
                    1: {'value': 1.0, 'integer': True},
                    'default': {
                        'total': 1.0,
                        'distribute': 'equal',
                        'integer': True,
                        'show_decimal': True  # 当不能整除时显示小数
                    }
                },
                'rules2': {
                    'total': 1.0,
                    'prefer_integer': False,  # SP类型不强制使用整数
                    'method': 'proportional'
                }
            },
            {
                'name': 'DISK',  # 普通DISK
                'code': '42700',
                'is_special': False,
                'has_price': False,
                'rules': {
                    1: {'value': 4.0},
                    2: {'value': 2.0, 'apply_to_all': True},
                    3: {'values': [1.0, 1.0, 2.0]},
                    4: {'value': 1.0, 'apply_to_all': True},
                    'default': {
                        'total': 4.0,
                        'distribute': 'average_with_remainder'
                    }
                },
                'rules2': {
                    'total': 4.0,
                    'prefer_integer': True,  # 优先使用整数
                    'method': 'proportional'  # 按比例分配
                }
            },
            {
                'name': 'DISK',  # SP DISK
                'code': '42700',
                'is_special': True,
                'has_price': True,
                'max_price': 150,
                'rules': {
                    1: {'value': 1.0, 'integer': True},
                    'default': {
                        'total': 1.0,
                        'distribute': 'equal',
                        'integer': True,
                        'show_decimal': True  # 当不能整除时显示小数
                    }
                },
                'rules2': {
                    'total': 1.0,
                    'prefer_integer': False,  # SP类型不强制使用整数
                    'method': 'proportional'
                }
            },
            {
                'name': 'CAP',   # CAP
                'code': '44732',
                'is_special': False,
                'has_price': False,
                'rules': {
                    1: {'value': 4.0},
                    2: {'value': 2.0, 'apply_to_all': True},
                    3: {'values': [1.0, 1.0, 2.0]},
                    4: {'value': 1.0, 'apply_to_all': True},
                    'default': {
                        'total': 4.0,
                        'distribute': 'average_with_remainder'
                    }
                },
                'rules2': {
                    'total': 4.0,
                    'prefer_integer': True,  # 优先使用整数
                    'method': 'proportional'  # 按比例分配
                }
            }
        ]
        
        self.part_code = None
        self.part_name = None
        
        self.part_code_column = 2
        self.part_name_column = 3
        self.xs_column = 19
        self.price_column = 4
        self.start_row = 2
        
        # 线程安全的锁
        self._model_lock = threading.Lock()
        
        # 初始化 MouseOperations 实例
        self.mouse_ops = None
        if self.table_view:
            self.mouse_ops = MouseOperations(self.table_view)
        
        # 如果当前有活动的table_view，禁用右键菜单
        if self.table_view:
            self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
            self.settings_dialog = ColumnSettingsDialog(self.table_view)
        
        # 添加新的状态管理
        self._state = PluginState.UNLOADED
        
        # 添加权限相关的属性
        self._required_permissions = {
            PluginPermission.FILE_READ,    # 需要读取表格数据
            PluginPermission.FILE_WRITE,   # 需要修改表格数据
            PluginPermission.UI_MODIFY     # 需要修改界面
        }
        
        self._optional_permissions = {
            PluginPermission.DATA_READ,    # 可选的文件读取权限
            PluginPermission.DATA_WRITE    # 可选的文件写入权限
        }
        
        # 当前已获得的权限
        self._granted_permissions = set()
        
    def initialize(self) -> None:
        """初始化插件"""
        self._logger.info("xzltxs插件初始化")
        self._logger.info(f"插件配置: {self._config}")
        self._logger.info(f"零件配置数量: {len(self.parts_config)}")
        self._logger.info(f"table_view 状态: {self.table_view is not None}")
        
    def activate(self, granted_permissions: Set[PluginPermission]) -> None:
        """激活插件"""
        try:
            self._logger.info("开始激活插件")
            # 更新已授权权限
            self._granted_permissions = granted_permissions
            
            # 检查是否有所有必要权限
            missing_permissions = self._required_permissions - self._granted_permissions
            if missing_permissions and len(missing_permissions) > 0:
                self._logger.info(f"缺失权限: {missing_permissions}")
            
            if missing_permissions:
                # 只请求未授权的必要权限
                for permission in missing_permissions:
                    if not self.check_permission(permission):
                        self._logger.info(f"请求权限: {permission}")
                        if not self.request_permission(permission):
                            raise PermissionError(
                                f"无法激活插件：缺少必要权限 {PluginPermission.get_permission_description(permission)}"
                            )
                        # 如果请求成功，添加到已授权权限集合
                        self._granted_permissions.add(permission)
            
            self._active = True  # 设置激活状态
            self._state = PluginState.ACTIVE
            self._logger.info("插件激活成功")
            
        except Exception as e:
            self._state = PluginState.ERROR
            ErrorHandler.handle_error(e, None, "激活插件失败")
            self._logger.error(f"插件激活失败: {e}")
        
    def deactivate(self) -> None:
        """停用插件"""
        self._active = False
        self._state = PluginState.LOADED
        # 清除已授予的权限
        self._granted_permissions.clear()
        
    def cleanup(self) -> None:
        """清理插件资源"""
        try:
            # 停止数据处理
            if hasattr(self, 'data_processor'):
                self.data_processor.stop()
                self.data_processor.wait()  # 等待线程结束
                self.data_processor.deleteLater()
                delattr(self, 'data_processor')
            
            # 关闭进度条
            if hasattr(self, 'progress'):
                self.progress.close()
                delattr(self, 'progress')
            
            # 关闭设置对话框
            if hasattr(self, 'settings_dialog'):
                self.settings_dialog.close()
                delattr(self, 'settings_dialog')
            
            # 清理其他资源
            if hasattr(self, 'mouse_ops'):
                delattr(self, 'mouse_ops')
            
            # 调用基类清理方法
            super().cleanup()
            
        except Exception as e:
            self._logger.error(f"清理资源时发生错误: {e}")
        
    def get_name(self) -> str:
        return "xzltxs"
        
    def get_version(self) -> str:
        return "1.0.0"
        
    def get_description(self) -> str:
        return "修正单台成本中的轮胎系数"
        
    def get_dependencies(self) -> List[str]:
        return []
        
    def get_required_parameters(self) -> Dict[str, Dict[str, Any]]:
        return {
            "table_view": {
                "type": "QTableView",
                "required": True,
                "description": "要处理的表格视图"
            }
        }
        
    def validate_parameters(self, parameters: Dict[str, Any]) -> Optional[str]:
        required_params = self.get_required_parameters()
        for param_name, param_info in required_params.items():
            if param_name == "table_view":
                continue  # 跳过 table_view 参数，因为它是通过插件管理器注入的
            if param_name not in parameters:
                return f"缺少必需的参数：{param_name}"
            param_value = parameters[param_name]
            if param_info["type"] != type(param_value).__name__:
                return f"参数 {param_name} 的类型不正确，应为 {param_info['type']}"
            if param_info["required"] and param_value is None:
                return f"参数 {param_name} 是必需的"
        return None
        
    def get_configuration(self) -> Dict[str, Any]:
        """获取插件配置"""
        return self._config.copy()  # 返回配置的副本以防止直接修改
        
    def set_configuration(self, config: Dict[str, Any]) -> None:
        self._config.update(config)
        
    def on_event(self, event: str, data: Dict[str, Any] = None) -> None:
        """处理系统事件"""
        pass

    def calculate_proportional_distribution(self, targets: List[int], current_col: int, model, rules2: Dict[str, Any]) -> List[PartTarget]:
        """按比例计算分配值"""
        results = []
        source_color = QColor(255, 255, 0)  # 黄色
        
        # 收集原始值并计算总和
        original_values = []
        total_original = 0.0
        
        with self._model_lock:
            for row in targets:
                value = safe_float_convert(model.data(model.index(row, current_col)))
                original_values.append(value)
                total_original += value
        
        if total_original == 0:
            # 如果原始总和为0，则平均分配
            value_per_target = rules2['total'] / len(targets)
            for row in targets:
                results.append(PartTarget(row=row, value=value_per_target, color=source_color))
            return results
        
        # 计算新值
        target_total = rules2['total']
        prefer_integer = rules2['prefer_integer']
        
        if prefer_integer and len(targets) > 1:
            # 如果需要整数值，使用特殊处理
            new_values = []
            remaining = target_total
            
            # 首先按比例计算浮点数值
            for original in original_values:
                proportion = original / total_original
                new_value = target_total * proportion
                new_values.append(new_value)
            
            # 对于需要整数的情况，先向下取整
            integer_values = [int(v) for v in new_values]
            remaining = target_total - sum(integer_values)
            
            # 计算小数部分，并按大小排序决定哪些值需要加1
            decimal_parts = [(i, v - int(v)) for i, v in enumerate(new_values)]
            decimal_parts.sort(key=lambda x: x[1], reverse=True)
            
            # 分配剩余值
            remaining = int(round(remaining))
            for i in range(remaining):
                if i < len(decimal_parts):
                    idx = decimal_parts[i][0]
                    integer_values[idx] += 1
            
            # 创建结果
            for row, value in zip(targets, integer_values):
                results.append(PartTarget(row=row, value=value, color=source_color))
        else:
            # 如果不要整数值，直接按比例计算
            for row, original in zip(targets, original_values):
                proportion = original / total_original
                new_value = target_total * proportion
                if prefer_integer:
                    new_value = round(new_value)
                else:
                    new_value = round(new_value, 3)  # 保留3位小数
                results.append(PartTarget(row=row, value=new_value, color=source_color))
        
        return results

    def calculate_value_rule(self, targets: List[int], rule: Dict[str, Any]) -> List[PartTarget]:
        """计算数值规则，返回目标列表"""
        results = []
        source_color = QColor(255, 255, 0)  # 黄色
        
        # 检查是否需要整数值
        integer = rule.get('integer', False)
        value = rule.get('value', 0)
        if integer:
            value = int(value)
        
        if 'value' in rule and rule.get('apply_to_all', False):
            # 对所有目标应用相同的值
            for row in targets:
                results.append(PartTarget(row=row, value=value, color=source_color))
        elif 'values' in rule:
            # 应用指定的值列表
            values = rule['values']
            if integer:
                values = [int(v) for v in values]
            for i, row in enumerate(targets):
                if i < len(values):
                    results.append(PartTarget(row=row, value=values[i], color=source_color))
        elif 'value' in rule:
            # 应用单个值到第一个目标
            results.append(PartTarget(row=targets[0], value=value, color=source_color))
            
        return results

    def calculate_distribution(self, targets: List[int], total: float, method: str = 'equal', integer: bool = False, show_decimal: bool = False) -> List[PartTarget]:
        """计算分配值，返回目标列表"""
        results = []
        source_color = QColor(255, 255, 0)  # 黄色
        num_targets = len(targets)
        
        if method == 'equal':
            # 平均分配
            value = total / num_targets
            if integer and not show_decimal:
                # 如果要求整数且不显示小数，则向下取整
                value = int(value)
                
            for row in targets:
                results.append(PartTarget(row=row, value=value, color=source_color))
                
        elif method == 'average_with_remainder':
            # 带余数的平均分配
            avg = total / num_targets
            if integer and not show_decimal:
                # 如果要求整数且不显示小数
                f_avg = int(avg)
                remainder = total - f_avg * num_targets
                # 将余数以1为单位分配给前面的目标
                for i, row in enumerate(targets):
                    value = f_avg + (1 if i < remainder else 0)
                    results.append(PartTarget(row=row, value=value, color=source_color))
            else:
                # 允许显示小数或不要求整数
                f_avg = float(int(avg))
                remainder = total - f_avg * num_targets
                decimal_value = remainder / num_targets
                
                for i, row in enumerate(targets):
                    if i < num_targets - 1:
                        value = round(f_avg + decimal_value, 3)
                    else:
                        value = f_avg
                    results.append(PartTarget(row=row, value=value, color=source_color))
                
        return results

    def calculate_rules(self, targets: List[int], rules: Dict[str, Any]) -> List[PartTarget]:
        """计算规则，返回目标列表"""
        num_targets = len(targets)
        
        # 查找匹配的规则
        rule = rules.get(str(num_targets), rules['default'])
        
        if 'total' in rule:
            # 使用分配方法
            return self.calculate_distribution(
                targets, 
                rule['total'], 
                rule.get('distribute', 'equal'),
                rule.get('integer', False),
                rule.get('show_decimal', False)
            )
        else:
            # 使用具体的值规则
            return self.calculate_value_rule(targets, rule)

    def process_column(self, current_col: int, model) -> List[PartTarget]:
        """处理单列数据"""
        self._logger.info(f"处理列: {current_col}")
        results = []
        batch_size = 1000  # 每批处理的行数
        total_rows = model.rowCount() - self.start_row
        processed_rows = 0
        
        # 为每种零件类型创建目标单元格列表
        part_targets = {i: [] for i in range(len(self.parts_config))}
        
        # 分批次处理数据
        while processed_rows < total_rows:
            # 获取当前批次的数据
            self._logger.info(f"处理行: {self.start_row + processed_rows} - {self.start_row + processed_rows + batch_size}")
            with self._model_lock:
                rows_data = []
                end_row = min(self.start_row + processed_rows + batch_size, model.rowCount())
                for row in range(self.start_row + processed_rows, end_row):
                    current_value = model.data(model.index(row, current_col))
                    part_code = str(model.data(model.index(row, self.part_code_column)) or '')
                    part_name = str(model.data(model.index(row, self.part_name_column)) or '')
                    price = safe_float_convert(model.data(model.index(row, self.price_column)))
                    rows_data.append((row, current_value, part_code, part_name, price))
            
            # 处理当前批次的数据
            for row, current_value, part_code, part_name, price in rows_data:
                if not current_value:  # 如果为空，跳过
                    continue
                try:
                    if float(str(current_value)) == 0:  # 如果等于0，跳过
                        continue
                except (ValueError, TypeError):
                    continue  # 如果无法转换为数值，跳过

                if not part_code and not part_name:
                    continue

                # 检查每种零件类型
                for part_idx, part_config in enumerate(self.parts_config):
                    # 检查零件代码条件
                    if part_config['code'] in part_code:
                        # 如果是TIRE的code (42751)
                        if part_config['code'] == self.parts_config[0]['code']:  # TIRE的code
                            # 检查是否是SP TIRE (第二个配置)
                            if 'D' in part_name:
                                # 是SP TIRE，使用第二个配置
                                part_targets[1].append(row)
                            else:
                                # 是普通TIRE，使用第一个配置
                                part_targets[0].append(row)
                            break

                        # 如果是DISK的code (42700)
                        elif part_config['code'] == self.parts_config[2]['code']:  # DISK的code
                            # 检查是否是SP DISK (第四个配置)
                            if price <= self.sp_disk_price:
                                # 是SP DISK，使用第四个配置
                                part_targets[3].append(row)
                            else:
                                # 是普通DISK，使用第三个配置
                                part_targets[2].append(row)
                            break

                        # 如果是CAP (44732)，使用第五个配置
                        elif part_config['code'] == self.parts_config[4]['code']:
                            part_targets[4].append(row)
                            break
            # 更新已处理行数
            self._logger.info(f"处理行: {self.start_row + processed_rows} - {self.start_row + processed_rows + batch_size} 完成")
            processed_rows += batch_size

        # 处理每种类型的目标单元格
        self._logger.info(f"处理当前列{current_col}的目标单元格")
        for part_idx, targets in part_targets.items():
            if not targets:  # 跳过没有目标的类型
                continue

            part_config = self.parts_config[part_idx]
            # 使用 rules2 进行处理
            if 'rules2' in part_config:
                results.extend(self.calculate_proportional_distribution(
                    targets,
                    current_col,
                    model,
                    part_config['rules2']
                ))
            else:
                # 如果没有 rules2，使用原来的规则
                results.extend(self.calculate_rules(targets, part_config['rules']))
        self._logger.info(f"处理当前列{current_col}的目标单元格完成")
        return results

    def apply_results(self, results: List[PartTarget], current_col: int, model):
        """应用处理结果到表格"""
        self._logger.info(f"开始应用处理结果到列: {current_col}, 目标数量: {len(results)}")
        try:
            with self._model_lock:
                for target in results:
                    # 设置单元格值
                    model.setData(model.index(target.row, current_col), 
                                target.value, Qt.ItemDataRole.EditRole)
                    
                    # 设置单元格颜色
                    if isinstance(model, TableModel):
                        model.set_cell_color(target.row, current_col, target.color)
                    else:
                        # 兼容旧的颜色设置方式
                        model.setData(model.index(target.row, current_col),
                                    target.color, Qt.ItemDataRole.BackgroundRole)
                    
        except Exception as e:
            self._logger.error(f"应用结果时发生错误: {str(e)}")
            ErrorHandler.handle_error(e, self.table_view, "应用结果时发生错误")
            
    def _create_progress_dialog(self, total_cols):
        """创建进度条对话框"""
        progress = QProgressDialog("处理数据中...", "取消", 0, total_cols)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        return progress

    class DataProcessor(QThread):
        finished = Signal()
        progress = Signal(int)
        error = Signal(str)
        stopped = Signal()
        
        class ColumnTask(QRunnable):
            def __init__(self, col, model, plugin, callback):
                super().__init__()
                self.col = col
                self.model = model
                self.plugin = plugin
                self.callback = callback
                self._logger = logging.getLogger(__name__)
                
            def run(self):
                try:
                    self._logger.info(f"开始处理列 {self.col}")
                    results = self.plugin.process_column(self.col, self.model)
                    if results:
                        self.plugin.apply_results(results, self.col, self.model)
                    self.callback()
                    self._logger.info(f"列 {self.col} 处理完成")
                except Exception as e:
                    self._logger.error(f"处理列 {self.col} 时发生错误: {str(e)}")
                    QMetaObject.invokeMethod(
                        self.plugin.data_processor,
                        "error",
                        Qt.ConnectionType.QueuedConnection,
                        Q_ARG(str, str(e))
                    )
                    
        def __init__(self, plugin):
            super().__init__()
            self.plugin = plugin
            self._stop_requested = False
            self.thread_pool = QThreadPool.globalInstance()
            self._completed_tasks = 0
            self._total_tasks = 0
            self._lock = threading.Lock()
            self._logger = logging.getLogger(__name__)
            
        def _update_progress(self):
            with self._lock:
                self._completed_tasks += 1
                progress = self._completed_tasks # int((self._completed_tasks / self._total_tasks) * 100)
                self.progress.emit(progress)
                if self._completed_tasks == self._total_tasks:
                    self.finished.emit()
                    
        def run(self):
            try:
                self._logger.info("开始数据处理")
                model = self.plugin.table_view.model()
                if not model:
                    raise ValueError("无表格模型")
                    
                max_col = model.columnCount()
                self._total_tasks = max_col - self.plugin.xs_column
                self._completed_tasks = 0
                self._logger.info(f"总列数: {self._total_tasks}")
                self.thread_pool.setMaxThreadCount(min(self._total_tasks, 8))
                
                for col in range(self.plugin.xs_column, max_col):
                    if self._stop_requested:
                        break
                        
                    self._logger.info(f"创建列 {col} 的处理任务")
                    task = self.ColumnTask(
                        col=col,
                        model=model,
                        plugin=self.plugin,
                        callback=self._update_progress
                    )
                    self.thread_pool.start(task)
                    self._logger.info(f"列 {col} 的任务已提交到线程池")
                    
                self._logger.info(f"已提交 {self._total_tasks} 个任务到线程池")
                self.thread_pool.waitForDone()
                # if isinstance(self.plugin.table_view.model(), TableModel):
                #     self.plugin.table_view.model().save_changes()
                # self.finished.emit()
                # self._logger.info("数据处理完成")
            except Exception as e:
                self._logger.error(f"处理数据时发生错误: {str(e)}")
                self.error.emit(str(e))
                
        def stop(self):
            self._logger.info("强制终止数据处理")
            self._stop_requested = True
            
            # 清空线程池中的所有任务
            self.thread_pool.clear()
            
            # 尝试等待任务完成，最多等待3次
            for i in range(3):
                if self.thread_pool.waitForDone(msecs=500):  # 每次等待500毫秒
                    break
                self._logger.warning(f"等待任务完成超时，尝试次数：{i+1}")
            
            # 如果仍有任务在运行，重置线程池
            if self.thread_pool.activeThreadCount() > 0:
                self._logger.warning("强制重置线程池")
                self.thread_pool = QThreadPool.globalInstance()
                self.thread_pool.setMaxThreadCount(min(self._total_tasks, 8))
            
            # 发出停止信号
            self.stopped.emit()
            
            # 退出当前线程
            self.quit()
            self.wait()  # 等待线程结束

    def _process_data(self, table_view: Optional[QTableView] = None, **parameters) -> Any:
        """处理数据的入口方法"""
        self._logger.info("开始处理数据")
        try:
            self._error_occurred = False
            self.table_view = table_view or self.get_table_view()
            if not self.table_view:
                raise ValueError("无效的表格视图")
                
            # 设置当前表格视图
            self.set_table_view(self.table_view)

            # 获取数据模型
            model = self.table_view.model()
            if not model:
                self._logger.info("无表格模型")
                raise ValueError("无表格模型")
            
            # 检查必要权限
            if not self._active:
                self._logger.info("插件未激活")
                raise RuntimeError("插件未激活")
            
            required_permissions = {
                PluginPermission.FILE_READ,
                PluginPermission.FILE_WRITE,
                PluginPermission.UI_MODIFY,
                PluginPermission.DATA_READ,
                PluginPermission.DATA_WRITE
            }
            
            # 检查是否有所有必要权限
            missing_permissions = required_permissions - self._granted_permissions
            self._logger.info(f"缺失权限: {missing_permissions}")
            
            if missing_permissions:
                # 尝试请求缺失的权限
                for permission in missing_permissions:
                    self._logger.info(f"请求权限: {permission}")
                    if not self.request_permission(permission):
                        self._logger.info(f"缺少必要权限：{PluginPermission.get_permission_description(permission)}")
                        raise PermissionError(
                            f"缺少必要权限: {PluginPermission.get_permission_description(permission)}"
                        )
            self._logger.info("权限检查通过")

            # 处理零件配置（显示配置对话框）
            if not self.process_parts():
                return None  # 用户取消配置
            QApplication.processEvents()

            max_col = self.table_view.model().columnCount()
            total_cols = max_col - self.xs_column
            self._logger.info(f"总列数: {total_cols}")

            # 创建进度条
            self._logger.info("创建进度条")
            self.progress = self._create_progress_dialog(total_cols)
            
            # 创建并启动数据处理器
            self._logger.info("创建数据处理器")
            self.data_processor = self.DataProcessor(self)
            self.data_processor.finished.connect(self._on_processing_finished)
            self.data_processor.error.connect(self._on_processing_error)
            self.data_processor.progress.connect(self.progress.setValue)
            self.data_processor.stopped.connect(self._on_processing_stopped)
            self.progress.canceled.connect(self.data_processor.stop)
            # 启动数据处理器
            self._logger.info("启动数据处理器")
            self.progress.show()
            self.data_processor.start()
            
            return not self._error_occurred
            
        except Exception as e:
            ErrorHandler.handle_error(e, self.table_view, "处理数据时发生错误")
            self._logger.error(f"处理数据时发生错误: {str(e)}")
            return False
        
    def _on_processing_finished(self):
        """处理完成时的回调"""
        self._logger.info("数据处理完成")
        if isinstance(self.plugin.table_view.model(), TableModel):
                    self.plugin.table_view.model().save_changes()
        if hasattr(self, 'progress') and self.progress:
            self.progress.close()
        
    def _on_processing_error(self, error_msg):
        """处理错误时的回调"""
        self._logger.error(f"数据处理发生错误: {error_msg}")
        self._error_occurred = True
        ErrorHandler.handle_error(Exception(error_msg), self.table_view, "处理数据时发生错误")
        self._on_processing_finished()
        
    def _cancel_processing(self):
        """取消处理"""
        self._logger.warning("用户取消数据处理")
        if hasattr(self, 'data_processor') and self.data_processor:
            self.data_processor.stop()
            
    def _on_processing_stopped(self):
        """处理停止时的回调"""
        self._logger.info("数据处理已停止")
        if hasattr(self, 'progress') and self.progress:
            self.progress.close()
        
        # 清理数据处理器
        if hasattr(self, 'data_processor'):
            self.data_processor.deleteLater()
            delattr(self, 'data_processor')
        
        # 重置错误状态
        self._error_occurred = False
        
        # 通知用户处理已停止
        ErrorHandler.handle_info("数据处理已停止", self.table_view)

    def process_parts(self):
        """处理零件数据"""
        self._logger.info("开始处理零件配置")
        
        # 创建并显示设置对话框
        self.settings_dialog = ColumnSettingsDialog(self.table_view)
        self.settings_dialog.request_cell_position.connect(self.on_cell_position_requested)
        
        # 显示对话框并等待用户输入
        result = self.settings_dialog.show()
        # 等待对话框完成
        while self.settings_dialog.isVisible():
            QApplication.processEvents()
        
        if self.settings_dialog.result() == QDialog.DialogCode.Accepted:
            # 获取并验证用户输入
            values = self.settings_dialog.get_values()
            # 更新配置
            self._logger.info("更新配置")
            self.part_code_column = values["part_code_column"]
            self.part_name_column = values["part_name_column"]
            self.price_column = values["price_column"]
            self.xs_column = values["xs_column"]
            self.start_row = values["start_row"]

            self._config.update({
                "part_code_column": values["part_code_column"],
                "part_name_column": values["part_name_column"],
                "price_column": values["price_column"],
                "xs_column": values["xs_column"],
                "start_row": values["start_row"]
            })
            return True
        else:
            # 用户取消且不使用默认值
            self._logger.info("用户取消且不使用默认值")
            return False

    def on_cell_position_requested(self, message):
        """处理单元格点击请求"""
        self._logger.debug(f"收到单元格位置请求: {message}")
        if not self.table_view:
            ErrorHandler.handle_warning("表格未初始化")
            return
            
        # 获取单元格位置
        row, col = self.get_cell_position()
        
        # 确保获取到有效的位置
        if row >= 0 and col >= 0:
            # 更新对话框中的值
            if hasattr(self, 'settings_dialog') and self.settings_dialog.isVisible():
                self.settings_dialog.update_value(row, col)
                
                # 如果使用了自定义模型，可以高亮选中的单元格
                model = self.table_view.model()
                if model and isinstance(model, TableModel):
                    model.set_cell_color(row, col, QColor(255, 255, 0))  # 黄色高亮

    def get_cell_position(self):
        """
        等待用户点击表格单元格并返回其位置
        返回: (row, column) 元组
        """
        # 确保之前的连接已断开
        self.mouse_ops.disconnect_cell_clicked()
        
        # 重置位置
        row = column = -1
        
        def on_cell_clicked(r, c):
            nonlocal row, column
            row, column = r, c
            # 立即断开信号，防止重复触发
            self.mouse_ops.disconnect_cell_clicked()
            QApplication.processEvents()
        
        # 连接单元格点击信号
        self.mouse_ops.cellClicked.connect(on_cell_clicked)
        self.mouse_ops.connect_cell_clicked()
        
        # 等待用户点击
        while row == -1 or column == -1:
            QApplication.processEvents()
            
        return row, column

    def set_table_view(self, table_view: QTableView):
        """设置表格视图"""
        self._logger.info(f"设置表格视图: {table_view}")
        super().set_table_view(table_view)  # 调用基类方法
        
        # 更新鼠标操作
        if table_view:
            self.mouse_ops = MouseOperations(table_view)
            table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
            self.settings_dialog = ColumnSettingsDialog(table_view)

    def on_config_changed(self, key: str, value: Any) -> None:
        """配置变更回调"""
        self._logger.info(f"配置变更: {key} = {value}")
        try:
            self._logger.info(f"配置变更: {key} = {value}")
            if key in self._config:
                # 验证数值类型的配置项
                if key in ['part_code_column', 'part_name_column', 'xs_column', 
                          'price_column', 'start_row']:
                    value = int(value)
                    if value < 0:
                        raise ValueError(f"{key} 不能为负数")
                self._config[key] = value
                self._logger.info(f"配置更新成功: {key} = {value}")
        except ValueError as e:
            self._logger.error(f"配置更新失败: {key} = {value}")
            ErrorHandler.handle_error(e, None, f"配置项 {key} 设置失败")

    def get_required_permissions(self) -> Set[PluginPermission]:
        """获取插件所需的必要权限"""
        return self._required_permissions
        
    def get_optional_permissions(self) -> Set[PluginPermission]:
        """获取插件的可选权限"""
        return self._optional_permissions
        
    def check_permission(self, permission: PluginPermission) -> bool:
        """检查是否拥有某个权限"""
        return permission in self._granted_permissions
        
    def request_permission(self, permission: PluginPermission) -> bool:
        """请求某个权限"""
        try:
            # 检查是否是必需或可选权限
            if permission not in self._required_permissions and permission not in self._optional_permissions:
                return False
                
            # 显示权限请求对话框
            message = (
                f"插件 {self.get_name()} 请求 {PluginPermission.get_permission_description(permission)}\n"
                f"是否授予此权限？"
            )
            reply = QMessageBox.question(
                self.table_view,
                "权限请求",
                message,
                buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                defaultButton=QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self._granted_permissions.add(permission)
                return True
            return False
            
        except Exception as e:
            ErrorHandler.handle_error(e, None, "请求权限时发生错误")
            self._logger.error(f"请求权限时发生错误: {e.with_traceback(None)}")
            return False
            
    def get_state(self) -> PluginState:
        """获取插件状态"""
        return self._state
