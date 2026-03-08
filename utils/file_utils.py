"""工具函数模块"""
import re
import os
from pathlib import Path
from typing import Optional


def sanitize_filename(title: str, max_length: int = 200) -> str:
    """清理文件名，移除非法字符

    Args:
        title: 原始标题
        max_length: 最大长度

    Returns:
        清理后的文件名
    """
    if not title:
        return "unnamed"

    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        title = title.replace(char, '_')

    title = re.sub(r'[\x00-\x1f]', '', title)

    title = title.strip('. ')

    windows_reserved = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
        'LPT1', 'LPT2', 'LPT3'
    }
    if title.upper() in windows_reserved:
        title = f"_{title}"

    if len(title) > max_length:
        title = title[:max_length].rstrip()

    return title or "unnamed"


def get_unique_filename(directory: Path, filename: str) -> Path:
    """获取唯一的文件名，避免冲突

    Args:
        directory: 目录路径
        filename: 文件名

    Returns:
        唯一的文件路径
    """
    filepath = directory / filename
    if not filepath.exists():
        return filepath

    name, ext = os.path.splitext(filename)
    counter = 1
    while filepath.exists():
        new_filename = f"{name} ({counter}){ext}"
        filepath = directory / new_filename
        counter += 1

    return filepath


def format_file_size(size: int) -> str:
    """格式化文件大小

    Args:
        size: 文件大小（字节）

    Returns:
        格式化后的字符串
    """
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f} GB"


def format_duration(seconds: int) -> str:
    """格式化时长

    Args:
        seconds: 秒数

    Returns:
        格式化后的字符串
    """
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}分{secs}秒" if secs else f"{minutes}分钟"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}小时{minutes}分" if minutes else f"{hours}小时"
