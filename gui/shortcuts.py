"""快捷键管理模块"""
from typing import Dict, Callable, Optional, List, Tuple
from threading import Lock
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QObject, pyqtSignal


class ShortcutInfo:
    """快捷键信息"""
    
    def __init__(self, key_sequence: str, description: str, callback: Callable, 
                 shortcut: Optional[QShortcut] = None):
        self.key_sequence = key_sequence
        self.description = description
        self.callback = callback
        self.shortcut = shortcut
        self.enabled = True


class ShortcutManager(QObject):
    """快捷键管理器 - 线程安全"""
    
    shortcut_triggered = pyqtSignal(str)
    
    DEFAULT_SHORTCUTS = {
        'refresh_devices': ('Ctrl+R', '刷新设备列表'),
        'search_video': ('Ctrl+F', '搜索视频'),
        'select_all': ('Ctrl+A', '全选视频'),
        'download_selected': ('Ctrl+D', '下载选中视频'),
        'open_settings': ('Ctrl+,', '打开设置'),
        'refresh_videos': ('F5', '刷新视频列表'),
        'delete_selected': ('Delete', '删除选中'),
        'show_help': ('F1', '显示快捷键说明'),
    }
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._parent = parent
        self._shortcuts: Dict[str, ShortcutInfo] = {}
        self._lock = Lock()
        self._registered = False
    
    def register(self, action_id: str, key_sequence: str, 
                 description: str, callback: Callable) -> bool:
        """注册快捷键
        
        Args:
            action_id: 动作唯一标识
            key_sequence: 快捷键序列 (如 'Ctrl+S')
            description: 快捷键描述
            callback: 触发时的回调函数
            
        Returns:
            是否注册成功
        """
        with self._lock:
            if action_id in self._shortcuts:
                return False
            
            try:
                shortcut = None
                if self._parent and self._registered:
                    shortcut = self._create_shortcut(key_sequence, callback)
                
                self._shortcuts[action_id] = ShortcutInfo(
                    key_sequence=key_sequence,
                    description=description,
                    callback=callback,
                    shortcut=shortcut
                )
                return True
            except Exception:
                return False
    
    def unregister(self, action_id: str) -> bool:
        """注销快捷键
        
        Args:
            action_id: 动作唯一标识
            
        Returns:
            是否注销成功
        """
        with self._lock:
            if action_id not in self._shortcuts:
                return False
            
            info = self._shortcuts[action_id]
            if info.shortcut:
                info.shortcut.setEnabled(False)
                info.shortcut.deleteLater()
            
            del self._shortcuts[action_id]
            return True
    
    def update_key_sequence(self, action_id: str, new_key_sequence: str) -> bool:
        """更新快捷键序列
        
        Args:
            action_id: 动作唯一标识
            new_key_sequence: 新的快捷键序列
            
        Returns:
            是否更新成功
        """
        with self._lock:
            if action_id not in self._shortcuts:
                return False
            
            info = self._shortcuts[action_id]
            
            if info.shortcut:
                info.shortcut.setEnabled(False)
                info.shortcut.deleteLater()
            
            try:
                shortcut = None
                if self._parent and self._registered:
                    shortcut = self._create_shortcut(new_key_sequence, info.callback)
                
                info.key_sequence = new_key_sequence
                info.shortcut = shortcut
                return True
            except Exception:
                return False
    
    def set_enabled(self, action_id: str, enabled: bool) -> bool:
        """设置快捷键启用状态
        
        Args:
            action_id: 动作唯一标识
            enabled: 是否启用
            
        Returns:
            是否设置成功
        """
        with self._lock:
            if action_id not in self._shortcuts:
                return False
            
            info = self._shortcuts[action_id]
            info.enabled = enabled
            
            if info.shortcut:
                info.shortcut.setEnabled(enabled)
            
            return True
    
    def set_all_enabled(self, enabled: bool):
        """设置所有快捷键启用状态
        
        Args:
            enabled: 是否启用
        """
        with self._lock:
            for info in self._shortcuts.values():
                info.enabled = enabled
                if info.shortcut:
                    info.shortcut.setEnabled(enabled)
    
    def get_shortcut_info(self, action_id: str) -> Optional[ShortcutInfo]:
        """获取快捷键信息
        
        Args:
            action_id: 动作唯一标识
            
        Returns:
            快捷键信息，不存在返回None
        """
        with self._lock:
            return self._shortcuts.get(action_id)
    
    def get_all_shortcuts(self) -> Dict[str, ShortcutInfo]:
        """获取所有快捷键信息
        
        Returns:
            快捷键字典
        """
        with self._lock:
            return dict(self._shortcuts)
    
    def get_shortcuts_list(self) -> List[Tuple[str, str, str]]:
        """获取快捷键列表
        
        Returns:
            列表，每项为 (action_id, key_sequence, description)
        """
        with self._lock:
            return [
                (action_id, info.key_sequence, info.description)
                for action_id, info in self._shortcuts.items()
            ]
    
    def register_all(self, parent: QWidget, callbacks: Dict[str, Callable]) -> int:
        """批量注册所有默认快捷键
        
        Args:
            parent: 父窗口
            callbacks: 回调函数字典 {action_id: callback}
            
        Returns:
            成功注册的数量
        """
        with self._lock:
            self._parent = parent
            self._registered = True
            
            success_count = 0
            
            for action_id, (key_sequence, description) in self.DEFAULT_SHORTCUTS.items():
                callback = callbacks.get(action_id)
                if callback is None:
                    continue
                
                try:
                    shortcut = self._create_shortcut(key_sequence, callback)
                    
                    self._shortcuts[action_id] = ShortcutInfo(
                        key_sequence=key_sequence,
                        description=description,
                        callback=callback,
                        shortcut=shortcut
                    )
                    success_count += 1
                except Exception:
                    pass
            
            return success_count
    
    def _create_shortcut(self, key_sequence: str, callback: Callable) -> QShortcut:
        """创建快捷键对象
        
        Args:
            key_sequence: 快捷键序列
            callback: 回调函数
            
        Returns:
            QShortcut对象
        """
        shortcut = QShortcut(QKeySequence(key_sequence), self._parent)
        shortcut.activated.connect(callback)
        return shortcut
    
    def clear(self):
        """清除所有快捷键"""
        with self._lock:
            for info in self._shortcuts.values():
                if info.shortcut:
                    info.shortcut.setEnabled(False)
                    info.shortcut.deleteLater()
            
            self._shortcuts.clear()
    
    def get_conflicts(self, key_sequence: str) -> List[str]:
        """检查快捷键冲突
        
        Args:
            key_sequence: 要检查的快捷键序列
            
        Returns:
            冲突的action_id列表
        """
        conflicts = []
        normalized = QKeySequence(key_sequence).toString()
        
        with self._lock:
            for action_id, info in self._shortcuts.items():
                if QKeySequence(info.key_sequence).toString() == normalized:
                    conflicts.append(action_id)
        
        return conflicts
    
    def export_config(self) -> Dict[str, str]:
        """导出快捷键配置
        
        Returns:
            配置字典 {action_id: key_sequence}
        """
        with self._lock:
            return {
                action_id: info.key_sequence
                for action_id, info in self._shortcuts.items()
            }
    
    def import_config(self, config: Dict[str, str]) -> int:
        """导入快捷键配置
        
        Args:
            config: 配置字典 {action_id: key_sequence}
            
        Returns:
            成功更新的数量
        """
        success_count = 0
        
        for action_id, key_sequence in config.items():
            if self.update_key_sequence(action_id, key_sequence):
                success_count += 1
        
        return success_count
