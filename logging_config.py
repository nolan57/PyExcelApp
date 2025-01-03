import logging
from logging.handlers import RotatingFileHandler
from enum import Enum

class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

class LoggingConfig:
    def __init__(self, log_file_path: str, max_bytes: int = 1024 * 1024 * 5, backup_count: int = 5):
        self.log_file_path = log_file_path
        self.max_bytes = max_bytes
        self.backup_count = backup_count

    def configure_logging(self, level: LogLevel = LogLevel.INFO):
        """
        配置日志记录

        Args:
            level: 日志级别，可选值为 LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL
        """
        # 创建日志记录器
        logger = logging.getLogger()
        logger.setLevel(level.value)

        # 创建文件处理器，支持日志轮转
        file_handler = RotatingFileHandler(
            self.log_file_path,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count
        )
        file_handler.setLevel(level.value)

        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level.value)

        # 创建日志格式化器
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 移除默认的日志处理器（如果有）
        if logger.hasHandlers():
            logger.handlers.clear()

        # 添加处理器到日志记录器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        logging.info(f"Logging configured with level: {level.name} and file: {self.log_file_path}")

# 示例使用
if __name__ == "__main__":
    log_config = LoggingConfig('app.log')
    log_config.configure_logging(LogLevel.DEBUG)
    logging.debug("This is a debug message")
    logging.info("This is an info message")
    logging.warning("This is a warning message")
    logging.error("This is an error message")
    logging.critical("This is a critical message")