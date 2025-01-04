"""插件管理系统"""

# 向下兼容的导入
from .core.plugin_interface import PluginInterface
from .core.plugin_base import PluginBase
from .core.plugin_system import PluginSystem
from .features.plugin_permissions import PluginPermission
from .utils.plugin_error import PluginError, PluginLoadError, PluginConfigError

# 保持旧的导入路径可用
import sys
from pathlib import Path

# 添加向下兼容的导入路径
_current_dir = Path(__file__).parent
sys.path.append(str(_current_dir))

# 为了向下兼容，保持旧的导入方式可用
from .core.plugin_interface import PluginInterface as Interface
from .core.plugin_base import PluginBase as Base
from .features.plugin_permissions import PluginPermission as Permission 