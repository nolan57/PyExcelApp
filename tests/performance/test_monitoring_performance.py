"""监控系统性能测试"""
import pytest
import time
from dependency_monitoring_framework.src.core.health_checker import HealthChecker
from dependency_monitoring_framework.src.services.version_checker import VersionChecker

@pytest.mark.performance
class TestMonitoringPerformance:
    def test_health_check_performance(self):
        """测试健康检查性能"""
        health_checker = HealthChecker()
        
        # 添加多个检查器
        for i in range(10):
            checker = VersionChecker()
            health_checker.register_plugin(f"version_{i}", checker)
        
        # 测量执行时间
        start_time = time.time()
        health_checker.check_health()
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 2.0  # 确保执行时间在可接受范围内 