"""国际化翻译模块"""
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


class TranslationManager:
    """翻译管理器"""
    
    _instance: Optional['TranslationManager'] = None
    _translations: Dict[str, str] = {}
    _current_language: str = "zh_CN"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'TranslationManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def load_language(self, language: str) -> bool:
        """加载语言文件"""
        self._current_language = language
        translations_dir = _get_locales_dir()
        
        if language == "zh_CN":
            self._translations = {}
            return True
        
        translation_file = translations_dir / f"{language}.json"
        if translation_file.exists():
            try:
                with open(translation_file, 'r', encoding='utf-8') as f:
                    self._translations = json.load(f)
                return True
            except Exception as e:
                print(f"加载翻译文件失败: {e}")
                self._translations = {}
                return False
        else:
            self._translations = {}
            return False
    
    def tr(self, text: str) -> str:
        """翻译文本"""
        if not self._translations:
            return text
        return self._translations.get(text, text)
    
    def get_current_language(self) -> str:
        """获取当前语言"""
        return self._current_language


def tr(text: str) -> str:
    """全局翻译函数"""
    return TranslationManager.get_instance().tr(text)
