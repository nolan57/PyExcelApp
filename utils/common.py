"""
通用工具函数模块
"""
from typing import Union, Optional

def safe_float_convert(value: Union[str, int, float, None], default: float = 0.0) -> float:
    """
    安全地将值转换为浮点数
    
    Args:
        value: 要转换的值，可以是字符串、整数、浮点数或None
        default: 转换失败时返回的默认值，默认为0.0
        
    Returns:
        float: 转换后的浮点数，如果转换失败则返回默认值
        
    Examples:
        >>> safe_float_convert("123.45")
        123.45
        >>> safe_float_convert("invalid")
        0.0
        >>> safe_float_convert(None)
        0.0
        >>> safe_float_convert("1,234.56")
        1234.56
    """
    if value is None or value == '' or (isinstance(value, str) and value.strip() == ''):
        return default
        
    try:
        # 如果是字符串，移除可能的空白字符和逗号
        if isinstance(value, str):
            value = value.strip().replace(',', '')
        return float(value)
    except (ValueError, TypeError):
        return default
