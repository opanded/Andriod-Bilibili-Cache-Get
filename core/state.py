"""统一状态管理模块 - 单一数据源原则"""
from typing import Dict, Any, Callable, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from threading import Lock
import logging
import weakref
from datetime import datetime


class StateKey(Enum):
    """状态键枚举"""
    CURRENT_DEVICE = auto()
    DEVICES = auto()
    VIDEOS = auto()
    SELECTED_VIDEOS = auto()
    DOWNLOAD_TASKS = auto()
    DOWNLOAD_PROGRESS = auto()
    SEARCH_FILTER = auto()
    DOWNLOAD_DIR = auto()


@dataclass
class DownloadTaskState:
    """下载任务状态"""
    task_id: str
    video_id: str
    video_title: str
    status: str
    progress: float = 0.0
    local_path: Optional[str] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class State:
    """应用状态 - 单一数据源"""
    current_device: Optional[Dict] = None
    devices: List[Dict] = field(default_factory=list)
    videos: List[Any] = field(default_factory=list)
    selected_videos: Set[str] = field(default_factory=set)
    download_tasks: Dict[str, DownloadTaskState] = field(default_factory=dict)
    download_progress: Dict[str, float] = field(default_factory=dict)
    search_filter: str = ""
    download_dir: str = ""
    
    def get_video_by_id(self, video_id: str) -> Optional[Any]:
        """根据ID获取视频"""
        for video in self.videos:
            if hasattr(video, 'video_id') and video.video_id == video_id:
                return video
        return None
    
    def get_device_by_id(self, device_id: str) -> Optional[Dict]:
        """根据ID获取设备"""
        for device in self.devices:
            if isinstance(device, dict):
                if device.get('device_id') == device_id or device.get('device_id') == device_id:
                    return device
            elif hasattr(device, 'device_id'):
                if device.device_id == device_id:
                    return device
        return None


