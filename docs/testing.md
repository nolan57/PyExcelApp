# 测试文档

## 测试架构

### 目录结构
```
tests/
├── conftest.py                # 共享fixtures
├── utils/
│   └── test_helpers.py       # 测试辅助函数
├── unit/                     # 单元测试
│   ├── monitoring/          # 监控相关
│   ├── plugin/             # 插件相关
│   └── excel/              # Excel相关
├── integration/             # 集成测试
│   ├── test_plugin_system_integration.py  # 渐进式测试
│   ├── test_monitoring_integration.py     # 渐进式测试
│   └── test_functional_integration.py     # 功能性测试
└── performance/            # 性能测试
```

### 测试类型
1. 单元测试
   - 监控框架测试
   - 插件系统测试
   - Excel操作测试

2. 集成测试
   - 渐进式测试（Level 1-3）
   - 功能性测试

3. 性能测试
   - 监控性能测试
   - 插件系统性能测试

## 运行测试

### 基本命令
```bash
# 运行所有测试
./scripts/run_tests.sh

# 运行单元测试
./scripts/run_tests.sh unit

# 运行集成测试
./scripts/run_tests.sh integration

# 运行性能测试
./scripts/run_tests.sh performance

# 运行特定级别的集成测试
./scripts/run_tests.sh level1
./scripts/run_tests.sh level2
./scripts/run_tests.sh level3

# 生成覆盖率报告
./scripts/run_tests.sh coverage
```

### 测试标记
- `slow`: 标记慢速测试
- `gui`: 标记GUI测试
- `benchmark`: 标记基准测试
- `integration`: 标记集成测试
- `monitoring`: 标记监控测试
- `excel`: 标记Excel操作测试
- `level1/2/3`: 标记集成测试级别
- `functional`: 标记功能测试

## 持续集成

### CI流程
1. 代码提交触发CI
2. 运行所有测试
3. 代码风格检查
4. 生成覆盖率报告

### CD流程
1. 版本标签触发CD
2. 构建包
3. 发布到PyPI

### 文档生成
1. 主分支更新触发
2. 生成文档
3. 部署到GitHub Pages

## 测试覆盖率要求
- 总体覆盖率目标：80%
- 核心模块覆盖率目标：90%
- 每次提交必须维持或提高覆盖率

## 编写测试指南

### 单元测试
1. 每个功能点至少一个测试用例
2. 包含正常和异常情况
3. 使用参数化测试减少重复

### 集成测试
1. 按复杂度递增编写
2. 确保组件间交互
3. 包含完整工作流

### 性能测试
1. 设置明确的性能指标
2. 包含基准测试
3. 监控性能退化 


## 测试示例
1. 目录结构检查：
```
dependency_monitoring_framework/
├── src/
│   ├── config/
│   │   └── config.json  ✅ (已配置)
│   ├── core/
│   │   ├── health_checker.py  ✅
│   │   └── notification_manager.py  ✅
│   ├── interfaces/
│   │   ├── health_check_plugin.py  ✅
│   │   └── notification_channel.py  ✅
│   └── services/
│       ├── security_scanner.py  ✅ (已更新)
│       ├── version_checker.py  ✅
│       └── compatibility_checker.py  ✅
tests/
├── conftest.py  ✅ (已配置)
├── unit/
│   └── monitoring/
│       └── test_dependency_monitoring.py  ✅ (已更新)
└── integration/
    └── test_monitoring_integration.py  ✅
```

2. 依赖检查：
需要确保安装了所有必要的依赖：
```bash
pip install -r test-requirements.txt
```

3. 环境变量检查：
需要设置必要的环境变量：
```bash
export PYTHONPATH="${PYTHONPATH}:${PWD}/dependency_monitoring_framework:${PWD}/plugin_manager"
```

4. 测试运行前的准备：

创建一个测试启动脚本 `run_monitoring_tests.sh`:
```bash
#!/bin/bash

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:${PWD}/dependency_monitoring_framework:${PWD}/plugin_manager"

# 运行单元测试
echo "Running unit tests..."
pytest tests/unit/monitoring/ -v

# 运行集成测试
echo "Running integration tests..."
pytest tests/integration/test_monitoring_integration.py -v

# 生成覆盖率报告
echo "Generating coverage report..."
pytest --cov=dependency_monitoring_framework tests/ --cov-report=html
```

5. 测试运行命令：
```bash
# 给脚本添加执行权限
chmod +x run_monitoring_tests.sh

# 运行测试
./run_monitoring_tests.sh
```

6. 需要确认的事项：

a. 配置文件检查：
- config.json 中的配置是否正确
- OSS Index 的认证信息是否已配置（如果需要）

b. 依赖项检查：
```python
# 检查 requirements.txt 是否包含所有必要依赖
requests>=2.28.1
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-asyncio>=0.21.0
aiohttp>=3.8.0
```

c. 测试数据准备：
- 确保有测试用的 requirements.txt
- 确保有测试用的配置文件

7. 建议的测试步骤：

