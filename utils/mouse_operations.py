from PyQt6.QtWidgets import QTableView, QTabWidget, QApplication
from PyQt6.QtCore import QObject, QEvent, QPoint, Qt, pyqtSignal, QModelIndex
from PyQt6.QtGui import QMouseEvent

class MouseOperations(QObject):
    cellClicked = pyqtSignal(int, int)
    
    def __init__(self, current_sheet: QTableView, parent=None):
        super().__init__(parent)
        if not isinstance(current_sheet, QTableView):
            raise TypeError("current_sheet must be a QTableView instance")
            
        self.table_view = current_sheet
        self._is_connected = False

    def on_cell_clicked(self, index: QModelIndex):
        """处理单元格点击事件"""
        if not index.isValid():
            return
            
        # 直接发送信号，不存储状态
        self.cellClicked.emit(index.row(), index.column())

    def connect_cell_clicked(self):
        """连接单元格点击信号"""
        if not self._is_connected:
            self.table_view.clicked.connect(self.on_cell_clicked)
            self._is_connected = True

    def disconnect_cell_clicked(self):
        """断开单元格点击信号"""
        if self._is_connected:
            try:
                self.table_view.clicked.disconnect(self.on_cell_clicked)
            except TypeError:
                # 信号可能已经断开，忽略错误
                pass
            self._is_connected = False

    def is_connected(self):
        """返回信号是否已连接"""
        return self._is_connected
