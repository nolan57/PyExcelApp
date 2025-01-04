import pandas as pd
from typing import Union, Dict, Any

class ExcelProcessor:
    """Excel文件处理器"""
    
    def __init__(self):
        self.current_file = None
        self.data = None
        
    def process_file(self, file_path: str) -> pd.DataFrame:
        """处理Excel文件
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            处理后的DataFrame
        """
        try:
            self.current_file = file_path
            self.data = pd.read_excel(file_path)
            return self.data
        except Exception as e:
            raise ValueError(f"处理Excel文件失败: {str(e)}")
            
    def save_file(self, df: pd.DataFrame, file_path: str) -> bool:
        """保存DataFrame到Excel文件
        
        Args:
            df: 要保存的DataFrame
            file_path: 保存路径
            
        Returns:
            是否保存成功
        """
        try:
            df.to_excel(file_path, index=False)
            return True
        except Exception as e:
            raise ValueError(f"保存Excel文件失败: {str(e)}")
            
    def get_sheet_names(self) -> list:
        """获取所有工作表名称"""
        if not self.current_file:
            return []
        return pd.ExcelFile(self.current_file).sheet_names
        
    def get_sheet_data(self, sheet_name: str) -> pd.DataFrame:
        """获取指定工作表的数据
        
        Args:
            sheet_name: 工作表名称
            
        Returns:
            工作表数据
        """
        if not self.current_file:
            raise ValueError("未加载Excel文件")
        return pd.read_excel(self.current_file, sheet_name=sheet_name) 