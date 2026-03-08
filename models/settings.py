"""用户设置数据模型"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class UserSettings:
    """用户设置数据类"""
    download_dir: str = ""
    theme: str = "dark"
    language: str = "zh_CN"
    auto_refresh: bool = False
    refresh_interval: int = 30
    max_concurrent_downloads: int = 3
    enable_notification: bool = True
    window_geometry: Optional[str] = None
    window_state: Optional[str] = None
    show_welcome: bool = True
    
    show_mascot: bool = True
    mascot_type: str = "rabbit_frog"
    mascot_position: str = "bottom_right"
    mascot_size: str = "medium"
    enable_animations: bool = True
    enable_achievements: bool = True
    mascot_animation_speed: float = 1.0
    mascot_idle_actions: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'download_dir': self.download_dir,
            'theme': self.theme,
            'language': self.language,
            'auto_refresh': self.auto_refresh,
            'refresh_interval': self.refresh_interval,
            'max_concurrent_downloads': self.max_concurrent_downloads,
            'enable_notification': self.enable_notification,
            'window_geometry': self.window_geometry,
            'window_state': self.window_state,
            'show_welcome': self.show_welcome,
            'show_mascot': self.show_mascot,
            'mascot_type': self.mascot_type,
            'mascot_position': self.mascot_position,
            'mascot_size': self.mascot_size,
            'enable_animations': self.enable_animations,
            'enable_achievements': self.enable_achievements,
            'mascot_animation_speed': self.mascot_animation_speed,
            'mascot_idle_actions': self.mascot_idle_actions,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSettings':
        """从字典创建实例"""
        if not data:
            return cls()
        
        return cls(
            download_dir=data.get('download_dir', ''),
            theme=data.get('theme', 'dark'),
            language=data.get('language', 'zh_CN'),
            auto_refresh=data.get('auto_refresh', True),
            refresh_interval=data.get('refresh_interval', 30),
            max_concurrent_downloads=data.get('max_concurrent_downloads', 3),
            enable_notification=data.get('enable_notification', True),
            window_geometry=data.get('window_geometry'),
            window_state=data.get('window_state'),
            show_welcome=data.get('show_welcome', True),
            show_mascot=data.get('show_mascot', True),
            mascot_type=data.get('mascot_type', 'rabbit_frog'),
            mascot_position=data.get('mascot_position', 'bottom_right'),
            mascot_size=data.get('mascot_size', 'medium'),
            enable_animations=data.get('enable_animations', True),
            enable_achievements=data.get('enable_achievements', True),
            mascot_animation_speed=data.get('mascot_animation_speed', 1.0),
            mascot_idle_actions=data.get('mascot_idle_actions', True),
        )
    
    def validate(self) -> bool:
        """验证设置的有效性"""
        if self.download_dir and not Path(self.download_dir).exists():
            logger.warning(f"下载目录不存在: {self.download_dir}")
            self.download_dir = ""
        
        if self.refresh_interval < 10:
            self.refresh_interval = 10
        elif self.refresh_interval > 300:
            self.refresh_interval = 300
        
        if self.max_concurrent_downloads < 1:
            self.max_concurrent_downloads = 1
        elif self.max_concurrent_downloads > 10:
            self.max_concurrent_downloads = 10
        
        if self.theme not in ['dark', 'light', 'cute']:
            self.theme = 'dark'
        
        if self.mascot_type not in ['rabbit_frog', 'donut', 'both']:
            self.mascot_type = 'rabbit_frog'
        
        if self.mascot_position not in ['bottom_right', 'bottom_left', 'top_right', 'top_left']:
            self.mascot_position = 'bottom_right'
        
        if self.mascot_size not in ['small', 'medium', 'large']:
            self.mascot_size = 'medium'
        
        if self.mascot_animation_speed < 0.5:
            self.mascot_animation_speed = 0.5
        elif self.mascot_animation_speed > 2.0:
            self.mascot_animation_speed = 2.0
        
        return True
