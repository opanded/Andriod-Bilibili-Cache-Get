"""下载历史对话框"""
import os
import json
import logging
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox, QHeaderView, QAbstractItemView,
    QComboBox, QGroupBox, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

logger = logging.getLogger(__name__)


class DownloadHistoryDialog(QDialog):
    """下载历史查看对话框"""
    
    open_file_requested = pyqtSignal(str, list)
    open_folder_requested = pyqtSignal(str, list)
    
    def __init__(self, db, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self.db = db
        self._theme = theme
        self.setWindowTitle("下载历史")
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)
        
        self._init_ui()
        self._apply_theme()
        self._load_history()
        
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        stats_group = QGroupBox("统计信息")
        stats_layout = QHBoxLayout()
        
        self.total_label = QLabel("总计: 0")
        self.completed_label = QLabel("已完成: 0")
        self.failed_label = QLabel("失败: 0")
        self.cancelled_label = QLabel("已取消: 0")
        self.size_label = QLabel("总大小: 0 B")
        
        for label in [self.total_label, self.completed_label, self.failed_label, 
                      self.cancelled_label, self.size_label]:
            label.setStyleSheet("color: #aaa; font-size: 12px; padding: 5px 10px;")
            stats_layout.addWidget(label)
        
        stats_layout.addStretch()
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("状态筛选:"))
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["全部", "已完成", "失败", "已取消"])
        self.status_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.status_filter)
        
        filter_layout.addStretch()
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self._load_history)
        filter_layout.addWidget(self.refresh_btn)
        
        self.clear_btn = QPushButton("清空历史")
        self.clear_btn.clicked.connect(self._clear_history)
        self.clear_btn.setStyleSheet("background-color: #f44336;")
        filter_layout.addWidget(self.clear_btn)
        
        layout.addLayout(filter_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "视频标题", "设备ID", "文件大小", "耗时", "状态", "完成时间", "操作"
        ])
        
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 150)
        self.table.setColumnWidth(7, 220)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(36)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #3d3d3d;
                border: 1px solid #555;
                gridline-color: #555;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #2196F3;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #fff;
                padding: 5px;
                border: 1px solid #555;
            }
        """)
        
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self._apply_style()
        
    def _apply_style(self):
        """应用样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
            }
            QLabel {
                color: #ffffff;
            }
            QGroupBox {
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 12px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            QPushButton:pressed {
                background-color: #5d5d5d;
            }
            QComboBox {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px 10px;
                color: #ffffff;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3d3d3d;
                color: #ffffff;
                selection-background-color: #2196F3;
            }
        """)
        
    def _load_history(self):
        """加载历史记录"""
        try:
            with self.db.session() as session:
                from src.models.database import DownloadHistoryModel
                
                status_map = {
                    0: None,
                    1: 'completed',
                    2: 'failed',
                    3: 'cancelled'
                }
                status = status_map.get(self.status_filter.currentIndex())
                
                if status:
                    histories = session.query(DownloadHistoryModel).filter(
                        DownloadHistoryModel.status == status
                    ).order_by(DownloadHistoryModel.completed_at.desc()).limit(200).all()
                else:
                    histories = DownloadHistoryModel.get_all(session, limit=200)
                
                self.table.setRowCount(len(histories))
                
                for row, history in enumerate(histories):
                    self._add_history_row(row, history)
                
                self._update_statistics()
                
        except Exception as e:
            logger.error(f"加载历史记录失败: {e}")
            QMessageBox.warning(self, "错误", f"加载历史记录失败: {e}")
            
    def _add_history_row(self, row: int, history):
        """添加历史记录行"""
        id_item = QTableWidgetItem(str(history.id))
        id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 0, id_item)
        
        title = history.video_title or "未知"
        if len(title) > 50:
            title = title[:47] + "..."
        title_item = QTableWidgetItem(title)
        title_item.setToolTip(history.video_title or "未知")
        self.table.setItem(row, 1, title_item)
        
        device_id = history.device_id or "未知"
        if len(device_id) > 12:
            device_id = device_id[:9] + "..."
        device_item = QTableWidgetItem(device_id)
        device_item.setToolTip(history.device_id or "未知")
        self.table.setItem(row, 2, device_item)
        
        size_str = self._format_size(history.file_size or 0)
        size_item = QTableWidgetItem(size_str)
        size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 3, size_item)
        
        duration_str = self._format_duration(history.duration or 0)
        duration_item = QTableWidgetItem(duration_str)
        duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 4, duration_item)
        
        status_map = {
            'completed': ('已完成', '#4CAF50'),
            'failed': ('失败', '#f44336'),
            'cancelled': ('已取消', '#FF9800')
        }
        status_text, status_color = status_map.get(history.status, ('未知', '#888'))
        status_item = QTableWidgetItem(status_text)
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        status_item.setForeground(QColor(status_color))
        self.table.setItem(row, 5, status_item)
        
        completed_str = ""
        if history.completed_at:
            completed_str = history.completed_at.strftime("%Y-%m-%d %H:%M:%S")
        completed_item = QTableWidgetItem(completed_str)
        completed_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 6, completed_item)
        
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(4, 4, 4, 4)
        action_layout.setSpacing(6)
        action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if history.status == 'completed' and history.local_path:
            all_paths = json.loads(history.all_local_paths) if history.all_local_paths else None
            
            open_btn = QPushButton("打开")
            open_btn.setFixedSize(55, 28)
            open_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            open_btn.clicked.connect(lambda checked, p=history.local_path, ap=all_paths: self._open_file(p, ap))
            action_layout.addWidget(open_btn)
            
            folder_btn = QPushButton("位置")
            folder_btn.setFixedSize(55, 28)
            folder_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
            folder_btn.clicked.connect(lambda checked, p=history.local_path, ap=all_paths: self._open_folder(p, ap))
            action_layout.addWidget(folder_btn)
        
        delete_btn = QPushButton("删除")
        delete_btn.setFixedSize(55, 28)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        delete_btn.clicked.connect(lambda checked, h_id=history.id: self._delete_history(h_id))
        action_layout.addWidget(delete_btn)
        
        action_layout.addStretch()
        self.table.setCellWidget(row, 7, action_widget)
        
    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"
            
    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}分{secs}秒"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}时{minutes}分"
            
    def _update_statistics(self):
        """更新统计信息"""
        try:
            with self.db.session() as session:
                from src.models.database import DownloadHistoryModel
                stats = DownloadHistoryModel.get_statistics(session)
                
                self.total_label.setText(f"总计: {stats['total']}")
                self.completed_label.setText(f"已完成: {stats['completed']}")
                self.failed_label.setText(f"失败: {stats['failed']}")
                self.cancelled_label.setText(f"已取消: {stats['cancelled']}")
                self.size_label.setText(f"总大小: {self._format_size(stats['total_size'])}")
                
        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")
            
    def _on_filter_changed(self, index: int):
        """筛选条件改变"""
        self._load_history()
        
    def _open_file(self, file_path: str, all_paths: list = None):
        """打开文件"""
        if file_path and os.path.exists(file_path):
            paths = all_paths if all_paths else [file_path]
            self.open_file_requested.emit(file_path, paths)
        else:
            QMessageBox.warning(self, "提示", f"文件不存在: {file_path}")
            
    def _open_folder(self, file_path: str, all_paths: list = None):
        """打开文件所在位置"""
        if file_path:
            paths = all_paths if all_paths else [file_path]
            self.open_folder_requested.emit(file_path, paths)
            
    def _delete_history(self, history_id: int):
        """删除历史记录"""
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除这条历史记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.db.session() as session:
                    from src.models.database import DownloadHistoryModel
                    DownloadHistoryModel.delete_by_id(session, history_id)
                self._load_history()
            except Exception as e:
                logger.error(f"删除历史记录失败: {e}")
                QMessageBox.warning(self, "错误", f"删除失败: {e}")
                
    def _clear_history(self):
        """清空历史记录"""
        reply = QMessageBox.question(
            self, "确认清空", "确定要清空所有历史记录吗？\n此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.db.session() as session:
                    from src.models.database import DownloadHistoryModel
                    count = DownloadHistoryModel.clear_all(session)
                QMessageBox.information(self, "完成", f"已清空 {count} 条历史记录")
                self._load_history()
            except Exception as e:
                logger.error(f"清空历史记录失败: {e}")
                QMessageBox.warning(self, "错误", f"清空失败: {e}")
    
    def _apply_theme(self):
        """应用主题"""
        if self._theme == 'light':
            self._apply_light_theme()
        else:
            self._apply_dark_theme()
    
    def _apply_light_theme(self):
        """应用浅色主题"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QGroupBox {
                background-color: #f5f5f5;
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
            QLabel {
                color: #1a1a1a;
            }
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #a0a0a0;
                border-radius: 5px;
                padding: 8px 16px;
                color: #1a1a1a;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e8f4fc;
                border-color: #2196F3;
            }
            QPushButton:pressed {
                background-color: #cce8f7;
            }
            QPushButton:disabled {
                background-color: #e8e8e8;
                color: #888888;
                border-color: #d0d0d0;
            }
            QTableWidget {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                gridline-color: #e0e0e0;
                color: #1a1a1a;
                alternate-background-color: #ffffff;
            }
            QTableWidget::item {
                padding: 5px;
                color: #1a1a1a;
                border-bottom: 1px solid #e0e0e0;
                background-color: #ffffff;
            }
            QTableWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #e8f4fc;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 10px;
                border: 1px solid #c0c0c0;
                font-weight: bold;
                color: #1a1a1a;
            }
            QComboBox {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                padding: 6px;
                color: #1a1a1a;
                min-width: 100px;
            }
            QComboBox:hover {
                border-color: #2196F3;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                color: #1a1a1a;
                selection-background-color: #2196F3;
            }
            QScrollBar:vertical {
                background-color: #f5f5f5;
                width: 14px;
            }
            QScrollBar::handle:vertical {
                background-color: #b0b0b0;
                border-radius: 7px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #f5f5f5;
                height: 14px;
            }
            QScrollBar::handle:horizontal {
                background-color: #b0b0b0;
                border-radius: 7px;
                min-width: 30px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
    
    def _apply_dark_theme(self):
        """应用深色主题"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
            }
            QGroupBox {
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px 16px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            QPushButton:pressed {
                background-color: #5d5d5d;
            }
            QTableWidget {
                background-color: #3d3d3d;
                border: 1px solid #555;
                gridline-color: #555;
                color: #ffffff;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #2196F3;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                padding: 8px;
                border: 1px solid #555;
                font-weight: bold;
                color: #ffffff;
            }
            QComboBox {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3d3d3d;
                border: 1px solid #555;
                color: #ffffff;
                selection-background-color: #2196F3;
            }
        """)
