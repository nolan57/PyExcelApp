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