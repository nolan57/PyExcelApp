"""测试辅助函数"""
import pandas as pd
from PyQt6.QtWidgets import QTableView

def create_test_data():
    """创建测试数据"""
    return pd.DataFrame({
        'Column1': ['A1', 'A2', 'A3'],
        'Column2': [1, 2, 3],
        'Column3': ['X', 'Y', 'Z']
    })

def create_test_table_view(data):
    """创建测试表格视图"""
    table_view = QTableView()
    # 设置模型
    from utils.excel_operations import PandasModel
    model = PandasModel(data)
    table_view.setModel(model)
    return table_view 