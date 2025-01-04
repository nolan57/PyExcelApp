import pytest
import time
import pandas as pd
from excel_processor import ExcelProcessor

def test_large_file_processing_performance(tmp_path):
    """测试大文件处理性能"""
    # 创建大型测试数据
    large_df = pd.DataFrame({
        'Column1': range(10000),
        'Column2': range(10000),
        'Column3': range(10000)
    })
    
    file_path = tmp_path / "large_test.xlsx"
    large_df.to_excel(file_path, index=False)
    
    processor = ExcelProcessor()
    
    # 测量处理时间
    start_time = time.time()
    result = processor.process_file(file_path)
    end_time = time.time()
    
    processing_time = end_time - start_time
    assert processing_time < 5.0  # 确保处理时间在可接受范围内
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 10000

@pytest.mark.benchmark
def test_data_processing_benchmark(benchmark, sample_excel_data):
    """基准测试数据处理性能"""
    processor = ExcelProcessor()
    
    # 使用pytest-benchmark进行性能测试
    result = benchmark(processor.process_data, sample_excel_data)
    assert isinstance(result, pd.DataFrame) 