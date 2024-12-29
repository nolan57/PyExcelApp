import pandas as pd
from PyQt6.QtCore import QAbstractTableModel, Qt, QSortFilterProxyModel, QPoint
from PyQt6.QtWidgets import (QTableView, QHeaderView, QMenu, QLineEdit, QWidget, 
                          QVBoxLayout, QWidgetAction, QPushButton, QHBoxLayout)
from PyQt6.QtGui import QColor
from globals import GlobalState
from utils.error_handler import ErrorHandler

class ColumnFilterWidget(QWidget):
    def __init__(self, proxy_model, column, parent=None):
        super().__init__(parent)
        self.proxy_model = proxy_model
        self.column = column
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(2)
        
        # 添加筛选输入框
        self.filter_edit = QLineEdit(self)
        self.filter_edit.setPlaceholderText("输入筛选条件...")
        self.filter_edit.textChanged.connect(self.update_filter)
        main_layout.addWidget(self.filter_edit)
        
        # 添加按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(4)
        
        # 添加清除筛选按钮
        clear_button = QPushButton("清除筛选", self)
        clear_button.clicked.connect(self.clear_filter)
        button_layout.addWidget(clear_button)
        
        main_layout.addLayout(button_layout)
        
    def update_filter(self, text):
        if isinstance(self.proxy_model, FilterProxyModel):
            self.proxy_model.setFilterByColumn(self.column, text.lower())
            
    def clear_filter(self):
        self.filter_edit.clear()
        if isinstance(self.proxy_model, FilterProxyModel):
            self.proxy_model.setFilterByColumn(self.column, "")

class FilterProxyModel(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.filters = {}  # 存储每列的筛选条件
        
    def setFilterByColumn(self, column, text):
        if text:
            self.filters[column] = text
        elif column in self.filters:
            del self.filters[column]
        self.invalidateFilter()
        
    def filterAcceptsRow(self, source_row, source_parent):
        for column, text in self.filters.items():
            item = self.sourceModel().index(source_row, column, source_parent)
            if text not in str(self.sourceModel().data(item, Qt.ItemDataRole.DisplayRole)).lower():
                return False
        return True
        
    def has_changes(self) -> bool:
        """检查源模型是否有未保存的更改"""
        source_model = self.sourceModel()
        if hasattr(source_model, 'has_changes'):
            return source_model.has_changes()
        return False

class ExcelOperations:
    def __init__(self, tab_widget):
        self.data = None
        self.tab_widget = tab_widget
        self.proxy_models = {}  # 存储每个表格的代理模型
        self.filter_widgets = {}  # 存储每个列的筛选控件

    def load_excel(self, file_path):
        try:
            # Load Excel file
            self.data = pd.read_excel(file_path, sheet_name=None)
            
            # Update global state
            state = GlobalState()
            state.workbook.file_path = file_path
            state.workbook.workbook = self.data
            state.workbook.sheet_names = list(self.data.keys())
            state.workbook.activate_sheet = state.workbook.workbook[state.workbook.sheet_names[0]]

            state = GlobalState()
            for sheet_name in state.workbook.sheet_names:
                table_view = QTableView()
                model = PandasModel(state.workbook.workbook[sheet_name])
                
                # 创建代理模型
                proxy_model = FilterProxyModel()
                proxy_model.setSourceModel(model)
                table_view.setModel(proxy_model)
                self.proxy_models[sheet_name] = proxy_model
                
                # 设置表头点击事件
                header = table_view.horizontalHeader()
                header.setSectionsClickable(True)
                header.sectionClicked.connect(lambda col, tv=table_view: self.show_filter_menu(tv, col))
                
                # 禁用右键菜单
                table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
                
                self.tab_widget.addTab(table_view, sheet_name)
                if sheet_name == state.workbook.sheet_names[0]:
                    state.workbook.tab_widget.setCurrentIndex(0)
        except Exception as e:
                        ErrorHandler.handle_error(e, self, "加载Excel文件时发生错误")

    def show_filter_menu(self, table_view, column):
        """显示筛选菜单"""
        header = table_view.horizontalHeader()
        
        # 创建菜单
        menu = QMenu(table_view)
        
        # 获取当前sheet名称
        current_index = self.tab_widget.currentIndex()
        sheet_name = self.tab_widget.tabText(current_index)
        proxy_model = self.proxy_models[sheet_name]
        
        # 创建筛选控件
        filter_widget = ColumnFilterWidget(proxy_model, column)
        
        # 创建一个QWidgetAction并设置自定义控件
        widget_action = QWidgetAction(menu)
        widget_action.setDefaultWidget(filter_widget)
        
        # 添加标题和分隔符
        title_action = menu.addAction("筛选")
        title_action.setEnabled(False)
        menu.addSeparator()
        
        # 添加筛选控件
        menu.addAction(widget_action)
        
        # 显示菜单
        header_pos = header.mapToGlobal(header.pos())
        pos = header_pos + QPoint(header.sectionPosition(column), header.height())
        menu.exec(pos)

    def save_excel(self):
        try:
            # Save Excel file
            state = GlobalState()
            with pd.ExcelWriter(state.workbook.file_path, engine='openpyxl') as writer:
                for sheet_name, df in state.workbook.workbook.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            ErrorHandler.handle_info(f"Workbook saved to {state.workbook.file_path}")
        except Exception as e:
            ErrorHandler.handle_error(e, None, "保存Excel文件时发生错误")

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self.modified = False
        self.dataChanged.connect(self.on_data_changed)

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid() and role == Qt.ItemDataRole.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole) -> bool:
        if role == Qt.ItemDataRole.EditRole:
            row = index.row()
            col = index.column()
            try:
                # 使用 iloc 进行定位和赋值
                self._data.iloc[row, col] = value
                self.modified = True  # 标记为已修改
                self.dataChanged.emit(index, index, [role])
                return True
            except Exception as e:
                print(f"设置数据时出错: {str(e)}")
                return False
        return False

    def has_changes(self):
        return self.modified
    def on_data_changed(self, top_left, bottom_right, roles):
        self.modified = True  # Mark as modified when data changes
    def save_data(self):
        # Placeholder for saving the data
        print("数据已保存。")
        self.modified = False  # Reset modified flag after saving
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._data.columns[section]
            else:
                return str(self._data.index[section])
        return None
