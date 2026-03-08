"""全局配置模块"""
import sys
import os
import shutil
from pathlib import Path


def _get_base_dir():
    """获取应用程序基础目录"""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent.parent


def _get_meipass_dir():
    """获取PyInstaller临时解压目录"""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return None


class Config:
    """全局配置类"""

    BASE_DIR = _get_base_dir()
    DATA_DIR = BASE_DIR / "data"
    ASSETS_DIR = BASE_DIR / "assets"

    DOWNLOAD_DIR = BASE_DIR / "downloads"
    TEMP_DIR = DOWNLOAD_DIR / "temp"
    COVER_CACHE_DIR = BASE_DIR / "data" / "cover_cache"

    MAX_CONCURRENT_DOWNLOADS = 2
    MAX_RETRY_COUNT = 2
    RETRY_INTERVAL = 5
    CHUNK_SIZE = 8192 * 1024

    DEVICE_CHECK_INTERVAL = 30
    MAX_RECONNECT_ATTEMPTS = 3
    RECONNECT_INTERVAL = 10

    MAX_FILENAME_LENGTH = 200
    WINDOWS_RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
        'LPT1', 'LPT2', 'LPT3'
    }
    FILENAME_INVALID_CHARS = r'<>:"/\|?*'

    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = BASE_DIR / "logs" / "bili-cache-get.log"
    LOG_MAX_BYTES = 10 * 1024 * 1024
    LOG_BACKUP_COUNT = 5

    DATABASE_PATH = DATA_DIR / "bili_cache.db"

    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    THEME = "dark"

    BILI_CACHE_PATH = "/sdcard/Android/data/tv.danmaku.bili/download"
    BILI_PACKAGE_NAME = "tv.danmaku.bili"

    COVER_THUMB_WIDTH = 120
    COVER_THUMB_HEIGHT = 68
    COVER_PREVIEW_MAX_WIDTH = 960
    COVER_PREVIEW_MAX_HEIGHT = 720

    MIN_DISK_SPACE_GB = 1

    @classmethod
    def ensure_directories(cls):
        """确保必要的目录存在"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        cls.COVER_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (cls.BASE_DIR / "logs").mkdir(parents=True, exist_ok=True)
        cls.ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def check_disk_space(cls, required_bytes: int = 0) -> tuple:
        """检查磁盘空间

        Returns:
            (is_sufficient, free_space_gb, message)
        """
        try:
            download_path = str(cls.DOWNLOAD_DIR)
            if not os.path.exists(download_path):
                download_path = str(cls.BASE_DIR)

            total, used, free = shutil.disk_usage(download_path)
            free_gb = free / (1024 ** 3)
            min_free_bytes = cls.MIN_DISK_SPACE_GB * (1024 ** 3)

            if required_bytes > 0:
                is_sufficient = free > required_bytes * 1.1
                if not is_sufficient:
                    return (False, free_gb, f"磁盘空间不足，需要 {required_bytes / (1024**2):.1f}MB，剩余 {free_gb:.1f}GB")
            else:
                is_sufficient = free > min_free_bytes

            if not is_sufficient:
                return (False, free_gb, f"磁盘空间不足，剩余 {free_gb:.1f}GB，建议至少保留 {cls.MIN_DISK_SPACE_GB}GB")

            return (True, free_gb, f"磁盘空间充足，剩余 {free_gb:.1f}GB")
        except Exception as e:
            return (True, 0, f"无法检测磁盘空间: {e}")

    @classmethod
    def get_adb_path(cls) -> Path:
        """获取 ADB 工具路径"""
        if getattr(sys, 'frozen', False):
            return Path(sys._MEIPASS) / 'tools' / 'adb' / 'adb.exe'
        else:
            return Path(__file__).parent.parent / 'package' / 'adb' / 'adb.exe'

    @classmethod
    def get_ffmpeg_path(cls) -> Path:
        """获取 FFmpeg 工具路径"""
        if getattr(sys, 'frozen', False):
            return Path(sys._MEIPASS) / 'tools' / 'ffmpeg' / 'ffmpeg.exe'
        else:
            return Path(__file__).parent.parent / 'package' / 'ffmpeg' / 'ffmpeg.exe'
