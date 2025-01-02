# 依赖监控框架

一个用于监控和管理软件依赖的框架，提供以下功能：

- 版本检查
- 安全漏洞扫描
- 兼容性验证
- 完整性检查
- 通知系统

## 功能

### 健康检查
- **版本检查器**: 验证依赖是否是最新版本
- **安全扫描器**: 检查已知漏洞
- **兼容性检查器**: 验证依赖的兼容性
- **完整性验证器**: 验证依赖的完整性

### 通知渠道
- **邮件通知器**: 通过邮件发送通知
- **Slack通知器**: 将通知发布到Slack
- **控制台通知器**: 在控制台打印通知
- **日志通知器**: 将通知记录到文件
- **API通知器**: 通过API发送通知

## 配置

配置通过`config.json`或环境变量管理。主要配置选项包括：

```json
{
  "notification_channels": [
    {
      "type": "email",
      "config": {
        "smtp_server": "smtp.example.com",
        "smtp_port": 587,
        "smtp_user": "user@example.com",
        "smtp_password": "password",
        "from_email": "noreply@example.com",
        "to_email": "admin@example.com"
      }
    }
  ],
  "health_check_plugins": [
    {
      "type": "version",
      "config": {
        "base_url": "https://registry.example.com",
        "timeout": 5
      }
    }
  ]
}
```

## 使用

```python
from dependency_monitoring_framework.core.health_checker import HealthChecker
from dependency_monitoring_framework.core.event_bus import EventBus

event_bus = EventBus()
health_checker = HealthChecker(event_bus)

# 运行所有健康检查
results = health_checker.run_checks()
```

## 安装

```bash
pip install -r requirements.txt
```

## 贡献

欢迎贡献！请遵循贡献指南。

## 许可证

MIT许可证
