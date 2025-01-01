# 测试包初始化文件
import os
import sys

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 测试配置
TEST_PLUGIN_DIR = os.path.join(os.path.dirname(__file__), 'test_plugins')
