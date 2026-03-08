"""接口抽象层 - 实现模块间解耦"""
from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from .services import (
    IADBService,
    IVideoMerger,
    ICacheService,
    IDeviceManager,
    IFileTransfer,
)


class DownloadStatus(Enum):
    """下载状态枚举"""
    NOT_DOWNLOADED = "not_downloaded"
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @classmethod
    def get_display_text(cls, status: str) -> str:
        """获取状态显示文本"""
        display_map = {
            cls.NOT_DOWNLOADED.value: "未下载",
            cls.QUEUED.value: "等待中",
            cls.DOWNLOADING.value: "下载中",
            cls.PAUSED.value: "已暂停",
            cls.COMPLETED.value: "已完成",
            cls.FAILED.value: "下载失败",
            cls.CANCELLED.value: "已取消"
        }
        return display_map.get(status, "未知")


class ErrorCategory(Enum):
    """错误分类"""
    RETRYABLE = "retryable"
    USER_ACTION = "user_action"
    FATAL = "fatal"


@dataclass
class DownloadRequest:
    """下载请求"""
    device_id: str
    video_id: str
    video_title: str
    cache_video_path: str
    cache_audio_path: Optional[str]
    cache_info_path: Optional[str]
    local_dir: str
    priority: int = 0


@dataclass
class DownloadTaskInfo:
    """下载任务信息"""
    task_id: str
    status: DownloadStatus
    progress: float
    local_path: Optional[str]
    error_message: Optional[str]
    error_category: Optional[ErrorCategory] = None


class IEventPublisher(ABC):
    """事件发布接口 - Core层通过此接口发布事件，不依赖具体GUI框架"""

    @abstractmethod
    def publish(self, event_type: str, data: Any) -> None:
        """发布事件

        Args:
            event_type: 事件类型，如 'device.connected', 'download.progress'
            data: 事件数据
        """


class IEventSubscriber(ABC):
    """事件订阅接口 - GUI层实现此接口接收事件"""

    @abstractmethod
    def on_event(self, event_type: str, data: Any) -> None:
        """接收事件"""


class IDownloadService(ABC):
    """下载服务接口 - VideoManager通过此接口与FileTransfer交互"""

    @abstractmethod
    def submit_download(self, request: DownloadRequest) -> str:
        """提交下载请求，返回任务ID"""

    @abstractmethod
    def submit_batch(self, requests: List[DownloadRequest]) -> List[str]:
        """批量提交下载请求，返回任务ID列表"""

    @abstractmethod
    def pause_task(self, task_id: str) -> bool:
        """暂停指定任务"""

    @abstractmethod
    def resume_task(self, task_id: str) -> bool:
        """恢复指定任务"""

    @abstractmethod
    def cancel_task(self, task_id: str) -> bool:
        """取消指定任务"""

    @abstractmethod
    def cancel_batch(self, task_ids: List[str]) -> bool:
        """批量取消任务"""

    @abstractmethod
    def get_task_info(self, task_id: str) -> Optional[DownloadTaskInfo]:
        """获取任务详细信息"""

    @abstractmethod
    def get_queue_summary(self) -> Dict:
        """获取队列概览"""

    @abstractmethod
    def get_active_tasks(self) -> List[str]:
        """获取进行中的任务ID列表"""

    @abstractmethod
    def restore_tasks(self) -> None:
        """从数据库恢复未完成的任务（程序启动时调用）"""


class IDeviceService(ABC):
    """设备服务接口"""

    @abstractmethod
    def get_online_devices(self) -> List[Any]:
        """获取在线设备列表"""

    @abstractmethod
    def get_device(self, device_id: str) -> Optional[Any]:
        """获取指定设备"""

    @abstractmethod
    def verify_connection(self, device_id: str) -> bool:
        """验证设备连接是否有效"""

    @abstractmethod
    def check_bilibili_installed(self, device_id: str) -> bool:
        """检查设备是否安装了B站"""


class IVideoService(ABC):
    """视频服务接口"""

    @abstractmethod
    def get_videos(self, device_id: str) -> List[Any]:
        """获取设备的视频列表"""

    @abstractmethod
    def update_download_status(self, video_id: str, device_id: str,
                               status: str, local_path: Optional[str] = None) -> None:
        """更新视频下载状态"""


class DownloadError(Exception):
    """下载错误"""

    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.FATAL):
        self.message = message
        self.category = category
        super().__init__(message)

    @classmethod
    def retryable(cls, message: str) -> 'DownloadError':
        """创建可重试错误"""
        return cls(message, ErrorCategory.RETRYABLE)

    @classmethod
    def user_action(cls, message: str) -> 'DownloadError':
        """创建需要用户介入的错误"""
        return cls(message, ErrorCategory.USER_ACTION)

    @classmethod
    def fatal(cls, message: str) -> 'DownloadError':
        """创建不可恢复错误"""
        return cls(message, ErrorCategory.FATAL)
