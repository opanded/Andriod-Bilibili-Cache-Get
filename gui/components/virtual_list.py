"""虚拟滚动组件 - 支持大量视频数据的高效显示"""
from typing import List, Optional, Set, Callable
from pathlib import Path

from PyQt6.QtCore import (
    Qt, QAbstractListModel, QModelIndex, QSize, QRect, 
    pyqtSignal, QObject, QTimer
)
from PyQt6.QtWidgets import (
    QStyledItemDelegate, QStyle, QApplication, QStyleOptionViewItem
)
from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QFont, QPen, QBrush,
    QFontMetrics
)

from src.models.video import Video
from src.interfaces import DownloadStatus
from src.utils.file_utils import format_file_size


class VideoListModel(QAbstractListModel):
    """视频列表数据模型 - 支持分页加载"""
    
    VIDEO_ROLE = Qt.ItemDataRole.UserRole + 1
    TITLE_ROLE = Qt.ItemDataRole.UserRole + 2
    OWNER_ROLE = Qt.ItemDataRole.UserRole + 3
    COVER_PATH_ROLE = Qt.ItemDataRole.UserRole + 4
    QUALITY_ROLE = Qt.ItemDataRole.UserRole + 5
    FILE_SIZE_ROLE = Qt.ItemDataRole.UserRole + 6
    STATUS_ROLE = Qt.ItemDataRole.UserRole + 7
    BVID_ROLE = Qt.ItemDataRole.UserRole + 8
    VIDEO_ID_ROLE = Qt.ItemDataRole.UserRole + 9
    SELECTED_ROLE = Qt.ItemDataRole.UserRole + 10
    LOCAL_PATH_ROLE = Qt.ItemDataRole.UserRole + 11
    ALL_LOCAL_PATHS_ROLE = Qt.ItemDataRole.UserRole + 12
    
    BATCH_SIZE = 50
    
    data_changed = pyqtSignal()
    loading_started = pyqtSignal()
    loading_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._all_videos: List[Video] = []
        self._filtered_videos: List[Video] = []
        self._displayed_videos: List[Video] = []
        self._selected_ids: Set[str] = set()
        self._is_loading = False
        self._current_count = 0
        self._total_count = 0
        self._is_filtering = False
        
    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._displayed_videos)
    
    def canFetchMore(self, parent=QModelIndex()) -> bool:
        if parent.isValid():
            return False
        source_list = self._filtered_videos if self._is_filtering else self._all_videos
        return len(self._displayed_videos) < len(source_list)
    
    def fetchMore(self, parent=QModelIndex()):
        if parent.isValid() or self._is_loading:
            return
        
        source_list = self._filtered_videos if self._is_filtering else self._all_videos
            
        self._is_loading = True
        self.loading_started.emit()
        
        remaining = len(source_list) - len(self._displayed_videos)
        items_to_fetch = min(remaining, self.BATCH_SIZE)
        
        if items_to_fetch <= 0:
            self._is_loading = False
            self.loading_finished.emit()
            return
        
        start = len(self._displayed_videos)
        end = start + items_to_fetch
        
        self.beginInsertRows(QModelIndex(), start, end - 1)
        self._displayed_videos.extend(source_list[start:end])
        self.endInsertRows()
        
        self._current_count = len(self._displayed_videos)
        self._is_loading = False
        self.loading_finished.emit()
        self.data_changed.emit()
    
    def data(self, index: QModelIndex, role: int):
        if not index.isValid() or index.row() >= len(self._displayed_videos):
            return None
        
        video = self._displayed_videos[index.row()]
        
        if role == Qt.ItemDataRole.DisplayRole:
            return video.display_title
        
        if role == self.VIDEO_ROLE:
            return video
        elif role == self.TITLE_ROLE:
            return video.display_title
        elif role == self.OWNER_ROLE:
            return video.display_owner
        elif role == self.COVER_PATH_ROLE:
            return video.cover_path
        elif role == self.QUALITY_ROLE:
            return video.display_quality
        elif role == self.FILE_SIZE_ROLE:
            return format_file_size(video.file_size)
        elif role == self.STATUS_ROLE:
            return video.download_status
        elif role == self.BVID_ROLE:
            return video.bvid
        elif role == self.VIDEO_ID_ROLE:
            return video.video_id
        elif role == self.SELECTED_ROLE:
            return video.video_id in self._selected_ids
        elif role == self.LOCAL_PATH_ROLE:
            return video.local_path
        elif role == self.ALL_LOCAL_PATHS_ROLE:
            return video.all_local_paths
        
        return None
    
    def set_all_videos(self, videos: List[Video]):
        """设置所有视频数据（重置模型）"""
        self.beginResetModel()
        self._all_videos = videos
        self._filtered_videos = []
        self._is_filtering = False
        self._displayed_videos = videos[:self.BATCH_SIZE]
        self._current_count = len(self._displayed_videos)
        self._total_count = len(videos)
        self._selected_ids.clear()
        self.endResetModel()
        self.data_changed.emit()
    
    def get_video_at(self, row: int) -> Optional[Video]:
        """获取指定行的视频"""
        if 0 <= row < len(self._displayed_videos):
            return self._displayed_videos[row]
        return None
    
    def get_all_videos(self) -> List[Video]:
        """获取所有视频（包括未加载的）"""
        return self._all_videos
    
    def get_displayed_videos(self) -> List[Video]:
        """获取已显示的视频"""
        return self._displayed_videos
    
    def toggle_selection(self, video_id: str):
        """切换选中状态"""
        if video_id in self._selected_ids:
            self._selected_ids.discard(video_id)
        else:
            self._selected_ids.add(video_id)
        
        for i, video in enumerate(self._displayed_videos):
            if video.video_id == video_id:
                idx = self.index(i)
                self.dataChanged.emit(idx, idx, [self.SELECTED_ROLE])
                break
    
    def set_selected(self, video_id: str, selected: bool):
        """设置选中状态"""
        if selected:
            self._selected_ids.add(video_id)
        else:
            self._selected_ids.discard(video_id)
        
        for i, video in enumerate(self._displayed_videos):
            if video.video_id == video_id:
                idx = self.index(i)
                self.dataChanged.emit(idx, idx, [self.SELECTED_ROLE])
                break
    
    def select_all(self):
        """全选"""
        self._selected_ids = {v.video_id for v in self._all_videos}
        if self._displayed_videos:
            self.dataChanged.emit(
                self.index(0), 
                self.index(len(self._displayed_videos) - 1),
                [self.SELECTED_ROLE]
            )
        self.data_changed.emit()
    
    def deselect_all(self):
        """取消全选"""
        self._selected_ids.clear()
        if self._displayed_videos:
            self.dataChanged.emit(
                self.index(0),
                self.index(len(self._displayed_videos) - 1),
                [self.SELECTED_ROLE]
            )
        self.data_changed.emit()
    
    def get_selected_videos(self) -> List[Video]:
        """获取选中的视频"""
        return [v for v in self._all_videos if v.video_id in self._selected_ids]
    
    def get_selected_count(self) -> int:
        """获取选中数量"""
        return len(self._selected_ids)
    
    def get_total_count(self) -> int:
        """获取总数"""
        return self._total_count
    
    def get_displayed_count(self) -> int:
        """获取已显示数量"""
        return self._current_count
    
    def update_video_status(self, video_id: str, status: str, 
                           local_path: str = None, progress: int = 0):
        """更新视频状态"""
        for video in self._all_videos:
            if video.video_id == video_id:
                video.download_status = status
                if local_path:
                    video.local_path = local_path
                break
        
        for i, video in enumerate(self._displayed_videos):
            if video.video_id == video_id:
                idx = self.index(i)
                self.dataChanged.emit(idx, idx, [self.STATUS_ROLE])
                break
    
    def update_video_all_local_paths(self, video_id: str, all_files: list):
        """更新视频的所有本地路径"""
        for video in self._all_videos:
            if video.video_id == video_id:
                video.all_local_paths = all_files
                break
        
        for i, video in enumerate(self._displayed_videos):
            if video.video_id == video_id:
                idx = self.index(i)
                self.dataChanged.emit(idx, idx, [self.ALL_LOCAL_PATHS_ROLE])
                break
    
    def filter_videos(self, search_text: str):
        """筛选视频"""
        if not search_text:
            self._is_filtering = False
            self._filtered_videos = []
            self.beginResetModel()
            self._displayed_videos = self._all_videos[:self.BATCH_SIZE]
            self._current_count = len(self._displayed_videos)
            self._total_count = len(self._all_videos)
            self.endResetModel()
            self.data_changed.emit()
            return
        
        self._is_filtering = True
        search_lower = search_text.lower()
        filtered = []
        for video in self._all_videos:
            title = (video.title or "").lower()
            owner = (video.owner_name or "").lower()
            bvid = (video.bvid or "").lower()
            video_id = (video.video_id or "").lower()
            
            if (search_lower in title or 
                search_lower in owner or 
                search_lower in bvid or 
                search_lower in video_id):
                filtered.append(video)
        
        self._filtered_videos = filtered
        self.beginResetModel()
        self._displayed_videos = filtered[:self.BATCH_SIZE]
        self._current_count = len(self._displayed_videos)
        self._total_count = len(filtered)
        self.endResetModel()
        self.data_changed.emit()


