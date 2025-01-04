def format_markdown(text):
    """格式化Markdown文本"""
    if not text:
        return ""
    return text.strip()
    
def clean_text(text):
    """清理文本内容"""
    if not text:
        return ""
    return text.strip() 