class StateManager:
    """状态管理器 - 单例模式，线程安全"""
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._state = State()
                    cls._instance._listeners: Dict[StateKey, List[weakref.ref]] = {}
                    cls._instance._state_lock = Lock()
                    cls._instance._logger = logging.getLogger('StateManager')
                    cls._instance._batch_mode = False
                    cls._instance._pending_notifications: Set[StateKey] = set()
        return cls._instance
    
    def get(self, key: StateKey) -> Any:
        """获取状态值"""
        with self._state_lock:
            return getattr(self._state, key.name.lower(), None)
    
    def set(self, key: StateKey, value: Any, silent: bool = False) -> None:
        """设置状态值并通知订阅者
        
        Args:
            key: 状态键
            value: 新值
            silent: 是否静默更新（不触发通知）
        """
        with self._state_lock:
            setattr(self._state, key.name.lower(), value)
        
        if not silent:
            if self._batch_mode:
                self._pending_notifications.add(key)
            else:
                self.notify(key)
    
    def update(self, key: StateKey, updater: Callable[[Any], Any], silent: bool = False) -> None:
        """使用更新函数更新状态
        
        Args:
            key: 状态键
            updater: 更新函数，接收当前值，返回新值
            silent: 是否静默更新
        """
        with self._state_lock:
            current_value = getattr(self._state, key.name.lower(), None)
            new_value = updater(current_value)
            setattr(self._state, key.name.lower(), new_value)
        
        if not silent:
            if self._batch_mode:
                self._pending_notifications.add(key)
            else:
                self.notify(key)
    
    def batch_update(self, updates: Dict[StateKey, Any]) -> None:
        """批量更新状态，只触发一次通知
        
        Args:
            updates: 状态键值对字典
        """
        self.begin_batch()
        try:
            for key, value in updates.items():
                with self._state_lock:
                    setattr(self._state, key.name.lower(), value)
                self._pending_notifications.add(key)
        finally:
            self.end_batch()
    
    def begin_batch(self) -> None:
        """开始批量更新模式"""
        self._batch_mode = True
        self._pending_notifications.clear()
    
    def end_batch(self) -> None:
        """结束批量更新模式，触发所有待处理的通知"""
        self._batch_mode = False
        pending = self._pending_notifications.copy()
        self._pending_notifications.clear()
        
        for key in pending:
            self.notify(key)
    
    def subscribe(self, key: StateKey, callback: Callable[[StateKey, Any], None]) -> None:
        """订阅状态变更
        
        Args:
            key: 状态键
            callback: 回调函数，接收 (key, new_value) 参数
        """
        if key not in self._listeners:
            self._listeners[key] = []
        
        weak_callback = weakref.ref(callback)
        self._listeners[key].append(weak_callback)
    
    def subscribe_strong(self, key: StateKey, callback: Callable[[StateKey, Any], None]) -> None:
        """强引用订阅（用于需要长期持有的情况）
        
        注意：使用强引用时，订阅者需要手动取消订阅以避免内存泄漏
        """
        if key not in self._listeners:
            self._listeners[key] = []
        
        class StrongRef:
            def __init__(self, cb):
                self.callback = cb
            def __call__(self):
                return self.callback
        
        strong_ref = StrongRef(callback)
        strong_ref.is_strong = True
        self._listeners[key].append(strong_ref)
    
    def unsubscribe(self, key: StateKey, callback: Callable) -> None:
        """取消订阅"""
        if key not in self._listeners:
            return
        
        self._listeners[key] = [
            ref for ref in self._listeners[key]
            if not (isinstance(ref, weakref.ref) and ref() == callback)
        ]
    
    def notify(self, key: StateKey) -> None:
        """通知所有订阅者"""
        if key not in self._listeners:
            return
        
        value = self.get(key)
        
        dead_refs = []
        for ref in self._listeners[key]:
            if isinstance(ref, weakref.ref):
                callback = ref()
                if callback is None:
                    dead_refs.append(ref)
                    continue
            else:
                callback = ref.callback if hasattr(ref, 'callback') else ref
            
            try:
                callback(key, value)
            except Exception as e:
                self._logger.error(f"状态变更回调执行失败 [{key.name}]: {e}")
        
        for ref in dead_refs:
            self._listeners[key].remove(ref)
    
    def get_state(self) -> State:
        """获取完整状态对象（只读访问）"""
        return self._state
    
    def get_video_by_id(self, video_id: str) -> Optional[Any]:
        """根据ID获取视频"""
        return self._state.get_video_by_id(video_id)
    
    def get_device_by_id(self, device_id: str) -> Optional[Dict]:
        """根据ID获取设备"""
        return self._state.get_device_by_id(device_id)
    
    def add_video_to_selection(self, video_id: str) -> None:
        """添加视频到选中列表"""
        self.update(StateKey.SELECTED_VIDEOS, lambda s: s | {video_id})
    
    def remove_video_from_selection(self, video_id: str) -> None:
        """从选中列表移除视频"""
        self.update(StateKey.SELECTED_VIDEOS, lambda s: s - {video_id})
    
    def clear_video_selection(self) -> None:
        """清空视频选中列表"""
        self.set(StateKey.SELECTED_VIDEOS, set())
    
    def add_download_task(self, task: DownloadTaskState) -> None:
        """添加下载任务"""
        def add_task(tasks):
            new_tasks = dict(tasks)
            new_tasks[task.task_id] = task
            return new_tasks
        
        self.update(StateKey.DOWNLOAD_TASKS, add_task)
    
    def update_download_task(self, task_id: str, **kwargs) -> None:
        """更新下载任务"""
        def update_task(tasks):
            new_tasks = dict(tasks)
            if task_id in new_tasks:
                task = new_tasks[task_id]
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
            return new_tasks
        
        self.update(StateKey.DOWNLOAD_TASKS, update_task)
    
    def remove_download_task(self, task_id: str) -> None:
        """移除下载任务"""
        def remove_task(tasks):
            new_tasks = dict(tasks)
            if task_id in new_tasks:
                del new_tasks[task_id]
            return new_tasks
        
        self.update(StateKey.DOWNLOAD_TASKS, remove_task)
    
    def update_download_progress(self, video_id: str, progress: float) -> None:
        """更新下载进度"""
        def update_progress(progress_dict):
            new_dict = dict(progress_dict)
            new_dict[video_id] = progress
            return new_dict
        
        self.update(StateKey.DOWNLOAD_PROGRESS, update_progress)
    
    @classmethod
    def reset(cls):
        """重置状态管理器（用于测试）"""
        with cls._lock:
            cls._instance = None
    
    @classmethod
    def get_instance(cls) -> 'StateManager':
        """获取单例实例"""
        if cls._instance is None:
            return cls()
        return cls._instance


class StateSubscriber:
    """状态订阅者基类 - 提供便捷的订阅管理"""
    
    def __init__(self):
        self._subscriptions: List[tuple] = []
    
    def subscribe_state(self, key: StateKey, callback: Callable) -> None:
        """订阅状态并记录订阅关系"""
        StateManager.get_instance().subscribe(key, callback)
        self._subscriptions.append((key, callback))
    
    def unsubscribe_all(self) -> None:
        """取消所有订阅"""
        state_manager = StateManager.get_instance()
        for key, callback in self._subscriptions:
            state_manager.unsubscribe(key, callback)
        self._subscriptions.clear()


def state_property(key: StateKey):
    """状态属性装饰器 - 提供便捷的状态访问
    
    用法:
        class MyComponent:
            @state_property(StateKey.CURRENT_DEVICE)
            def current_device(self, value):
                # 当 current_device 状态变更时自动调用
                self.update_ui(value)
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            StateManager.get_instance().subscribe(key, lambda k, v: func(self, v))
            return func(self, *args, **kwargs)
        return wrapper
    return decorator
