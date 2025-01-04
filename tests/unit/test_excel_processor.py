import pytest
import pandas as pd
from tests.src.excel_processor import ExcelProcessor

def test_excel_file_loading(temp_excel_file):
    """测试Excel文件加载"""
    processor = ExcelProcessor()
    df = processor.process_file(temp_excel_file)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty

def test_excel_file_saving(temp_excel_file, tmp_path):
    """测试Excel文件保存"""
    processor = ExcelProcessor()
    df = processor.process_file(temp_excel_file)
    
    # 保存到新文件
    new_file = tmp_path / "new.xlsx"
    result = processor.save_file(df, new_file)
    assert result is True
    assert new_file.exists()

def test_invalid_file():
    """测试无效文件处理"""
    processor = ExcelProcessor()
    with pytest.raises(ValueError):
        processor.process_file("nonexistent.xlsx")

def test_sheet_operations(temp_excel_file):
    """测试工作表操作"""
    processor = ExcelProcessor()
    processor.process_file(temp_excel_file)
    
    # 获取工作表名称
    sheets = processor.get_sheet_names()
    assert isinstance(sheets, list)
    assert len(sheets) > 0
    
    # 获取工作表数据
    df = processor.get_sheet_data(sheets[0])
    assert isinstance(df, pd.DataFrame)
    assert not df.empty 