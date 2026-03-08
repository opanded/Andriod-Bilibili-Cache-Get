"""视频管理模块"""
import logging
from typing import List, Optional
from datetime import datetime

from ..interfaces import IEventPublisher, IVideoService, DownloadStatus
from ..models.video import Video
from ..models.database import Database, VideoModel
from ..services.adb_service import ADBService
from ..services.cache_parser import CacheParser
from .device_manager import DeviceManager

logger = logging.getLogger(__name__)


class VideoManager(IVideoService):
    """视频管理核心类 - 实现 IVideoService 接口"""

    def __init__(self, config, device_manager: DeviceManager,
                 adb_service: ADBService, event_publisher: IEventPublisher, db: Database):
        self.config = config
        self.device_manager = device_manager
        self.adb_service = adb_service
        self.event_publisher = event_publisher
        self.db = db

        self.cache_parser = CacheParser(adb_service, config.BILI_CACHE_PATH)
        self._current_device_id: Optional[str] = None
        self._current_videos: List[Video] = []

    def select_device(self, device_id: str) -> bool:
        """选择设备并加载视频列表"""
        if not self.device_manager.verify_connection(device_id):
            logger.error(f"设备连接无效: {device_id}")
            return False

        if not self.device_manager.check_bilibili_installed(device_id):
            logger.error(f"设备未安装B站: {device_id}")
            return False

        self._current_device_id = device_id
        self.refresh_videos()

        return True

    def refresh_videos(self) -> List[Video]:
        """刷新当前设备的视频列表"""
        if not self._current_device_id:
            logger.warning("未选择设备")
            return []

        try:
            with self.db.session() as session:
                videos = self.cache_parser.get_cached_videos(self._current_device_id, session)

                for video in videos:
                    saved_video = VideoModel.get_by_video_and_device(
                        session, video.video_id, video.device_id
                    )
                    if saved_video:
                        video.download_status = saved_video.download_status
                        video.local_path = saved_video.local_path
                        video.download_time = saved_video.download_time

            self._current_videos = videos

            self.event_publisher.publish('video.list_updated', videos)

            logger.info(f"加载了 {len(videos)} 个视频")
            return videos

        except Exception as e:
            logger.error(f"刷新视频列表失败: {e}")
            return []

    def get_videos(self, device_id: str) -> List[Video]:
        """获取设备的视频列表"""
        if device_id != self._current_device_id:
            self._current_device_id = device_id
            return self.refresh_videos()
        return self._current_videos.copy()

    def get_current_videos(self) -> List[Video]:
        """获取当前视频列表"""
        return self._current_videos.copy()

    def get_video(self, video_id: str) -> Optional[Video]:
        """获取指定视频"""
        for video in self._current_videos:
            if video.video_id == video_id:
                return video
        return None

    def check_cache_integrity(self, video: Video) -> bool:
        """检查视频缓存完整性"""
        return self.cache_parser.check_cache_integrity(
            video.device_id, video
        )

    def update_download_status(self, video_id: str, device_id: str,
                               status: str, local_path: Optional[str] = None):
        """更新视频下载状态"""
        for video in self._current_videos:
            if video.video_id == video_id and video.device_id == device_id:
                video.download_status = status
                if local_path:
                    video.local_path = local_path
                if status == DownloadStatus.COMPLETED.value:
                    video.download_time = datetime.now()
                break

        with self.db.session() as session:
            VideoModel.update_download_status(
                session, video_id, device_id, status, local_path
            )

    def get_videos_by_status(self, status: str) -> List[Video]:
        """按状态获取视频"""
        return [v for v in self._current_videos if v.download_status == status]

    def get_pending_videos(self) -> List[Video]:
        """获取未下载的视频"""
        return self.get_videos_by_status(DownloadStatus.NOT_DOWNLOADED.value)

    def get_downloaded_videos(self) -> List[Video]:
        """获取已下载的视频"""
        return self.get_videos_by_status(DownloadStatus.COMPLETED.value)

    def clear_current_device(self):
        """清除当前设备选择"""
        self._current_device_id = None
        self._current_videos = []
        self.event_publisher.publish('video.list_updated', [])
