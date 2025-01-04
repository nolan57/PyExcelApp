import pytest
import os
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

def test_file_open_workflow(mock_main_window, temp_excel_file, monkeypatch):
    """测试文件打开工作流"""
    # 模拟文件对话框
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', 
                       lambda *args, **kwargs: (str(temp_excel_file), ''))
    
    # 触发打开文件动作
    mock_main_window.open_file_action.trigger()
    
    # 验证数据是否正确加载
    assert mock_main_window.table_view.model() is not None
    assert mock_main_window.table_view.model().rowCount() > 0

def test_data_processing_workflow(mock_main_window, sample_excel_data):
    """测试数据处理工作流"""
    # 加载数据
    mock_main_window.load_data(sample_excel_data)
    
    # 执行数据处理
    mock_main_window.process_data()
    
    # 验证处理结果
    processed_data = mock_main_window.get_current_data()
    assert processed_data is not None
    assert not processed_data.empty

def test_save_workflow(mock_main_window, sample_excel_data, tmp_path, monkeypatch):
    """测试保存工作流"""
    output_file = tmp_path / "output.xlsx"
    
    # 模拟保存对话框
    monkeypatch.setattr(QFileDialog, 'getSaveFileName',
                       lambda *args, **kwargs: (str(output_file), ''))
    
    # 加载数据并保存
    mock_main_window.load_data(sample_excel_data)
    mock_main_window.save_file_action.trigger()
    
    # 验证文件保存
    assert output_file.exists() 