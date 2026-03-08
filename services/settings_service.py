"""用户设置服务模块"""
import json
import logging
from pathlib import Path
from typing import Optional

from ..models.settings import UserSettings

logger = logging.getLogger(__name__)


class SettingsService:
    """用户设置服务类"""
    
    DEFAULT_SETTINGS_FILE = "user_settings.json"
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = config_dir / self.DEFAULT_SETTINGS_FILE
        self.settings: UserSettings = self._load()
    
    def _load(self) -> UserSettings:
        """加载用户设置"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                settings = UserSettings.from_dict(data)
                settings.validate()
                logger.info(f"已加载用户设置: {self.settings_file}")
                return settings
        except json.JSONDecodeError as e:
            logger.error(f"设置文件格式错误: {e}")
        except Exception as e:
            logger.error(f"加载设置失败: {e}")
        
        logger.info("使用默认设置")
        return UserSettings()
    
    def get(self) -> UserSettings:
        """获取当前设置"""
        return self.settings
    
    def save(self) -> bool:
        """保存用户设置"""
        try:
            self.settings.validate()
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"设置已保存: {self.settings_file}")
            return True
        except Exception as e:
            logger.error(f"保存设置失败: {e}")
            return False
    
    def update(self, **kwargs) -> bool:
        """更新设置"""
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
            else:
                logger.warning(f"未知的设置项: {key}")
        
        return self.save()
    
    def reset(self) -> bool:
        """重置为默认设置"""
        self.settings = UserSettings()
        return self.save()
    
    def get_download_dir(self) -> Optional[str]:
        """获取下载目录"""
        return self.settings.download_dir if self.settings.download_dir else None
    
    def set_download_dir(self, path: str) -> bool:
        """设置下载目录"""
        if Path(path).exists():
            return self.update(download_dir=path)
        logger.warning(f"下载目录不存在: {path}")
        return False
    
    def get_theme(self) -> str:
        """获取主题"""
        return self.settings.theme
    
    def set_theme(self, theme: str) -> bool:
        """设置主题"""
        if theme in ['dark', 'light']:
            return self.update(theme=theme)
        logger.warning(f"未知的主题: {theme}")
        return False
    
    def get_max_concurrent_downloads(self) -> int:
        """获取最大并发下载数"""
        return self.settings.max_concurrent_downloads
    
    def set_max_concurrent_downloads(self, count: int) -> bool:
        """设置最大并发下载数"""
        return self.update(max_concurrent_downloads=count)
    
    def save_window_state(self, geometry: bytes, state: bytes) -> bool:
        """保存窗口状态"""
        import base64
        geometry_str = base64.b64encode(geometry).decode('utf-8') if geometry else None
        state_str = base64.b64encode(state).decode('utf-8') if state else None
        return self.update(window_geometry=geometry_str, window_state=state_str)
    
    def load_window_state(self) -> tuple:
        """加载窗口状态"""
        import base64
        geometry = None
        state = None
        
        if self.settings.window_geometry:
            try:
                geometry = base64.b64decode(self.settings.window_geometry.encode('utf-8'))
            except Exception as e:
                logger.warning(f"解码窗口几何数据失败: {e}")
        
        if self.settings.window_state:
            try:
                state = base64.b64decode(self.settings.window_state.encode('utf-8'))
            except Exception as e:
                logger.warning(f"解码窗口状态数据失败: {e}")
        
        return geometry, state
    
    def is_first_run(self) -> bool:
        """检查是否首次运行"""
        return self.settings.show_welcome
    
    def set_welcome_shown(self, dont_show_again: bool = False) -> bool:
        """设置欢迎对话框已显示
        
        Args:
            dont_show_again: 是否不再显示
            
        Returns:
            是否保存成功
        """
        if dont_show_again:
            return self.update(show_welcome=False)
        return True
