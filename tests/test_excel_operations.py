import unittest
from unittest.mock import MagicMock
from PyQt6.QtCore import QModelIndex, Qt
from PyQt6.QtWidgets import QApplication, QTableView
from test_src.utils.excel_operations import ExcelOperations, PandasModel
from plugin_manager.plugins.xzltxs_test import XzltxsPlugin
from plugin_manager.features.plugin_permissions import PluginPermission
import pandas as pd
import sys

# Ensure QApplication exists before running tests
app = QApplication.instance() or QApplication(sys.argv)

class TestExcelOperations(unittest.TestCase):
    def setUp(self):
        self.tab_widget = MagicMock()
        self.excel_ops = ExcelOperations(self.tab_widget)
        
    def test_load_excel(self):
        # 测试加载Excel文件
        test_data = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        mock_state = MagicMock()
        mock_state.workbook.tab_widget = MagicMock()
        
        with unittest.mock.patch('pandas.read_excel', return_value={'Sheet1': test_data}), \
             unittest.mock.patch('utils.excel_operations.GlobalState', return_value=mock_state):
            self.excel_ops.load_excel('test.xlsx')
            
            # 验证数据是否正确加载
            self.assertIsNotNone(self.excel_ops.data)
            self.assertEqual(len(self.excel_ops.proxy_models), 1)
            
    def test_save_excel(self):
        # 测试保存Excel文件
        test_data = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        self.excel_ops.data = {'Sheet1': test_data}
        
        with unittest.mock.patch('pandas.ExcelWriter') as mock_writer:
            self.excel_ops.save_excel()
            mock_writer.assert_called_once()

    def test_data_processing(self):
        plugin = XzltxsPlugin()
        # 创建真实的QTableView实例
        table_view = QTableView()
        # 创建并设置模型
        test_data = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        model = PandasModel(test_data)
        table_view.setModel(model)
        
        # 激活插件
        plugin.activate({
            PluginPermission.FILE_READ,
            PluginPermission.FILE_WRITE,
            PluginPermission.UI_MODIFY,
            PluginPermission.DATA_READ,
            PluginPermission.DATA_WRITE
        })
        
        # 测试数据处理
        try:
            result = plugin.process_data(table_view)
            self.assertTrue(result)
        except Exception as e:
            self.fail(f"测试失败，异常信息: {str(e)}")

class TestPandasModel(unittest.TestCase):
    def setUp(self):
        self.test_data = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        self.model = PandasModel(self.test_data)
        
    def test_rowCount(self):
        self.assertEqual(self.model.rowCount(), 2)
        
    def test_columnCount(self):
        self.assertEqual(self.model.columnCount(), 2)
        
    def test_data(self):
        index = self.model.index(0, 0)
        self.assertEqual(self.model.data(index), '1')
        
    def test_setData(self):
        index = self.model.index(0, 0)
        self.assertTrue(self.model.setData(index, 5, Qt.ItemDataRole.EditRole))
        self.assertEqual(self.model._data.iloc[0, 0], 5)

if __name__ == '__main__':
    unittest.main()
