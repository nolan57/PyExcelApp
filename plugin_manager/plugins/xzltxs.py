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
from ..core.plugin_base import PluginBase
from ..features.plugin_permissions import PluginPermission
from ..features.plugin_lifecycle import PluginState
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
        
        # 添加配置模式定义
        self.config_schema = {
            'part_code_column': {
                'type': int,
                'required': True,
                'default': 2,
                'description': '零件编码列'
            },
            'part_name_column': {
                'type': int,
                'required': True,
                'default': 3,
                'description': '零件名称列'
            },
            'xs_column': {
                'type': int,
                'required': True,
                'default': 19,
                'description': '系数起始列'
            },
            'price_column': {
                'type': int,
                'required': True,
                'default': 4,
                'description': '价格列'
            },
            'start_row': {
                'type': int,
                'required': True,
                'default': 2,
                'description': '起始行'
            }
        }

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
                try:
                    # 先断开所有信号连接
                    try:
                        self.data_processor.finished.disconnect()
                        self.data_processor.error.disconnect()
                        self.data_processor.progress.disconnect()
                        self.data_processor.stopped.disconnect()
                    except:
                        pass
                    
                    # 然后停止处理器
                    self.data_processor.stop()
                    self.data_processor.wait(1000)
                    self.data_processor.deleteLater()
                except:
                    pass
                finally:
                    delattr(self, 'data_processor')
            
            # 关闭进度条
            if hasattr(self, 'progress'):
                try:
                    if not self.progress.isHidden():
                        try:
                            self.progress.canceled.disconnect()
                        except:
                            pass
                        self.progress.close()
                except:
                    pass
                finally:
                    delattr(self, 'progress')
            
            # 调用基类清理方法
            super().cleanup()
            
        except Exception as e:
            self._logger.error(f"清理资源时发生错误: {str(e)}")
        
    def get_name(self) -> str:
        """获取插件名称"""
        return "xzltxs"
        
    def get_version(self) -> str:
        """获取插件版本"""
        return "1.0.0"
        
    def get_description(self) -> str:
        """获取插件描述"""
        return "修正单台成本中的轮胎系数"
        
    def get_dependencies(self) -> List[str]:
        """获取插件依赖"""
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
        """验证参数有效性"""
        if not all(key in parameters for key in ['part_column', 'price_column', 'start_row']):
            return "缺少必需的参数"
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

    def process_column(self, current_col, cached_data):
        """处理单列数据"""
        self._logger.info(f"处理列: {current_col}")
        results = []
        
        # 将缓存数据转换为原来的格式: (row, current_value, part_code, part_name, price)
        rows_data = []
        for row_data in cached_data:
            current_value = row_data['values'].get(current_col)
            if not current_value:  # 如果为空，跳过
                continue
            try:
                if float(str(current_value)) == 0:  # 如果等于0，跳过
                    continue
            except (ValueError, TypeError):
                continue  # 如果无法转换为数值，跳过
            
            rows_data.append((
                row_data['row'],
                current_value,
                row_data['part_code'],
                row_data['part_name'],
                row_data['price']
            ))
        
        # 为每种零件类型创建目标单元格列表
        part_targets = {i: [] for i in range(len(self.parts_config))}
        
        # 处理当前批次的数据
        for row, current_value, part_code, part_name, price in rows_data:
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
                    self.table_view.model(),  # 从 table_view 获取 model
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
            # 批量更新以提高性能
            with self._model_lock:
                # 预先准备所有更新数据
                updates = []
                for target in results:
                    updates.append({
                        'row': target.row,
                        'value': target.value,
                        'color': target.color
                    })
                
                # 批量应用更新
                if isinstance(model, TableModel):
                    # 如果是自定义的 TableModel，使用批量更新方法
                    model.batch_update_cells(current_col, updates)
                else:
                    # 对于标准模型，使用常规方式更新
                    for update in updates:
                        # 设置单元格值
                        model.setData(
                            model.index(update['row'], current_col),
                            update['value'],
                            Qt.ItemDataRole.EditRole
                        )
                        # 设置单元格颜色
                        model.setData(
                            model.index(update['row'], current_col),
                            update['color'],
                            Qt.ItemDataRole.BackgroundRole
                        )
                    
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
        task_completed = Signal(int)

        class ColumnTask(QRunnable):
            def __init__(self, col, cached_data, plugin, callback):
                super().__init__()
                self.col = col
                self.cached_data = cached_data
                self.plugin = plugin
                self.callback = callback
                self._logger = None

            def run(self):
                try:
                    self._logger = logging.getLogger(__name__)
                    self._logger.info(f"开始处理列 {self.col}")
                    
                    # 使用缓存的数据调用 process_column
                    results = self.plugin.process_column(self.col, self.cached_data)
                    if results:
                        # 将结果应用到模型
                        self.plugin.apply_results(results, self.col, self.plugin.table_view.model())
                    
                    self.callback()
                    self._logger.info(f"列 {self.col} 处理完成")
                except Exception as e:
                    self._logger.error(f"处理列 {self.col} 时发生错误: {str(e)}")
                    QMetaObject.invokeMethod(
                        self.plugin.data_processor,
                        "error",
                        Qt.ConnectionType.QueuedConnection,
                        Q_ARG(str, str(e)))

        def __init__(self, plugin):
            super().__init__()
            self.plugin = plugin
            self._stop_requested = False
            self._is_stopping = False
            self._completed_tasks = 0
            self._total_tasks = 0
            self._lock = threading.Lock()
            self._logger = logging.getLogger(__name__)
            
            # 创建线程池并设置父对象
            self.thread_pool = QThreadPool()
            self.thread_pool.setParent(self)  # 确保线程池随线程一起销毁

        def _on_task_completed(self, col):
            """处理单个任务完成的槽函数"""
            with self._lock:
                self._completed_tasks += 1
                self.progress.emit(self._completed_tasks)
                self._logger.debug(f"任务完成进度: {self._completed_tasks}/{self._total_tasks}")

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
                
                # 在主循环前连接信号
                self.task_completed.connect(self._on_task_completed, Qt.ConnectionType.QueuedConnection)
                
                # 预处理：缓存有效数据
                self._logger.info("开始缓存有效数据")
                cached_data = self._cache_valid_data(model)
                self._logger.info(f"缓存完成，有效数据行数: {len(cached_data)}")
                
                # 创建所有任务
                tasks = []
                for col in range(self.plugin.xs_column, max_col):
                    if self._stop_requested:
                        break
                        
                    self._logger.info(f"创建列 {col} 的处理任务")
                    task = self.ColumnTask(
                        col=col,
                        cached_data=cached_data,  # 传入缓存的数据
                        plugin=self.plugin,
                        callback=lambda c=col: self.task_completed.emit(c)
                    )
                    tasks.append(task)
                    
                # 批量提交任务
                for task in tasks:
                    if self._stop_requested:
                        break
                    self.thread_pool.start(task)
                    
                self._logger.info(f"已提交 {self._total_tasks} 个任务到线程池")
                
                # 等待所有任务完成或被终止
                while not self._stop_requested and self._completed_tasks < self._total_tasks:
                    if self.thread_pool.waitForDone(100):  # 如果所有任务完成，跳出循环
                        break
                    QThread.msleep(10)  # 短暂休眠避免CPU过载
                    
                # 确保所有任务都完成或被清理
                self.thread_pool.waitForDone()
                
                # 断开信号连接
                try:
                    self.task_completed.disconnect(self._on_task_completed)
                except:
                    pass
                    
                if self._stop_requested:
                    self._logger.info("数据处理被用户终止")
                    self.stopped.emit()
                else:
                    self._logger.info("数据处理完成")
                    self.finished.emit()
                    
            except Exception as e:
                self._logger.error(f"处理数据时发生错误: {str(e)}")
                self.error.emit(str(e))

        def stop(self):
            """停止处理"""
            try:
                if self._is_stopping:  # 防止重复停止
                    return
                
                self._is_stopping = True
                self._logger.info("强制终止数据处理")
                self._stop_requested = True
                
                # 清空线程池中的所有任务
                self.thread_pool.clear()
                
                # 等待线程池清空
                self.thread_pool.waitForDone(100)
                
                # 发出停止信号
                self.stopped.emit()
                
                # 退出当前线程
                self.quit()
                self.wait(1000)  # 等待最多1秒
                
            except Exception as e:
                self._logger.error(f"停止处理时发生错误: {str(e)}")
                ErrorHandler.handle_error(e,self,f"停止处理时发生错误: {str(e)}")
            finally:
                self._is_stopping = False

        def _cache_valid_data(self, model):
            """缓存有效数据"""
            valid_data = []
            start_row = self.plugin.start_row
            max_row = model.rowCount()
            max_col = model.columnCount()
            
            # 创建parts_config的查找集合，提高查找效率
            valid_parts = {
                (str(config.get('code', '')), config.get('name', ''))
                for config in self.plugin.parts_config
            }
            
            # 批量获取数据
            for row in range(start_row, max_row):
                part_code = str(model.data(model.index(row, self.plugin.part_code_column)) or '')
                part_name = str(model.data(model.index(row, self.plugin.part_name_column)) or '')
                
                # 检查是否是有效数据
                if (part_code, part_name) in valid_parts:
                    # 缓存这一行的所有必要数据
                    row_data = {
                        'row': row,
                        'part_code': part_code,
                        'part_name': part_name,
                        'price': safe_float_convert(model.data(model.index(row, self.plugin.price_column))),
                        'values': {}  # 存储从xs_column开始到最后一列的所有数据
                    }
                    
                    # 缓存从xs_column开始到最后一列的所有数据
                    for col in range(self.plugin.xs_column, max_col):
                        cell_value = model.data(model.index(row, col))
                        # 转换为浮点数，如果转换失败则保留原值
                        if isinstance(cell_value, (int, float)):
                            cell_value = float(cell_value)
                        elif isinstance(cell_value, str):
                            try:
                                cell_value = float(cell_value)
                            except (ValueError, TypeError):
                                pass
                        row_data['values'][col] = cell_value
                        
                    valid_data.append(row_data)
            
            return valid_data

    def process_data(self, table_view: Optional[QTableView] = None, **parameters) -> Any:  # type: ignore[override]  # QTableView, **parameters) -> Any:
        """处理数据"""
        # 从 parameters 中获取配置值
        part_code_column = parameters.get('part_code_column', 2)  # 使用默认值
        part_name_column = parameters.get('part_name_column', 3)
        xs_column = parameters.get('xs_column', 19)
        price_column = parameters.get('price_column', 4)
        start_row = parameters.get('start_row', 2)

        try:
            # 启动插件处理
            self.start()  # 调用基类的 start 方法，触发 plugin.started 事件
            
            # 等待数据处理完成
            result = self._process_data(table_view, **parameters)
            
            # 创建事件循环等待处理完成
            loop = QEventLoop()
            if hasattr(self, 'data_processor'):
                self.data_processor.finished.connect(loop.quit)
                self.data_processor.stopped.connect(loop.quit)
                self.data_processor.error.connect(loop.quit)
                loop.exec()  # 等待直到处理完成
            
            return result
        except Exception as e:
            self._logger.error(f"处理数据时发生错误: {str(e)}")
            raise e
        finally:
            # 确保处理完成后停止插件
            self.stop()  # 调用基类的 stop 方法，触发 plugin.stopped 事件

    def _process_data(self, table_view: QTableView, **parameters) -> Any:
        """处理数据的具体实现"""
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
            
            # 创建数据处理器
            self._logger.info("创建数据处理器")
            self.data_processor = self.DataProcessor(self)
            
            # 先连接取消按钮
            self.progress.canceled.connect(self._cancel_processing)
            
            # 然后连接数据处理器的信号
            self.data_processor.finished.connect(self._on_processing_finished)
            self.data_processor.error.connect(self._on_processing_error)
            self.data_processor.progress.connect(self.progress.setValue)
            self.data_processor.stopped.connect(self._on_processing_stopped)
            
            # 显示进度条
            self.progress.show()
            QApplication.processEvents()  # 确保UI更新
            
            # 启动处理器
            self._logger.info("启动数据处理器")
            self.data_processor.start()
            
            return True  # 返回 True 表示处理已经开始
            
        except Exception as e:
            ErrorHandler.handle_error(e, self.table_view, "处理数据时发生错误")
            self._logger.error(f"处理数据时发生错误: {str(e)}")
            return False
        
    def _on_processing_finished(self):
        """处理完成时的回调"""
        self._logger.info("数据处理完成")
        if isinstance(self.table_view.model(), TableModel):
            self.table_view.model().save_changes()
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
        try:
            self._logger.warning("用户取消数据处理")
            if hasattr(self, 'data_processor') and self.data_processor:
                # 先停止处理器
                self.data_processor.stop()
                
                # 等待一小段时间确保停止信号被处理
                QThread.msleep(100)
                
                # 然后断开信号连接
                try:
                    self.data_processor.finished.disconnect()
                    self.data_processor.error.disconnect()
                    self.data_processor.progress.disconnect()
                    self.data_processor.stopped.disconnect()
                    self.progress.canceled.disconnect()
                except:
                    pass  # 忽略断开连接时的错误
                
        except Exception as e:
            self._logger.error(f"取消处理时发生错误: {str(e)}")

    def _on_processing_stopped(self):
        """处理停止时的回调"""
        try:
            self._logger.info("数据处理已停止")
            
            # 关闭进度条
            if hasattr(self, 'progress'):
                if not self.progress.isHidden():
                    self.progress.close()
                delattr(self, 'progress')
            
            # 清理数据处理器
            if hasattr(self, 'data_processor'):
                try:
                    self.data_processor.wait(1000)  # 等待线程结束
                    self.data_processor.deleteLater()
                except:
                    pass
                finally:
                    delattr(self, 'data_processor')
            
            # 重置错误状态
            self._error_occurred = False
            
            # 通知用户处理已停止
            ErrorHandler.handle_info("数据处理已停止", self.table_view)
            
            # 确保插件状态更新
            self.stop()  # 调用基类的 stop 方法，触发 plugin.stopped 事件
            
        except Exception as e:
            self._logger.error(f"处理停止回调时发生错误: {str(e)}")

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

    def get_config_schema(self) -> Dict[str, Dict[str, Any]]:
        """获取配置模式"""
        return {
            'part_code_column': {
                'type': int,
                'required': True,
                'default': 2,
                'description': '零件编码列'
            },
            'part_name_column': {
                'type': int,
                'required': True,
                'default': 3,
                'description': '零件名称列'
            },
            'xs_column': {
                'type': int,
                'required': True,
                'default': 19,
                'description': '系数起始列'
            },
            'price_column': {
                'type': int,
                'required': True,
                'default': 4,
                'description': '价格列'
            },
            'start_row': {
                'type': int,
                'required': True,
                'default': 2,
                'description': '起始行'
            }
        }

    def verify_dependency_signature(self, dependency_name: str, signature: str) -> bool:
        """验证依赖包签名"""
        # 暂不实现签名验证
        return True
        
    def get_trusted_sources(self) -> List[str]:
        """获取可信源列表"""
        return ["https://pypi.org/simple"]
