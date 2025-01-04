"""依赖安全扫描服务"""
import os
import json
import requests
from typing import Dict, List, Optional
from ..core.event_bus import EventBus
from ..interfaces.health_check_plugin import HealthCheckPlugin

class SecurityScanner(HealthCheckPlugin):
    """使用OSS Index的安全扫描器"""
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus
        self._load_config()

    def _load_config(self):
        """从配置文件加载设置"""
        try:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '..', 'config', 'config.json'
            )
            with open(config_path, 'r') as f:
                config = json.load(f)
                security_config = config.get('security', {})
                oss_config = security_config.get('oss_index', {})
                
                self.base_url = oss_config.get(
                    'base_url', 
                    'https://ossindex.sonatype.org/api/v3/component-report'
                )
                self.headers = oss_config.get('headers', {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                })
                
                # 认证配置
                auth_config = oss_config.get('auth', {})
                if auth_config.get('username') and auth_config.get('api_key'):
                    self.auth = (
                        auth_config['username'],
                        auth_config['api_key']
                    )
                else:
                    self.auth = None
                
                # 检查配置
                self.check_config = security_config.get('check', {
                    'severity_threshold': 'medium',
                    'check_outdated': True,
                    'auto_update': False
                })
        except Exception as e:
            if self.event_bus:
                self.event_bus.emit('config_error', {
                    'component': 'SecurityScanner',
                    'error': str(e)
                })
            # 使用默认配置
            self.base_url = 'https://ossindex.sonatype.org/api/v3/component-report'
            self.headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            self.auth = None
            self.check_config = {
                'severity_threshold': 'medium',
                'check_outdated': True,
                'auto_update': False
            }

    def _format_package(self, package: str, version: str) -> str:
        """格式化包名为OSS Index格式"""
        return f"pkg:pypi/{package}@{version}"

    def check_package(self, package: str, version: str) -> Dict:
        """检查单个包的安全漏洞"""
        coordinates = [self._format_package(package, version)]
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                auth=self.auth,
                json={"coordinates": coordinates}
            )
            response.raise_for_status()
            return response.json()[0]
        except Exception as e:
            if self.event_bus:
                self.event_bus.emit('security_check_error', {
                    'package': package,
                    'error': str(e)
                })
            return {
                'coordinates': coordinates[0],
                'vulnerabilities': [],
                'error': str(e)
            }

    def check_dependencies(self, dependencies: List[Dict[str, str]]) -> Dict:
        """检查多个依赖的安全漏洞"""
        coordinates = [
            self._format_package(dep['name'], dep['version'])
            for dep in dependencies
        ]
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                auth=self.auth,
                json={"coordinates": coordinates}
            )
            response.raise_for_status()
            return {
                'status': 'success',
                'reports': response.json()
            }
        except Exception as e:
            if self.event_bus:
                self.event_bus.emit('security_check_error', {
                    'error': str(e)
                })
            return {
                'status': 'error',
                'error': str(e),
                'reports': []
            }

    def check(self) -> Dict:
        """实现HealthCheckPlugin接口的健康检查方法"""
        try:
            # 从项目的requirements.txt读取依赖
            dependencies = self._get_project_dependencies()
            result = self.check_dependencies(dependencies)
            
            # 分析结果
            vulnerabilities = []
            for report in result.get('reports', []):
                vulns = report.get('vulnerabilities', [])
                # 处理 None 值的情况
                if vulns is None:
                    vulns = []
                # 根据严重性阈值过滤漏洞
                threshold = self.check_config['severity_threshold']
                vulns = [v for v in vulns if self._is_severe_enough(v, threshold)]
                vulnerabilities.extend(vulns)
            
            return {
                'status': 'error' if vulnerabilities else 'healthy',
                'vulnerabilities': vulnerabilities,
                'total_packages': len(dependencies),
                'vulnerable_packages': len(set(v.get('package') for v in vulnerabilities))
            }
        except Exception as e:
            if self.event_bus:
                self.event_bus.emit('security_check_error', {
                    'error': str(e)
                })
            return {
                'status': 'error',
                'error': str(e),
                'vulnerabilities': []  # 确保总是返回 vulnerabilities 字段
            }

    def _get_project_dependencies(self) -> List[Dict[str, str]]:
        """获取项目依赖列表"""
        try:
            with open('requirements.txt', 'r') as f:
                deps = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split('==')
                        if len(parts) == 2:
                            deps.append({
                                'name': parts[0],
                                'version': parts[1]
                            })
                return deps
        except Exception as e:
            if self.event_bus:
                self.event_bus.emit('dependency_error', {
                    'error': str(e)
                })
            return []

    def _is_severe_enough(self, vulnerability: Dict, threshold: str) -> bool:
        """检查漏洞是否达到严重性阈值"""
        severity_levels = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
        vuln_severity = vulnerability.get('severity', 'low').lower()
        return severity_levels.get(vuln_severity, 0) >= severity_levels.get(threshold, 0)

    def configure(self, config: Dict) -> None:
        """配置扫描器"""
        self.config = config
        
    def get_status(self) -> str:
        """获取当前状态"""
        try:
            result = self.check()
            return result.get('status', 'error')
        except Exception:
            return 'error'
