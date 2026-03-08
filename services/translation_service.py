import sys
import json
from pathlib import Path
from typing import Dict, Optional


def _get_locales_dir() -> Path:
    """获取翻译文件目录"""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / 'locales'
    else:
        return Path(__file__).parent.parent.parent / 'locales'


class TranslationService:
    """多语言翻译服务"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._translations: Dict[str, str] = {}
            cls._instance._current_language = 'zh_CN'
        return cls._instance
    
    def load_language(self, language: str) -> bool:
        """加载语言文件"""
        lang_file = _get_locales_dir() / f'{language}.json'
        
        if not lang_file.exists():
            return False
        
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self._translations = json.load(f)
            self._current_language = language
            return True
        except Exception as e:
            print(f"加载语言文件失败: {e}")
            return False
    
    def tr(self, key: str, default: str = None) -> str:
        """翻译文本"""
        if default is None:
            default = key
        return self._translations.get(key, default)
    
    def get_current_language(self) -> str:
        """获取当前语言"""
        return self._current_language
    
    def get_available_languages(self) -> list:
        """获取可用语言列表"""
        locales_dir = _get_locales_dir()
        if not locales_dir.exists():
            return ['zh_CN']
        
        languages = []
        for f in locales_dir.glob('*.json'):
            languages.append(f.stem)
        
        return languages if languages else ['zh_CN']
    
    @classmethod
    def reset(cls):
        """重置实例（用于测试）"""
        cls._instance = None
