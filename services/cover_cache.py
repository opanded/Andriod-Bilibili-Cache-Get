"""封面缓存服务模块"""
import os
import logging
import urllib.request
import urllib.error
import socket
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Optional, Any, Tuple

from ..interfaces.services import ICacheService

logger = logging.getLogger(__name__)


class LRUCache:
    """线程安全的LRU缓存实现"""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache: OrderedDict[str, Tuple[bytes, str]] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Tuple[bytes, str]]:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._hits += 1
                return self._cache[key]
            self._misses += 1
            return None

    def put(self, key: str, data: bytes, ext: str = '.jpg') -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key] = (data, ext)
            else:
                if len(self._cache) >= self.max_size:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    logger.debug(f"LRU缓存淘汰: {oldest_key}")
                self._cache[key] = (data, ext)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> dict:
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            total_size = sum(len(data) for data, _ in self._cache.values())
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'memory_bytes': total_size,
                'memory_mb': total_size / (1024 * 1024)
            }


class CoverCacheService(ICacheService):
    """封面缓存服务"""

    def __init__(self, cache_dir: Path, default_cover_path: Optional[Path] = None, lru_max_size: int = 100):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_cover_path = default_cover_path
        self._lru_cache = LRUCache(max_size=lru_max_size)
        self._memory_cache_dir = cache_dir / 'memory_cache'
        self._memory_cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cached_cover(self, video_id: str) -> Optional[Path]:
        """获取已缓存的封面"""
        for ext in ['.jpg', '.png', '.webp']:
            cached = self.cache_dir / f"{video_id}{ext}"
            if cached.exists():
                return cached
        return None

    def download_cover(self, video_id: str, cover_url: str) -> Optional[Path]:
        """下载并缓存封面

        Args:
            video_id: 视频ID
            cover_url: 封面URL

        Returns:
            本地封面路径
        """
        if not cover_url:
            return self._get_default_cover()

        cached = self.get_cached_cover(video_id)
        if cached:
            self._load_to_lru(video_id, cached)
            return cached

        lru_data = self._lru_cache.get(video_id)
        if lru_data:
            data, ext = lru_data
            local_path = self._save_from_lru(video_id, data, ext)
            if local_path:
                return local_path

        local_path = self.cache_dir / f"{video_id}.jpg"

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0',
                'Referer': 'https://www.bilibili.com'
            }

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    request = urllib.request.Request(cover_url, headers=headers)

                    with urllib.request.urlopen(request, timeout=15) as response:
                        data = response.read()
                        with open(local_path, 'wb') as f:
                            f.write(data)
                        self._lru_cache.put(video_id, data, '.jpg')

                    logger.debug(f"封面下载成功: {video_id}")
                    return local_path

                except (urllib.error.URLError, socket.gaierror, socket.timeout) as e:
                    if attempt < max_retries - 1:
                        logger.debug(f"下载封面重试 {attempt + 1}/{max_retries}: {e}")
                        continue
                    raise

        except Exception as e:
            logger.warning(f"下载封面失败: {video_id}, {e}")
            return self._get_default_cover()

    def _load_to_lru(self, video_id: str, file_path: Path) -> None:
        """将磁盘缓存加载到LRU缓存"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            ext = file_path.suffix
            self._lru_cache.put(video_id, data, ext)
        except Exception as e:
            logger.debug(f"加载封面到LRU缓存失败: {video_id}, {e}")

    def _save_from_lru(self, video_id: str, data: bytes, ext: str) -> Optional[Path]:
        """从LRU缓存保存到磁盘"""
        try:
            local_path = self.cache_dir / f"{video_id}{ext}"
            with open(local_path, 'wb') as f:
                f.write(data)
            return local_path
        except Exception as e:
            logger.warning(f"从LRU缓存保存封面失败: {video_id}, {e}")
            return None

    def _get_default_cover(self) -> Optional[Path]:
        """获取默认封面"""
        if self.default_cover_path and self.default_cover_path.exists():
            return self.default_cover_path
        return None

    def get_lru_stats(self) -> dict:
        """获取LRU缓存统计信息

        Returns:
            包含缓存统计信息的字典
        """
        return self._lru_cache.get_stats()

    def clear_lru_cache(self) -> None:
        """清理LRU内存缓存"""
        self._lru_cache.clear()
        logger.info("LRU内存缓存已清空")

    def clear_cache(self, max_age_days: int = 30, clear_lru: bool = True) -> int:
        """清理过期缓存

        Args:
            max_age_days: 最大保留天数
            clear_lru: 是否同时清理LRU内存缓存

        Returns:
            清理的文件数量
        """
        import time
        count = 0
        cutoff = time.time() - max_age_days * 86400

        for file in self.cache_dir.iterdir():
            if file.is_file() and file.stat().st_mtime < cutoff:
                try:
                    file.unlink()
                    count += 1
                except Exception as e:
                    logger.warning(f"清理缓存文件失败: {file}, {e}")

        if clear_lru:
            self.clear_lru_cache()

        return count
