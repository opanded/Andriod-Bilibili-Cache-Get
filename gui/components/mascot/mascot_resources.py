"""吉祥物表情资源管理器"""
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Union

from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QSize, QPoint

from src.gui.utils.sprite_splitter import SpriteSplitter

logger = logging.getLogger(__name__)


class MascotResources:
    """吉祥物表情资源管理器"""
    
    _instance = None
    
    RABBIT_FROG_SPRITE = "🐇🐸4x4表情16个.png"
    DONUT_SPRITE = "圈圈子4x4表情16个.png"
    
    SIZE_MAP = {
        "small": 64,
        "medium": 96,
        "large": 128,
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._resources_dir: Optional[Path] = None
        self._cache_dir: Optional[Path] = None
        
        self._rabbit_frog_expressions: Dict[str, List[QPixmap]] = {}
        self._donut_expressions: Dict[str, List[QPixmap]] = {}
        
        self._expression_index_map = {
            "normal": [0],
            "happy": [1, 2, 7],
            "thinking": [3],
            "sad": [4],
            "working": [5],
            "celebrate": [6],
            "sleep": [8],
            "worried": [9],
            "excited": [10],
            "relax": [11],
            "surprised": [12],
            "confused": [13],
            "love": [14],
            "cool": [15],
        }
    
    def initialize(self, resources_dir: Path = None) -> bool:
        """初始化资源管理器
        
        Args:
            resources_dir: 资源目录路径，默认为项目根目录
            
        Returns:
            是否初始化成功
        """
        if resources_dir is None:
            resources_dir = Path(__file__).parent.parent.parent.parent.parent
        
        self._resources_dir = resources_dir
        self._cache_dir = resources_dir / "resources" / "mascot" / "cache"
        
        logger.info(f"初始化吉祥物资源管理器，资源目录: {self._resources_dir}")
        
        return True
    
    def _get_sprite_path(self, mascot_type: str) -> Optional[Path]:
        """获取精灵图路径
        
        Args:
            mascot_type: 吉祥物类型 ('rabbit_frog' 或 'donut')
            
        Returns:
            精灵图路径
        """
        if mascot_type == "rabbit_frog":
            sprite_name = self.RABBIT_FROG_SPRITE
        elif mascot_type == "donut":
            sprite_name = self.DONUT_SPRITE
        else:
            logger.error(f"未知吉祥物类型: {mascot_type}")
            return None
        
        sprite_path = self._resources_dir / sprite_name
        
        if not sprite_path.exists():
            logger.error(f"精灵图文件不存在: {sprite_path}")
            return None
        
        return sprite_path
    
    def _load_expressions(
        self,
        mascot_type: str,
        size: str
    ) -> Optional[List[QPixmap]]:
        """加载指定类型和尺寸的表情
        
        Args:
            mascot_type: 吉祥物类型
            size: 尺寸 ('small', 'medium', 'large')
            
        Returns:
            表情图片列表
        """
        sprite_path = self._get_sprite_path(mascot_type)
        if sprite_path is None:
            return None
        
        target_size = self.SIZE_MAP.get(size, 96)
        
        expressions = SpriteSplitter.split_and_scale(
            str(sprite_path),
            target_size=target_size,
            smooth=True
        )
        
        if not expressions:
            logger.error(f"加载表情失败: {mascot_type}, 尺寸: {size}")
            return None
        
        return expressions
    
    def get_expressions(
        self,
        mascot_type: str,
        size: str = "medium"
    ) -> Optional[List[QPixmap]]:
        """获取指定类型和尺寸的表情列表
        
        Args:
            mascot_type: 吉祥物类型 ('rabbit_frog' 或 'donut')
            size: 尺寸 ('small', 'medium', 'large')
            
        Returns:
            表情图片列表
        """
        if mascot_type == "rabbit_frog":
            cache = self._rabbit_frog_expressions
        elif mascot_type == "donut":
            cache = self._donut_expressions
        else:
            return None
        
        if size in cache:
            return cache[size]
        
        expressions = self._load_expressions(mascot_type, size)
        if expressions:
            cache[size] = expressions
        
        return expressions
    
    def get_expression(
        self,
        mascot_type: str,
        state: str,
        size: str = "medium",
        random_variant: bool = True
    ) -> Optional[QPixmap]:
        """获取指定状态的表情图片
        
        Args:
            mascot_type: 吉祥物类型
            state: 状态名称
            size: 尺寸
            random_variant: 是否随机选择变体（用于有多种表情的状态）
            
        Returns:
            表情图片
        """
        expressions = self.get_expressions(mascot_type, size)
        if not expressions:
            return None
        
        indices = self._expression_index_map.get(state, [0])
        
        if random_variant and len(indices) > 1:
            index = random.choice(indices)
        else:
            index = indices[0]
        
        if 0 <= index < len(expressions):
            return expressions[index]
        
        return expressions[0] if expressions else None
    
    def get_expression_by_index(
        self,
        mascot_type: str,
        index: int,
        size: str = "medium"
    ) -> Optional[QPixmap]:
        """根据索引获取表情图片
        
        Args:
            mascot_type: 吉祥物类型
            index: 表情索引 (0-15)
            size: 尺寸
            
        Returns:
            表情图片
        """
        expressions = self.get_expressions(mascot_type, size)
        if not expressions:
            return None
        
        if 0 <= index < len(expressions):
            return expressions[index]
        
        return expressions[0] if expressions else None
    
    def get_available_states(self) -> List[str]:
        """获取所有可用状态列表
        
        Returns:
            状态名称列表
        """
        return list(self._expression_index_map.keys())
    
    def preload_all(self, size: str = "medium") -> bool:
        """预加载所有表情资源
        
        Args:
            size: 尺寸
            
        Returns:
            是否全部加载成功
        """
        success = True
        
        for mascot_type in ["rabbit_frog", "donut"]:
            expressions = self.get_expressions(mascot_type, size)
            if expressions is None:
                success = False
                logger.warning(f"预加载失败: {mascot_type}")
        
        if success:
            logger.info(f"成功预加载所有表情资源，尺寸: {size}")
        
        return success
    
    def clear_cache(self):
        """清除内存缓存"""
        self._rabbit_frog_expressions.clear()
        self._donut_expressions.clear()
        logger.info("已清除表情资源缓存")
    
    def save_position(self, position):
        """保存吉祥物窗口位置
        
        Args:
            position: QPoint 或 (x, y) 元组
        """
        try:
            if hasattr(position, 'x') and hasattr(position, 'y'):
                x, y = position.x(), position.y()
            else:
                x, y = position
            
            settings_file = self._resources_dir / "resources" / "mascot" / "position.txt"
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                f.write(f"{x},{y}")
            
            logger.debug(f"保存吉祥物位置: ({x}, {y})")
        except Exception as e:
            logger.warning(f"保存吉祥物位置失败: {e}")
    
    def get_saved_position(self) -> Optional[QPoint]:
        """获取保存的吉祥物窗口位置
        
        Returns:
            QPoint 或 None
        """
        try:
            settings_file = self._resources_dir / "resources" / "mascot" / "position.txt"
            
            if not settings_file.exists():
                return None
            
            with open(settings_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if ',' in content:
                x, y = content.split(',')
                return QPoint(int(x), int(y))
            
            return None
        except Exception as e:
            logger.warning(f"加载吉祥物位置失败: {e}")
            return None


mascot_resources = MascotResources()
