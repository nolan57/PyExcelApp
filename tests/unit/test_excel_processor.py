import pytest
import pandas as pd
from excel_processor import ExcelProcessor

def test_excel_file_loading(temp_excel_file):
    """测试Excel文件加载功能"""
    processor = ExcelProcessor()
    df = processor.process_file(temp_excel_file)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert list(df.columns) == ['Column1', 'Column2', 'Column3']

def test_data_processing(sample_excel_data):
    """测试数据处理功能"""
    processor = ExcelProcessor()
    result = processor.process_data(sample_excel_data)
    assert isinstance(result, pd.DataFrame)
    assert 'Column1' in result.columns
    
@pytest.mark.parametrize("invalid_path", [
    "nonexistent.xlsx",
    "invalid/path/file.xlsx",
    ""
])
def test_invalid_file_handling(invalid_path):
    """测试无效文件处理"""
    processor = ExcelProcessor()
    with pytest.raises(FileNotFoundError):
        processor.process_file(invalid_path)

def test_save_excel_file(tmp_path, sample_excel_data):
    """测试Excel文件保存功能"""
    output_path = tmp_path / "output.xlsx"
    processor = ExcelProcessor()
    success = processor.save_file(sample_excel_data, output_path)
    assert success
    assert output_path.exists()
    
    # 验证保存的数据
    loaded_df = pd.read_excel(output_path)
    pd.testing.assert_frame_equal(loaded_df, sample_excel_data) 