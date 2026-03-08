"""表情精灵图分割工具"""
import logging
from pathlib import Path
from typing import List, Optional, Tuple

from PyQt6.QtGui import QPixmap, QImage, QPainter
from PyQt6.QtCore import Qt, QSize

logger = logging.getLogger(__name__)


class SpriteSplitter:
    """精灵图分割器 - 将4x4表情图分割为独立表情"""
    
    DEFAULT_ROWS = 4
    DEFAULT_COLS = 4
    
    @staticmethod
    def split_sprite_sheet(
        image_path: str,
        rows: int = DEFAULT_ROWS,
        cols: int = DEFAULT_COLS
    ) -> List[QPixmap]:
        """分割精灵图为独立表情图片
        
        Args:
            image_path: 精灵图文件路径
            rows: 行数，默认4
            cols: 列数，默认4
            
        Returns:
            分割后的表情图片列表，按行优先顺序排列
        """
        pixmap = QPixmap(image_path)
        
        if pixmap.isNull():
            logger.error(f"无法加载精灵图: {image_path}")
            return []
        
        cell_width = pixmap.width() // cols
        cell_height = pixmap.height() // rows
        
        if cell_width <= 0 or cell_height <= 0:
            logger.error(f"精灵图尺寸无效: {pixmap.width()}x{pixmap.height()}")
            return []
        
        expressions = []
        for row in range(rows):
            for col in range(cols):
                x = col * cell_width
                y = row * cell_height
                expression = pixmap.copy(x, y, cell_width, cell_height)
                expressions.append(expression)
        
        logger.info(f"成功分割精灵图 {image_path}，共 {len(expressions)} 个表情")
        return expressions
    
    @staticmethod
    def split_and_scale(
        image_path: str,
        target_size: int,
        rows: int = DEFAULT_ROWS,
        cols: int = DEFAULT_COLS,
        smooth: bool = True
    ) -> List[QPixmap]:
        """分割精灵图并缩放到指定大小
        
        Args:
            image_path: 精灵图文件路径
            target_size: 目标尺寸（正方形）
            rows: 行数
            cols: 列数
            smooth: 是否平滑缩放
            
        Returns:
            缩放后的表情图片列表
        """
        expressions = SpriteSplitter.split_sprite_sheet(image_path, rows, cols)
        
        if not expressions:
            return []
        
        scaled_expressions = []
        transform_mode = Qt.TransformationMode.SmoothTransformation if smooth else Qt.TransformationMode.FastTransformation
        
        for expr in expressions:
            scaled = expr.scaled(
                target_size, target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                transform_mode
            )
            scaled_expressions.append(scaled)
        
        return scaled_expressions
    
    @staticmethod
    def get_expression_by_index(
        expressions: List[QPixmap],
        index: int
    ) -> Optional[QPixmap]:
        """根据索引获取表情图片
        
        Args:
            expressions: 表情图片列表
            index: 表情索引（0-15）
            
        Returns:
            表情图片，索引无效时返回None
        """
        if 0 <= index < len(expressions):
            return expressions[index]
        logger.warning(f"表情索引越界: {index}, 总数: {len(expressions)}")
        return None
    
    @staticmethod
    def get_expression_indices_for_state(state_index: int) -> List[int]:
        """获取状态对应的表情索引列表
        
        某些状态可能有多个表情变体（如开心有3种）
        
        Args:
            state_index: 状态索引
            
        Returns:
            可用的表情索引列表
        """
        state_to_expressions = {
            0: [0],       # NORMAL
            1: [1, 2, 7], # HAPPY - 3种变体
            2: [3],       # THINKING
            3: [4],       # SAD
            4: [5],       # WORKING
            5: [6],       # CELEBRATE
            6: [8],       # SLEEP
            7: [9],       # WORRIED
            8: [10],      # EXCITED
            9: [11],      # RELAX
            10: [12],     # SURPRISED
            11: [13],     # CONFUSED
            12: [14],     # LOVE
            13: [15],     # COOL
        }
        return state_to_expressions.get(state_index, [0])


def create_expression_cache_dir(base_dir: Path) -> Path:
    """创建表情缓存目录
    
    Args:
        base_dir: 基础目录
        
    Returns:
        缓存目录路径
    """
    cache_dir = base_dir / "expression_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def save_expression_cache(
    expressions: List[QPixmap],
    cache_dir: Path,
    prefix: str
) -> bool:
    """保存表情到缓存目录
    
    Args:
        expressions: 表情图片列表
        cache_dir: 缓存目录
        prefix: 文件名前缀
        
    Returns:
        是否保存成功
    """
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        for i, expr in enumerate(expressions):
            file_path = cache_dir / f"{prefix}_{i:02d}.png"
            if not expr.save(str(file_path), "PNG"):
                logger.warning(f"保存表情失败: {file_path}")
        
        logger.info(f"已缓存 {len(expressions)} 个表情到 {cache_dir}")
        return True
        
    except Exception as e:
        logger.error(f"保存表情缓存失败: {e}")
        return False


def load_expression_cache(
    cache_dir: Path,
    prefix: str,
    count: int = 16
) -> Optional[List[QPixmap]]:
    """从缓存加载表情
    
    Args:
        cache_dir: 缓存目录
        prefix: 文件名前缀
        count: 预期表情数量
        
    Returns:
        表情图片列表，加载失败返回None
    """
    expressions = []
    
    for i in range(count):
        file_path = cache_dir / f"{prefix}_{i:02d}.png"
        if not file_path.exists():
            logger.warning(f"表情缓存文件不存在: {file_path}")
            return None
        
        pixmap = QPixmap(str(file_path))
        if pixmap.isNull():
            logger.warning(f"加载表情缓存失败: {file_path}")
            return None
        
        expressions.append(pixmap)
    
    logger.info(f"从缓存加载 {len(expressions)} 个表情")
    return expressions
