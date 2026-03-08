"""服务接口定义模块

定义核心服务接口，实现模块间解耦。
每个接口对应一个具体的服务实现，便于测试和替换。
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from ..models.device import Device
    from . import DownloadRequest


class IADBService(ABC):
    """ADB服务接口
    
    封装Android Debug Bridge操作，提供设备通信能力。
    实现类: ADBService
    """

    @abstractmethod
    def get_devices(self) -> List[Dict[str, str]]:
        """获取已连接的设备列表
        
        Returns:
            设备信息列表，每个元素包含 device_id, status 等字段
        """

    @abstractmethod
    def get_device_info(self, device_id: str) -> Dict[str, str]:
        """获取设备详细信息
        
        Args:
            device_id: 设备标识符
            
        Returns:
            设备信息字典，包含 market_name, model, manufacturer, 
            android_version, serial 等字段
        """

    @abstractmethod
    def check_package_installed(self, device_id: str, package_name: str) -> bool:
        """检查应用包是否已安装
        
        Args:
            device_id: 设备标识符
            package_name: 应用包名
            
        Returns:
            是否已安装
        """

    @abstractmethod
    def pull_file(self, device_id: str, remote_path: str, local_path: str) -> bool:
        """从设备拉取文件到本地
        
        Args:
            device_id: 设备标识符
            remote_path: 设备上的文件路径
            local_path: 本地保存路径
            
        Returns:
            是否成功
        """

    @abstractmethod
    def list_directory(self, device_id: str, remote_path: str) -> List[Dict]:
        """列出设备目录内容
        
        Args:
            device_id: 设备标识符
            remote_path: 设备上的目录路径
            
        Returns:
            目录项列表，每个元素包含 permissions, owner, group, 
            size, date, name 等字段
        """

    @abstractmethod
    def get_file_size(self, device_id: str, remote_path: str) -> int:
        """获取设备上文件的大小
        
        Args:
            device_id: 设备标识符
            remote_path: 设备上的文件路径
            
        Returns:
            文件大小（字节），失败返回 -1
        """

    @abstractmethod
    def connect_wireless(self, ip: str, port: int) -> bool:
        """通过无线方式连接设备
        
        Args:
            ip: 设备IP地址
            port: ADB端口
            
        Returns:
            是否成功
        """

    @abstractmethod
    def disconnect_wireless(self, ip: str, port: int) -> bool:
        """断开无线设备连接
        
        Args:
            ip: 设备IP地址
            port: ADB端口
            
        Returns:
            是否成功
        """

    @abstractmethod
    def pair_wireless(self, ip: str, port: int, code: str) -> bool:
        """使用配对码配对新设备
        
        Args:
            ip: 设备IP地址
            port: 配对端口
            code: 6位配对码
            
        Returns:
            是否成功
        """

    @abstractmethod
    def test_connection(self, device_id: str) -> bool:
        """测试设备连接
        
        Args:
            device_id: 设备标识符
            
        Returns:
            是否连接正常
        """


class IVideoMerger(ABC):
    """视频合并服务接口
    
    提供视频和音频合并功能，依赖FFmpeg。
    实现类: VideoMerger
    """

    @abstractmethod
    def merge(self, video_path: str, audio_path: Optional[str], output_path: str) -> bool:
        """合并视频和音频文件
        
        Args:
            video_path: 视频文件路径
            audio_path: 音频文件路径（可选，为None时仅复制视频）
            output_path: 输出文件路径
            
        Returns:
            是否成功
        """

    @abstractmethod
    def is_available(self) -> bool:
        """检查FFmpeg是否可用
        
        Returns:
            FFmpeg是否可用
        """


class ICacheService(ABC):
    """缓存服务接口
    
    管理封面等资源的缓存。
    实现类: CoverCacheService
    """

    @abstractmethod
    def get_cached_cover(self, video_id: str) -> Optional[Path]:
        """获取已缓存的封面
        
        Args:
            video_id: 视频ID
            
        Returns:
            封面文件路径，未缓存返回None
        """

    @abstractmethod
    def download_cover(self, video_id: str, cover_url: str) -> Optional[Path]:
        """下载并缓存封面
        
        Args:
            video_id: 视频ID
            cover_url: 封面URL
            
        Returns:
            本地封面路径，下载失败返回默认封面或None
        """

    @abstractmethod
    def clear_cache(self, max_age_days: int) -> int:
        """清理过期缓存
        
        Args:
            max_age_days: 最大保留天数
            
        Returns:
            清理的文件数量
        """


class IDeviceManager(ABC):
    """设备管理器接口
    
    管理设备连接状态、监控设备变化。
    实现类: DeviceManager
    """

    @abstractmethod
    def get_online_devices(self) -> List['Device']:
        """获取在线设备列表
        
        Returns:
            在线设备列表
        """

    @abstractmethod
    def refresh_devices(self) -> None:
        """立即刷新设备列表
        
        主动触发设备检查，不等待监控周期。
        """

    @abstractmethod
    def start_monitoring(self) -> None:
        """启动设备监控
        
        开始后台监控线程，定期检查设备连接状态。
        """

    @abstractmethod
    def stop_monitoring(self) -> None:
        """停止设备监控
        
        停止后台监控线程。
        """


class IFileTransfer(ABC):
    """文件传输服务接口
    
    管理下载队列，处理文件传输任务。
    实现类: FileTransfer
    """

    @abstractmethod
    def submit_download(self, request: 'DownloadRequest') -> str:
        """提交下载请求
        
        Args:
            request: 下载请求对象
            
        Returns:
            任务ID
        """

    @abstractmethod
    def cancel_download(self, task_id: str) -> bool:
        """取消下载任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """

    @abstractmethod
    def get_active_downloads(self) -> List[str]:
        """获取进行中的下载任务ID列表
        
        Returns:
            活动任务ID列表
        """
