import pytest
from response.utils import format_markdown, clean_text

def test_format_markdown(sample_file_content):
    """测试markdown格式化功能"""
    formatted = format_markdown(sample_file_content)
    assert formatted.startswith("# ")
    assert "\n\n" in formatted

def test_clean_text():
    """测试文本清理功能"""
    dirty_text = "  测试文本\n\n多余的空行\r\n  "
    clean = clean_text(dirty_text)
    assert clean == "测试文本\n多余的空行"

def test_empty_text():
    """测试空文本处理"""
    assert clean_text("") == ""
    assert clean_text(None) == "" 

@pytest.mark.parametrize("input_text,expected", [
    ("  多余空格  ", "多余空格"),
    ("\n\n多行\n\n", "多行"),
    ("混合\r\n换行", "混合\n换行"),
    ("保留\n单个\n换行", "保留\n单个\n换行")
])
def test_clean_text_variations(input_text, expected):
    """测试不同文本清理场景"""
    assert clean_text(input_text) == expected

def test_format_markdown_complex():
    """测试复杂markdown格式化"""
    complex_md = """
    # 标题
    
    ## 子标题
    
    - 列表项1
    - 列表项2
    
    ```python
    def test():
        pass
    ```
    """
    formatted = format_markdown(complex_md)
    assert "# 标题" in formatted
    assert "## 子标题" in formatted
    assert "```python" in formatted 