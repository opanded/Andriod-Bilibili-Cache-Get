"""视频数据模型"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

from ..interfaces import DownloadStatus


@dataclass
class Video:
    """视频数据类"""
    video_id: str
    device_id: str
    bvid: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    cover_path: Optional[str] = None
    duration: int = 0
    file_size: int = 0
    video_quality: int = 0
    video_quality_text: Optional[str] = None
    episode_number: int = 1
    total_episodes: int = 1
    upload_time: Optional[datetime] = None
    cache_path: Optional[str] = None
    cache_video_path: Optional[str] = None
    cache_audio_path: Optional[str] = None
    cache_info_path: Optional[str] = None
    download_status: str = field(default=DownloadStatus.NOT_DOWNLOADED.value)
    local_path: Optional[str] = None
    all_local_paths: Optional[List[str]] = None
    download_time: Optional[datetime] = None

    @property
    def is_downloaded(self) -> bool:
        return self.download_status == DownloadStatus.COMPLETED.value

    @property
    def is_downloading(self) -> bool:
        return self.download_status in [
            DownloadStatus.DOWNLOADING.value,
            DownloadStatus.QUEUED.value
        ]

    @property
    def is_multi_episode(self) -> bool:
        return self.total_episodes > 1

    @property
    def display_title(self) -> str:
        if self.title:
            return self.title
        return f"视频_{self.video_id}"

    @property
    def display_owner(self) -> str:
        if self.owner_name:
            return self.owner_name
        return "未知UP主"

    @property
    def display_quality(self) -> str:
        if self.video_quality_text:
            return self.video_quality_text
        if self.video_quality:
            return f"清晰度{self.video_quality}"
        return "未知"
