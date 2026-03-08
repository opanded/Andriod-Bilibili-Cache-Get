from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional
from datetime import datetime


class EventType(Enum):
    """事件类型枚举"""
    
    # 设备事件
    DEVICE_LIST_UPDATED = auto()
    DEVICE_CONNECTED = auto()
    DEVICE_DISCONNECTED = auto()
    DEVICE_BILIBILI_STATUS = auto()
    
    # 视频事件
    VIDEO_LIST_UPDATED = auto()
    VIDEO_LOAD_PROGRESS = auto()
    VIDEO_LOAD_ERROR = auto()
    
    # 下载事件
    DOWNLOAD_QUEUED = auto()
    DOWNLOAD_STARTED = auto()
    DOWNLOAD_PROGRESS = auto()
    DOWNLOAD_COMPLETED = auto()
    DOWNLOAD_ERROR = auto()
    DOWNLOAD_PAUSED = auto()
    DOWNLOAD_RESUMED = auto()
    DOWNLOAD_CANCELLED = auto()
    
    # 封面事件
    COVER_LOADED = auto()
    COVER_FAILED = auto()


@dataclass
class Event:
    """事件数据类"""
    event_type: EventType
    data: Any
    timestamp: datetime = None
    source: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class DeviceEvent(Event):
    """设备事件数据"""
    device_id: str = None
    device_name: str = None


@dataclass
class DownloadProgressEvent(Event):
    """下载进度事件数据"""
    task_id: str = None
    video_id: str = None
    progress: float = 0.0
    speed: str = ""
    status: str = ""


@dataclass
class VideoStatusEvent(Event):
    """视频状态事件数据"""
    video_id: str = None
    status: str = None
    local_path: str = None
    progress: float = 0.0
