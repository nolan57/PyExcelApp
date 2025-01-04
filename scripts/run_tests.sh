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