class VideoListDelegate(QStyledItemDelegate):
    """视频列表自定义绘制委托"""
    
    ITEM_HEIGHT = 90
    COVER_WIDTH = 120
    COVER_HEIGHT = 68
    MARGIN = 8
    SPACING = 10
    
    cover_clicked = pyqtSignal(object)
    checkbox_clicked = pyqtSignal(str, bool)
    open_video_clicked = pyqtSignal(str, list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._cover_pixmaps: dict = {}
        self._hover_row = -1
        self._checkbox_rects: dict = {}
        self._cover_rects: dict = {}
        self._open_btn_rects: dict = {}
        self._title_rects: dict = {}
        
        self._colors = {
            'bg_normal': QColor('#3d3d3d'),
            'bg_hover': QColor('#4a4a4a'),
            'bg_selected': QColor('#2196F3'),
            'text_primary': QColor('#ffffff'),
            'text_secondary': QColor('#aaaaaa'),
            'text_status_ok': QColor('#4CAF50'),
            'text_status_pending': QColor('#FF9800'),
            'text_status_error': QColor('#f44336'),
            'border': QColor('#555'),
            'checkbox_border': QColor('#888'),
            'checkbox_checked': QColor('#2196F3'),
            'cover_placeholder': QColor('#4d4d4d'),
        }
        
        self._fonts = {
            'title': QFont('Microsoft YaHei', 11, QFont.Weight.Bold),
            'owner': QFont('Microsoft YaHei', 10),
            'info': QFont('Microsoft YaHei', 9),
            'status': QFont('Microsoft YaHei', 10),
        }
    
    def sizeHint(self, option, index) -> QSize:
        return QSize(option.rect.width(), self.ITEM_HEIGHT)
    
    def paint(self, painter: QPainter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        video = index.data(VideoListModel.VIDEO_ROLE)
        if not video:
            painter.restore()
            return
        
        rect = option.rect
        is_selected = index.data(VideoListModel.SELECTED_ROLE)
        is_hovered = option.state & QStyle.StateFlag.State_MouseOver
        
        self._draw_background(painter, rect, is_selected, is_hovered)
        
        checkbox_rect = self._draw_checkbox(painter, rect, is_selected, index.row())
        self._checkbox_rects[index.row()] = checkbox_rect
        
        cover_rect = self._draw_cover(painter, rect, video, index.row())
        self._cover_rects[index.row()] = cover_rect
        
        title_rect = self._draw_info(painter, rect, video, cover_rect, index.row())
        self._title_rects[index.row()] = title_rect
        
        self._draw_status(painter, rect, video, index.row())
        
        self._draw_separator(painter, rect)
        
        painter.restore()
    
    def _draw_background(self, painter: QPainter, rect: QRect, 
                         is_selected: bool, is_hovered: bool):
        if is_selected:
            color = self._colors['bg_selected']
        elif is_hovered:
            color = self._colors['bg_hover']
        else:
            color = self._colors['bg_normal']
        
        painter.fillRect(rect, color)
    
    def _draw_checkbox(self, painter: QPainter, rect: QRect, 
                       is_checked: bool, row: int) -> QRect:
        checkbox_size = 18
        x = rect.left() + self.MARGIN
        y = rect.top() + (rect.height() - checkbox_size) // 2
        
        checkbox_rect = QRect(x, y, checkbox_size, checkbox_size)
        
        painter.setPen(QPen(self._colors['checkbox_border'], 2))
        painter.setBrush(QBrush(QColor('#ffffff') if not is_checked else self._colors['checkbox_checked']))
        painter.drawRoundedRect(checkbox_rect, 3, 3)
        
        if is_checked:
            painter.setPen(QPen(QColor('#ffffff'), 2))
            check_points = [
                (x + 4, y + 9),
                (x + 7, y + 12),
                (x + 14, y + 5)
            ]
            path_points = []
            for px, py in check_points:
                path_points.append((px, py))
            for i in range(len(path_points) - 1):
                painter.drawLine(path_points[i][0], path_points[i][1],
                               path_points[i+1][0], path_points[i+1][1])
        
        return checkbox_rect
    
    def _draw_cover(self, painter: QPainter, rect: QRect, 
                    video: Video, row: int) -> QRect:
        x = rect.left() + self.MARGIN + 18 + self.SPACING
        y = rect.top() + (rect.height() - self.COVER_HEIGHT) // 2
        
        cover_rect = QRect(x, y, self.COVER_WIDTH, self.COVER_HEIGHT)
        
        if video.video_id in self._cover_pixmaps:
            pixmap = self._cover_pixmaps[video.video_id]
            scaled = pixmap.scaled(
                self.COVER_WIDTH, self.COVER_HEIGHT,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(cover_rect, scaled)
        else:
            painter.fillRect(cover_rect, self._colors['cover_placeholder'])
            painter.setPen(self._colors['text_secondary'])
            painter.setFont(self._fonts['info'])
            painter.drawText(cover_rect, Qt.AlignmentFlag.AlignCenter, "加载中...")
        
        painter.setPen(QPen(self._colors['border'], 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(cover_rect, 4, 4)
        
        return cover_rect
    
    def _draw_info(self, painter: QPainter, rect: QRect, 
                   video: Video, cover_rect: QRect, row: int) -> QRect:
        info_x = cover_rect.right() + self.SPACING
        info_width = rect.width() - info_x - self.MARGIN - 120
        
        title = video.display_title
        if len(title) > 50:
            title = title[:47] + "..."
        
        painter.setPen(self._colors['text_primary'])
        painter.setFont(self._fonts['title'])
        title_rect = QRect(info_x, rect.top() + self.MARGIN, info_width, 20)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title)
        
        painter.setPen(self._colors['text_secondary'])
        painter.setFont(self._fonts['owner'])
        owner_rect = QRect(info_x, rect.top() + self.MARGIN + 22, info_width, 18)
        painter.drawText(owner_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, 
                        f"UP主: {video.display_owner}")
        
        info_parts = []
        if video.bvid:
            info_parts.append(f"BV: {video.bvid}")
        info_parts.append(f"清晰度: {video.display_quality}")
        info_parts.append(f"大小: {format_file_size(video.file_size)}")
        
        info_text = " | ".join(info_parts)
        painter.setFont(self._fonts['info'])
        info_rect = QRect(info_x, rect.top() + self.MARGIN + 42, info_width, 16)
        painter.drawText(info_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, info_text)
        
        return title_rect
    
    def _draw_status(self, painter: QPainter, rect: QRect, 
                     video: Video, row: int):
        status_x = rect.right() - self.MARGIN - 100
        status_y = rect.top() + (rect.height() - 28) // 2
        status_rect = QRect(status_x, status_y, 90, 28)
        
        status = video.download_status
        
        if status == DownloadStatus.COMPLETED.value:
            self._draw_completed_status(painter, status_rect, video, row)
        elif status == DownloadStatus.DOWNLOADING.value:
            self._draw_downloading_status(painter, status_rect, video)
        elif status == DownloadStatus.QUEUED.value:
            self._draw_queued_status(painter, status_rect)
        elif status == DownloadStatus.FAILED.value:
            self._draw_failed_status(painter, status_rect)
        elif status == DownloadStatus.CANCELLED.value:
            self._draw_cancelled_status(painter, status_rect)
        else:
            self._draw_not_downloaded_status(painter, status_rect)
    
    def _draw_completed_status(self, painter: QPainter, rect: QRect, 
                               video: Video, row: int):
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self._colors['text_status_ok']))
        painter.drawRoundedRect(rect, 4, 4)
        
        painter.setPen(QColor('#ffffff'))
        painter.setFont(self._fonts['status'])
        
        all_paths = video.all_local_paths
        if all_paths and len(all_paths) > 1:
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"共{len(all_paths)}P ✓")
        else:
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "✓ 已完成")
        
        self._open_btn_rects[row] = rect
    
    def _draw_downloading_status(self, painter: QPainter, rect: QRect, video: Video):
        painter.setPen(self._colors['text_status_pending'])
        painter.setFont(self._fonts['status'])
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "⏳ 下载中...")
    
    def _draw_queued_status(self, painter: QPainter, rect: QRect):
        painter.setPen(self._colors['text_status_pending'])
        painter.setFont(self._fonts['status'])
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "⏳ 等待中")
    
    def _draw_failed_status(self, painter: QPainter, rect: QRect):
        painter.setPen(self._colors['text_status_error'])
        painter.setFont(self._fonts['status'])
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "❌ 失败")
    
    def _draw_cancelled_status(self, painter: QPainter, rect: QRect):
        painter.setPen(self._colors['text_secondary'])
        painter.setFont(self._fonts['status'])
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "⏹ 已取消")
    
    def _draw_not_downloaded_status(self, painter: QPainter, rect: QRect):
        painter.setPen(self._colors['text_secondary'])
        painter.setFont(self._fonts['status'])
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "— 未下载")
    
    def _draw_separator(self, painter: QPainter, rect: QRect):
        painter.setPen(QPen(self._colors['border'], 1))
        line_y = rect.bottom()
        painter.drawLine(rect.left(), line_y, rect.right(), line_y)
    
    def update_cover(self, video_id: str, pixmap: QPixmap):
        """更新封面图片"""
        self._cover_pixmaps[video_id] = pixmap
    
    def clear_covers(self):
        """清除所有封面缓存"""
        self._cover_pixmaps.clear()
    
    def hitTest(self, pos, rect, row) -> tuple:
        """点击测试，返回点击区域类型
        
        Returns:
            tuple: ('checkbox', 'cover', 'open_btn', 'title', 'item', None)
        """
        if row in self._checkbox_rects:
            if self._checkbox_rects[row].contains(pos):
                return ('checkbox', None)
        
        if row in self._cover_rects:
            if self._cover_rects[row].contains(pos):
                return ('cover', None)
        
        if row in self._open_btn_rects:
            if self._open_btn_rects[row].contains(pos):
                return ('open_btn', None)
        
        if row in self._title_rects:
            if self._title_rects[row].contains(pos):
                return ('title', None)
        
        if rect.contains(pos):
            return ('item', None)
        
        return (None, None)
