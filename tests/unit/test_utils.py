import pytest
from tests.src.response.utils import format_markdown, clean_text

def test_format_markdown():
    """测试Markdown格式化"""
    test_text = "  # Title  \n  * Item  "
    result = format_markdown(test_text)
    assert result == "# Title  \n  * Item"
    
def test_clean_text():
    """测试文本清理"""
    test_text = "  Hello  World  "
    result = clean_text(test_text)
    assert result == "Hello  World" 