```bash
# 1. 首先只运行单个测试文件
pytest tests/unit/monitoring/test_dependency_monitoring.py -v

# 2. 如果成功，运行所有单元测试
pytest tests/unit/ -v

# 3. 然后运行集成测试
pytest tests/integration/ -v

# 4. 最后运行完整测试套件并生成覆盖率报告
pytest --cov=dependency_monitoring_framework tests/ --cov-report=html
```

创建测试启动脚本：
创建一个专门用于监控框架测试的脚本：

````bash:scripts/run_monitoring_tests.sh
#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:${PWD}/dependency_monitoring_framework:${PWD}/plugin_manager"

# 运行单个测试文件
run_single_test() {
    echo -e "${BLUE}Running single test file...${NC}"
    pytest tests/unit/monitoring/test_dependency_monitoring.py -v
}

# 运行单元测试
run_unit_tests() {
    echo -e "${BLUE}Running unit tests...${NC}"
    pytest tests/unit/monitoring/ -v
}

# 运行集成测试
run_integration_tests() {
    echo -e "${BLUE}Running integration tests...${NC}"
    pytest tests/integration/test_monitoring_integration.py -v
}

# 运行覆盖率测试
run_coverage() {
    echo -e "${BLUE}Running tests with coverage...${NC}"
    pytest --cov=dependency_monitoring_framework tests/ --cov-report=html
    echo -e "${GREEN}Coverage report generated in coverage_html/index.html${NC}"
}

# 运行完整测试套件
run_all() {
    echo -e "${BLUE}Running complete test suite...${NC}"
    
    echo -e "\n${BLUE}1. Running single test file...${NC}"
    run_single_test
    
    echo -e "\n${BLUE}2. Running all unit tests...${NC}"
    run_unit_tests
    
    echo -e "\n${BLUE}3. Running integration tests...${NC}"
    run_integration_tests
    
    echo -e "\n${BLUE}4. Generating coverage report...${NC}"
    run_coverage
}

# 检查依赖
check_dependencies() {
    echo -e "${BLUE}Checking dependencies...${NC}"
    pip install -r test-requirements.txt
}

# 主函数
main() {
    case "$1" in
        "single")
            run_single_test
            ;;
        "unit")
            run_unit_tests
            ;;
        "integration")
            run_integration_tests
            ;;
        "coverage")
            run_coverage
            ;;
        "check")
            check_dependencies
            ;;
        *)
            run_all
            ;;
    esac
}

# 运行主函数
main "$@"
````

修改主测试脚本以包含监控测试：

````bash:scripts/run_tests.sh
#!/bin/bash

# 添加PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}/dependency_monitoring_framework:${PWD}/plugin_manager"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 运行所有测试
run_all() {
    echo -e "${BLUE}Running all tests...${NC}"
    pytest -v
}

# 运行单元测试
run_unit() {
    echo -e "${BLUE}Running unit tests...${NC}"
    pytest tests/unit/ -v
}

# 运行集成测试
run_integration() {
    echo -e "${BLUE}Running integration tests...${NC}"
    pytest tests/integration/ -v
}

# 运行性能测试
run_performance() {
    echo -e "${BLUE}Running performance tests...${NC}"
    pytest tests/performance/ -v
}

# 运行特定级别的集成测试
run_level() {
    level=$1
    echo -e "${BLUE}Running level ${level} integration tests...${NC}"
    pytest -v -m "level${level}"
}

# 运行覆盖率报告
run_coverage() {
    echo -e "${BLUE}Running tests with coverage...${NC}"
    pytest --cov=src --cov-report=html
    echo -e "${GREEN}Coverage report generated in coverage_html/index.html${NC}"
}

# 运行监控测试
run_monitoring() {
    echo -e "${BLUE}Running monitoring tests...${NC}"
    ./scripts/run_monitoring_tests.sh
}

# 检查依赖
check_dependencies() {
    echo -e "${BLUE}Checking dependencies...${NC}"
    pip install -r test-requirements.txt
}

# 主函数
main() {
    case "$1" in
        "unit")
            run_unit
            ;;
        "integration")
            run_integration
            ;;
        "performance")
            run_performance
            ;;
        "level1"|"level2"|"level3")
            run_level "${1#level}"
            ;;
        "coverage")
            run_coverage
            ;;
        "monitoring")
            run_monitoring
            ;;
        "check")
            check_dependencies
            ;;
        *)
            run_all
            ;;
    esac
}

# 运行主函数
main "$@"
````

使用方法：

1. 给脚本添加执行权限：
````bash
chmod +x scripts/run_tests.sh
chmod +x scripts/run_monitoring_tests.sh
````

2. 运行测试：
````bash
# 运行所有测试
./scripts/run_tests.sh

# 只运行监控测试
./scripts/run_tests.sh monitoring

# 只运行单元测试
./scripts/run_tests.sh unit

# 检查依赖
./scripts/run_tests.sh check
````

3. 运行特定的监控测试：
````bash
# 运行单个监控测试文件
./scripts/run_monitoring_tests.sh single

# 运行监控单元测试
./scripts/run_monitoring_tests.sh unit

# 运行监控集成测试
./scripts/run_monitoring_tests.sh integration
````