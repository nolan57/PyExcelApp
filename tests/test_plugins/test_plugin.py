from plugin_manager.core.plugin_base import PluginBase

class TestPlugin(PluginBase):
    def get_name(self) -> str:
        return "Test Plugin"
        
    def get_version(self) -> str:
        return "1.0.0"
        
    def get_description(self) -> str:
        return "A simple test plugin"
        
    def process_data(self, table_view, **parameters):
        return "Test Plugin processed data"
