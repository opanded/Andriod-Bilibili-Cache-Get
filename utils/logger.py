"""日志工具模块"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logger(name: str, config) -> logging.Logger:
    """配置日志记录器

    Args:
        name: 日志记录器名称
        config: 配置对象

    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL))

    if logger.handlers:
        return logger

    formatter = logging.Formatter(config.LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_dir = Path(config.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器
    """
    return logging.getLogger(name)
