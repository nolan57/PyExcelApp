class Response:
    """响应类，用于处理和格式化响应"""
    
    def __init__(self, content=None, status=None):
        self.content = content
        self.status = status
        
    def format(self):
        """格式化响应内容"""
        if not self.content:
            return ""
        return str(self.content)
        
    def is_success(self):
        """检查是否成功响应"""
        return self.status == "success" 