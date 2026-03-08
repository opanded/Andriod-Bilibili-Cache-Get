"""视频列表面板组件 - 使用虚拟滚动优化"""
from typing import List, Optional, Set
from pathlib import Path

from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListView, QProgressBar, QWidget, QAbstractItemView,
    QStyledItemDelegate
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QModelIndex
from PyQt6.QtGui import QPixmap, QColor

from src.models.video import Video
from src.interfaces import DownloadStatus
from src.gui.components.virtual_list import VideoListModel, VideoListDelegate


class VideoPanel(QGroupBox):
    """视频列表面板组件 - 使用虚拟滚动"""
    
    select_all = pyqtSignal()
    select_none = pyqtSignal()
    refresh_requested = pyqtSignal()
    cancel_downloads = pyqtSignal()
    download_requested = pyqtSignal()
    browse_download_path = pyqtSignal()
    search_changed = pyqtSignal(str)
    cell_double_clicked = pyqtSignal(int, int)
    video_checked = pyqtSignal(str, int)
    cover_clicked = pyqtSignal(object)
    open_video_requested = pyqtSignal(str, list)
    video_clicked = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__("🎬 缓存视频", parent)
        
        self._videos: List[Video] = []
        self._selected_videos: Set[str] = set()
        self._download_dir: str = ""
        self._is_filtering = False
        self._empty_message: str = ""
        
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        self._create_search_area(layout)
        self._create_toolbar(layout)
        self._create_loading_progress(layout)
        self._create_video_list(layout)
        self._create_download_area(layout)
        
        self.setLayout(layout)

    def _create_search_area(self, parent_layout: QVBoxLayout):
        """创建搜索区域"""
        search_layout = QHBoxLayout()
        
        search_label = QLabel("🔍 搜索:")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词筛选视频（标题/UP主/BV号）...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 10px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
            QLineEdit::placeholder {
                color: #888;
            }
        """)
        search_layout.addWidget(self.search_input, 1)
        
        self.clear_search_btn = QPushButton("✕ 清除")
        self.clear_search_btn.setFixedWidth(60)
        self.clear_search_btn.setVisible(False)
        search_layout.addWidget(self.clear_search_btn)
        
        parent_layout.addLayout(search_layout)

    def _create_toolbar(self, parent_layout: QVBoxLayout):
        """创建工具栏"""
        toolbar = QHBoxLayout()

        self.select_all_btn = QPushButton("✓ 全选")
        toolbar.addWidget(self.select_all_btn)

        self.select_none_btn = QPushButton("✗ 取消全选")
        toolbar.addWidget(self.select_none_btn)

        self.refresh_video_btn = QPushButton("🔄 刷新列表")
        self.refresh_video_btn.setEnabled(False)
        toolbar.addWidget(self.refresh_video_btn)

        self.cancel_all_btn = QPushButton("⏹ 取消下载")
        self.cancel_all_btn.setEnabled(False)
        self.cancel_all_btn.setStyleSheet("""
            QPushButton { background-color: #c62828; }
            QPushButton:hover { background-color: #e53935; }
            QPushButton:disabled { background-color: #2d2d2d; color: #666666; }
        """)
        toolbar.addWidget(self.cancel_all_btn)

        toolbar.addStretch()
        
        self.video_count_label = QLabel("共 0 个视频")
        self.video_count_label.setStyleSheet("color: #888; font-size: 12px;")
        toolbar.addWidget(self.video_count_label)
        
        self.selected_count_label = QLabel("已选 0 个")
        self.selected_count_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
        toolbar.addWidget(self.selected_count_label)

        toolbar.addStretch()

        toolbar.addWidget(QLabel("📁 下载目录:"))
        self.download_path_label = QLabel("")
        self.download_path_label.setStyleSheet("color: #4CAF50;")
        toolbar.addWidget(self.download_path_label)

        self.browse_btn = QPushButton("📂 浏览...")
        toolbar.addWidget(self.browse_btn)

        parent_layout.addLayout(toolbar)

    def _create_loading_progress(self, parent_layout: QVBoxLayout):
        """创建加载进度条"""
        self.video_load_progress = QProgressBar()
        self.video_load_progress.setVisible(False)
        self.video_load_progress.setTextVisible(True)
        self.video_load_progress.setRange(0, 0)
        parent_layout.addWidget(self.video_load_progress)

    def _create_video_list(self, parent_layout: QVBoxLayout):
        """创建视频列表（使用虚拟滚动）"""
        self.video_list = QListView()
        self.video_list.setViewMode(QListView.ViewMode.ListMode)
        self.video_list.setFlow(QListView.Flow.TopToBottom)
        self.video_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.video_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.video_list.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.video_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.video_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.video_list.setUniformItemSizes(True)
        self.video_list.setMouseTracking(True)
        
        self._video_model = VideoListModel(self)
        self._video_delegate = VideoListDelegate(self)
        
        self.video_list.setModel(self._video_model)
        self.video_list.setItemDelegate(self._video_delegate)
        
        self._apply_list_style()
        
        parent_layout.addWidget(self.video_list)

    def _apply_list_style(self):
        """应用列表样式"""
        self.video_list.setStyleSheet("""
            QListView {
                background-color: #3d3d3d;
                border: 1px solid #555;
                color: #ffffff;
                outline: none;
            }
            QListView::item {
                border: none;
                padding: 0px;
            }
            QListView::item:selected {
                background-color: transparent;
            }
            QListView::item:hover {
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def _create_download_area(self, parent_layout: QVBoxLayout):
        """创建下载区域"""
        download_layout = QHBoxLayout()

        self.download_btn = QPushButton("⬇ 下载选中视频")
        self.download_btn.setEnabled(False)
        self.download_btn.setStyleSheet("""
            QPushButton { background-color: #2196F3; font-size: 14px; padding: 10px 20px; }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #2d2d2d; color: #666666; }
        """)
        download_layout.addWidget(self.download_btn)

        download_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedWidth(300)
        download_layout.addWidget(self.progress_bar)

        parent_layout.addLayout(download_layout)

    def _connect_signals(self):
        """连接内部信号"""
        self.select_all_btn.clicked.connect(self.select_all.emit)
        self.select_none_btn.clicked.connect(self.select_none.emit)
        self.refresh_video_btn.clicked.connect(self.refresh_requested.emit)
        self.cancel_all_btn.clicked.connect(self.cancel_downloads.emit)
        self.download_btn.clicked.connect(self.download_requested.emit)
        self.browse_btn.clicked.connect(self.browse_download_path.emit)
        
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.clear_search_btn.clicked.connect(self._clear_search)
        
        self.video_list.doubleClicked.connect(self._on_double_click)
        self.video_list.clicked.connect(self._on_item_clicked)
        
        self._video_delegate.cover_clicked.connect(self.cover_clicked.emit)
        self._video_delegate.checkbox_clicked.connect(self._on_delegate_checkbox_clicked)
        self._video_delegate.open_video_clicked.connect(self.open_video_requested.emit)
        
        self._video_model.data_changed.connect(self._on_model_data_changed)
        self._video_model.loading_started.connect(self.show_loading)
        self._video_model.loading_finished.connect(self.hide_loading)

    def _on_search_text_changed(self, text: str):
        """搜索文本变化"""
        self.clear_search_btn.setVisible(bool(text.strip()))
        self.search_changed.emit(text)

    def _clear_search(self):
        """清除搜索"""
        self.search_input.clear()
        self.clear_search_btn.setVisible(False)

    def _on_double_click(self, index: QModelIndex):
        """双击事件 - 根据点击区域传递不同的列标识"""
        rect = self.video_list.visualRect(index)
        pos = self.video_list.mapFromGlobal(self.video_list.cursor().pos())
        
        hit_result = self._video_delegate.hitTest(pos, rect, index.row())
        hit_type = hit_result[0]
        
        if hit_type == 'cover':
            self.cell_double_clicked.emit(index.row(), 1)
        elif hit_type == 'title':
            self.cell_double_clicked.emit(index.row(), 2)
        else:
            self.cell_double_clicked.emit(index.row(), 0)

    def _on_item_clicked(self, index: QModelIndex):
        """单击事件 - 处理点击区域"""
        video = self._video_model.get_video_at(index.row())
        if not video:
            return
        
        rect = self.video_list.visualRect(index)
        pos = self.video_list.mapFromGlobal(self.video_list.cursor().pos())
        
        hit_result = self._video_delegate.hitTest(pos, rect, index.row())
        hit_type = hit_result[0]
        
        if hit_type == 'checkbox':
            self._video_model.toggle_selection(video.video_id)
            is_selected = video.video_id in self._video_model._selected_ids
            state = Qt.CheckState.Checked.value if is_selected else Qt.CheckState.Unchecked.value
            self.video_checked.emit(video.video_id, state)
            self._update_counts()
            self._update_download_button()
        elif hit_type == 'cover':
            self.cover_clicked.emit(video)
        elif hit_type == 'open_btn':
            if video.local_path:
                all_paths = video.all_local_paths if video.all_local_paths else [video.local_path]
                self.open_video_requested.emit(video.local_path, all_paths)
        elif hit_type == 'item':
            self.video_clicked.emit(video)

    def _on_delegate_checkbox_clicked(self, video_id: str, checked: bool):
        """委托复选框点击"""
        self._video_model.set_selected(video_id, checked)
        state = Qt.CheckState.Checked.value if checked else Qt.CheckState.Unchecked.value
        self.video_checked.emit(video_id, state)
        self._update_counts()
        self._update_download_button()

    def _on_model_data_changed(self):
        """模型数据变化"""
        self._update_counts()
        self._update_download_button()

    def set_videos(self, videos: List[Video]):
        """设置视频列表"""
        self._videos = videos
        self._selected_videos.clear()
        self._video_model.set_all_videos(videos)
        self._video_delegate.clear_covers()
        self._update_counts()
        self._update_download_button()

    def _update_counts(self, filtered_count: int = None):
        """更新计数标签"""
        total = self._video_model.get_total_count()
        displayed = self._video_model.get_displayed_count()
        selected = self._video_model.get_selected_count()
        
        if displayed < total and displayed > 0:
            self.video_count_label.setText(f"显示 {displayed}/{total} 个视频")
        else:
            self.video_count_label.setText(f"共 {total} 个视频")
        
        self.selected_count_label.setText(f"已选 {selected} 个")

    def _update_download_button(self):
        """更新下载按钮状态"""
        self.download_btn.setEnabled(self._video_model.get_selected_count() > 0)

    def update_video_status(self, video_id: str, status: str, local_path: str = None, progress: int = 0):
        """更新视频状态"""
        self._video_model.update_video_status(video_id, status, local_path, progress)

    def update_video_all_local_paths(self, video_id: str, all_files: list):
        """更新视频的所有本地路径并刷新UI"""
        self._video_model.update_video_all_local_paths(video_id, all_files)

    def get_selected_videos(self) -> List[Video]:
        """获取选中的视频"""
        return self._video_model.get_selected_videos()

    def set_download_enabled(self, enabled: bool):
        """设置下载按钮状态"""
        self.download_btn.setEnabled(enabled)

    def set_refresh_enabled(self, enabled: bool):
        """设置刷新按钮状态"""
        self.refresh_video_btn.setEnabled(enabled)

    def set_cancel_enabled(self, enabled: bool):
        """设置取消下载按钮状态"""
        self.cancel_all_btn.setEnabled(enabled)

    def set_download_dir(self, path: str):
        """设置下载目录"""
        self._download_dir = path
        self.download_path_label.setText(path)

    def get_download_dir(self) -> str:
        """获取下载目录"""
        return self._download_dir

    def show_loading(self):
        """显示加载进度"""
        self.video_load_progress.setVisible(True)

    def hide_loading(self):
        """隐藏加载进度"""
        self.video_load_progress.setVisible(False)

    def show_progress(self, value: int = 0):
        """显示下载进度"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(value)

    def hide_progress(self):
        """隐藏下载进度"""
        self.progress_bar.setVisible(False)

    def show_empty_guide(self, guide_type: str = "no_device"):
        """显示空列表指引"""
        guide_messages = {
            "no_device": "👈 请先在左侧选择设备",
            "no_videos": "📭 该设备没有缓存视频",
            "loading": "⏳ 正在加载视频列表..."
        }
        
        message = guide_messages.get(guide_type, "📭 暂无数据")
        
        self._video_model.set_all_videos([])
        self._empty_message = message
        self.video_list.update()

    def update_cover(self, video_id: str, pixmap: QPixmap):
        """更新封面图片"""
        self._video_delegate.update_cover(video_id, pixmap)
        
        for i in range(self._video_model.rowCount()):
            video = self._video_model.get_video_at(i)
            if video and video.video_id == video_id:
                idx = self._video_model.index(i)
                self._video_model.dataChanged.emit(idx, idx)
                break

    def get_video_at_row(self, row: int) -> Optional[Video]:
        """获取指定行的视频"""
        return self._video_model.get_video_at(row)

    def get_all_videos(self) -> List[Video]:
        """获取所有视频"""
        return self._video_model.get_all_videos()

    def clear_selection(self):
        """清除所有选择"""
        self._video_model.deselect_all()
        self._update_counts()
        self._update_download_button()

    def select_all_videos(self):
        """全选"""
        self._video_model.select_all()
        self._update_counts()
        self._update_download_button()

    def deselect_all_videos(self):
        """取消全选"""
        self._video_model.deselect_all()
        self._update_counts()
        self._update_download_button()

    def filter_videos(self, search_text: str):
        """筛选视频"""
        self._is_filtering = True
        self._video_model.filter_videos(search_text)
        self._is_filtering = False
        self._update_counts()

    def apply_theme(self, theme: str):
        """应用主题"""
        if theme == 'light':
            self._apply_light_theme()
        else:
            self._apply_dark_theme()

    def _apply_light_theme(self):
        """应用浅色主题"""
        self.setStyleSheet("""
            QGroupBox {
                border: 2px solid #c0c0c0;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
                color: #1a1a1a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #1a1a1a;
            }
        """)
        
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                padding: 8px 12px;
                color: #1a1a1a;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
            QLineEdit::placeholder {
                color: #888;
            }
        """)
        
        self.video_list.setStyleSheet("""
            QListView {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                color: #1a1a1a;
                outline: none;
            }
            QListView::item {
                border: none;
                padding: 0px;
            }
            QListView::item:selected {
                background-color: transparent;
            }
            QListView::item:hover {
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #e8e8e8;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        self._video_delegate._colors = {
            'bg_normal': QColor('#ffffff'),
            'bg_hover': QColor('#f5f5f5'),
            'bg_selected': QColor('#e3f2fd'),
            'text_primary': QColor('#1a1a1a'),
            'text_secondary': QColor('#666666'),
            'text_status_ok': QColor('#4CAF50'),
            'text_status_pending': QColor('#FF9800'),
            'text_status_error': QColor('#f44336'),
            'border': QColor('#e0e0e0'),
            'checkbox_border': QColor('#808080'),
            'checkbox_checked': QColor('#2196F3'),
            'cover_placeholder': QColor('#f0f0f0'),
        }
        
        self.download_btn.setStyleSheet("""
            QPushButton { background-color: #2196F3; color: white; font-size: 14px; padding: 10px 20px; border: none; border-radius: 5px; }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #e0e0e0; color: #999999; }
        """)
        
        self.cancel_all_btn.setStyleSheet("""
            QPushButton { background-color: #f44336; color: white; }
            QPushButton:hover { background-color: #d32f2f; }
            QPushButton:disabled { background-color: #e0e0e0; color: #999999; }
        """)
        
        self.video_count_label.setStyleSheet("color: #666; font-size: 12px;")
        self.selected_count_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
        self.download_path_label.setStyleSheet("color: #4CAF50;")

    def _apply_dark_theme(self):
        """应用深色主题"""
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 10px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
            QLineEdit::placeholder {
                color: #888;
            }
        """)
        
        self._apply_list_style()
        
        self._video_delegate._colors = {
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
        
        self.download_btn.setStyleSheet("""
            QPushButton { background-color: #2196F3; font-size: 14px; padding: 10px 20px; }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #2d2d2d; color: #666666; }
        """)
        
        self.cancel_all_btn.setStyleSheet("""
            QPushButton { background-color: #c62828; }
            QPushButton:hover { background-color: #e53935; }
            QPushButton:disabled { background-color: #2d2d2d; color: #666666; }
        """)
        
        self.video_count_label.setStyleSheet("color: #888; font-size: 12px;")
        self.selected_count_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
        self.download_path_label.setStyleSheet("color: #4CAF50;")
