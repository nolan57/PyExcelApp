import pytest
from response.response import Response

def test_response_initialization(sample_response):
    """测试Response类的初始化"""
    response = Response(sample_response)
    assert response.content == sample_response["content"]
    assert response.role == sample_response["role"]
    assert response.metadata == sample_response["metadata"]

def test_response_to_markdown(sample_response):
    """测试响应转换为markdown格式"""
    response = Response(sample_response)
    markdown = response.to_markdown()
    assert isinstance(markdown, str)
    assert markdown.startswith("# ")

def test_invalid_response():
    """测试无效响应处理"""
    with pytest.raises(ValueError):
        Response({})  # 空响应应该引发错误

def test_response_formatting():
    """测试响应格式化"""
    response = Response({
        "content": "```python\nprint('hello')\n```",
        "role": "assistant",
        "metadata": {"format": "code"}
    })
    formatted = response.format_content()
    assert "```python" in formatted 

def test_response_with_empty_content():
    """测试空内容响应"""
    response = Response({
        "content": "",
        "role": "assistant",
        "metadata": {"format": "text"}
    })
    assert response.content == ""
    assert response.to_markdown() == ""

def test_response_with_special_characters():
    """测试包含特殊字符的响应"""
    special_content = "# Title with *special* chars\n> Quote with `code`"
    response = Response({
        "content": special_content,
        "role": "assistant",
        "metadata": {"format": "markdown"}
    })
    result = response.to_markdown()
    assert "*special*" in result
    assert "`code`" in result

@pytest.mark.parametrize("metadata_format", [
    "markdown",
    "code",
    "text",
    None
])
def test_response_different_formats(metadata_format):
    """测试不同格式的响应"""
    response = Response({
        "content": "test content",
        "role": "assistant",
        "metadata": {"format": metadata_format} if metadata_format else {}
    })
    assert response.to_markdown() is not None 