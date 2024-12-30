class PluginErrorHandler:
    def handle_error(self, plugin_name: str, error: Exception) -> None:
        """处理插件错误"""
        pass
        
    def recover_plugin(self, plugin_name: str) -> bool:
        """尝试恢复出错的插件"""
        pass 