"""下载进度面板组件"""
import os
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QAbstractItemView, QGroupBox, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from src.interfaces import DownloadStatus


class DownloadPanel(QWidget):
    """下载进度面板组件"""

    pause_all = pyqtSignal()
    resume_all = pyqtSignal()
    retry_failed = pyqtSignal()
    cancel_task = pyqtSignal(str)
    open_file_requested = pyqtSignal(str)
    open_folder_requested = pyqtSignal(str)
    delete_history_requested = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None, theme: str = "dark"):
        super().__init__(parent)
        self._tasks: Dict[str, Dict] = {}
        self._theme = theme
        self._init_ui()
        self.apply_theme(theme)

    def set_database(self, db):
        """设置数据库引用"""
        pass

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        group = QGroupBox("⬇ 下载进度")
        group_layout = QVBoxLayout()
        group.setLayout(group_layout)

        active_tab = self._create_active_tab()
        group_layout.addWidget(active_tab)
        main_layout.addWidget(group)

    def _create_active_tab(self) -> QWidget:
        """创建进行中任务标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        tab.setLayout(layout)

        toolbar = QHBoxLayout()

        self.pause_all_btn = QPushButton("⏸ 全部暂停")
        self.pause_all_btn.clicked.connect(self.pause_all.emit)
        toolbar.addWidget(self.pause_all_btn)

        self.resume_all_btn = QPushButton("▶ 全部继续")
        self.resume_all_btn.clicked.connect(self.resume_all.emit)
        toolbar.addWidget(self.resume_all_btn)

        self.retry_failed_btn = QPushButton("🔄 重试失败")
        self.retry_failed_btn.clicked.connect(self.retry_failed.emit)
        toolbar.addWidget(self.retry_failed_btn)

        self.clear_completed_btn = QPushButton("✕ 清除已完成")
        self.clear_completed_btn.clicked.connect(self.clear_completed)
        toolbar.addWidget(self.clear_completed_btn)

        toolbar.addStretch()

        self.total_progress_label = QLabel("总进度: 0/0")
        self.total_progress_label.setStyleSheet("color: #888; font-size: 12px;")
        toolbar.addWidget(self.total_progress_label)

        layout.addLayout(toolbar)

        self.total_progress_bar = QProgressBar()
        self.total_progress_bar.setRange(0, 100)
        self.total_progress_bar.setValue(0)
        self.total_progress_bar.setTextVisible(True)
        self.total_progress_bar.setFixedHeight(20)
        self.total_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 3px;
                text-align: center;
                font-size: 11px;
                background-color: #3d3d3d;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.total_progress_bar)

        self.task_table = QTableWidget()
        self.task_table.setColumnCount(4)
        self.task_table.setHorizontalHeaderLabels(["标题", "状态", "进度", "速度"])
        self.task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.task_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.task_table.verticalHeader().setDefaultSectionSize(36)
        self.task_table.verticalHeader().setVisible(False)
        self.task_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_table.customContextMenuRequested.connect(self._show_context_menu)

        self._apply_table_style(self.task_table)
        layout.addWidget(self.task_table)

        self.empty_label = QLabel("(◕‿◕✿) 暂无下载任务")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 16px;
                padding: 40px;
            }
        """)
        self.empty_label.setVisible(True)
        layout.addWidget(self.empty_label)

        self._update_empty_state()

        return tab

    def _apply_table_style(self, table: QTableWidget):
        """应用表格样式"""
        table.setStyleSheet("""
            QTableWidget {
                background-color: #3d3d3d;
                border: 1px solid #555;
                gridline-color: #555;
                color: #ffffff;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #555;
            }
            QTableWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                padding: 8px;
                border: 1px solid #555;
                font-weight: bold;
                color: #ffffff;
            }
        """)

    def _apply_dark_theme(self):
        """应用深色主题"""
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QGroupBox {
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
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
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #666666;
            }
            QLabel {
                color: #ffffff;
            }
        """)

    def _show_context_menu(self, position):
        """显示右键菜单"""
        row = self.task_table.rowAt(position.y())
        if row < 0:
            return

        task_id = self.task_table.item(row, 0)
        if not task_id:
            return

        task_id = task_id.data(Qt.ItemDataRole.UserRole)
        if not task_id:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #3d3d3d;
                border: 1px solid #555;
            }
            QMenu::item:selected {
                background-color: #2196F3;
            }
        """)

        task_info = self._tasks.get(task_id, {})
        status = task_info.get('status', '')

        if status == DownloadStatus.DOWNLOADING.value:
            cancel_action = menu.addAction("⏹ 取消下载")
            cancel_action.triggered.connect(lambda: self.cancel_task.emit(task_id))
        elif status == DownloadStatus.QUEUED.value:
            cancel_action = menu.addAction("⏹ 取消等待")
            cancel_action.triggered.connect(lambda: self.cancel_task.emit(task_id))
        elif status == DownloadStatus.FAILED.value:
            retry_action = menu.addAction("🔄 重试下载")
            retry_action.triggered.connect(lambda: self._retry_single_task(task_id))
        elif status == DownloadStatus.PAUSED.value:
            resume_action = menu.addAction("▶ 继续下载")
            resume_action.triggered.connect(lambda: self._resume_single_task(task_id))
        elif status == DownloadStatus.COMPLETED.value:
            remove_action = menu.addAction("✕ 从列表移除")
            remove_action.triggered.connect(lambda: self.remove_task(task_id))

        if not menu.isEmpty():
            menu.exec(self.task_table.viewport().mapToGlobal(position))

    def _retry_single_task(self, task_id: str):
        """重试单个任务"""
        self.retry_failed.emit()

    def _resume_single_task(self, task_id: str):
        """继续单个任务"""
        self.resume_all.emit()

    def _update_empty_state(self):
        """更新空状态显示"""
        has_tasks = len(self._tasks) > 0
        self.task_table.setVisible(has_tasks)
        self.empty_label.setVisible(not has_tasks)
        self._update_total_progress()

    def _update_total_progress(self):
        """更新总体进度"""
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks.values() if t.get('status') == DownloadStatus.COMPLETED.value)
        failed = sum(1 for t in self._tasks.values() if t.get('status') == DownloadStatus.FAILED.value)

        self.total_progress_label.setText(f"总进度: {completed + failed}/{total}")

        if total > 0:
            progress = int((completed + failed) / total * 100)
            self.total_progress_bar.setValue(progress)
        else:
            self.total_progress_bar.setValue(0)

    def _get_status_display(self, status: str) -> str:
        """获取状态显示文本"""
        status_map = {
            DownloadStatus.NOT_DOWNLOADED.value: "未下载",
            DownloadStatus.QUEUED.value: "⏳ 等待中",
            DownloadStatus.DOWNLOADING.value: "⬇ 下载中",
            DownloadStatus.PAUSED.value: "⏸ 已暂停",
            DownloadStatus.COMPLETED.value: "✓ 已完成",
            DownloadStatus.FAILED.value: "✗ 失败",
            DownloadStatus.CANCELLED.value: "⏹ 已取消"
        }
        return status_map.get(status, "未知")

    def _get_status_color(self, status: str) -> QColor:
        """获取状态颜色"""
        color_map = {
            DownloadStatus.NOT_DOWNLOADED.value: QColor("#888888"),
            DownloadStatus.QUEUED.value: QColor("#FF9800"),
            DownloadStatus.DOWNLOADING.value: QColor("#2196F3"),
            DownloadStatus.PAUSED.value: QColor("#9E9E9E"),
            DownloadStatus.COMPLETED.value: QColor("#4CAF50"),
            DownloadStatus.FAILED.value: QColor("#f44336"),
            DownloadStatus.CANCELLED.value: QColor("#9E9E9E")
        }
        return color_map.get(status, QColor("#888888"))

    def _format_file_size(self, size: int) -> str:
        """格式化文件大小"""
        if size <= 0:
            return "--"
        elif size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"

    def add_task(self, task_id: str, title: str):
        """添加下载任务

        Args:
            task_id: 任务ID
            title: 任务标题
        """
        if task_id in self._tasks:
            return

        self._tasks[task_id] = {
            'title': title,
            'status': DownloadStatus.QUEUED.value,
            'progress': 0,
            'speed': ''
        }

        row = self.task_table.rowCount()
        self.task_table.insertRow(row)

        title_item = QTableWidgetItem(title)
        title_item.setData(Qt.ItemDataRole.UserRole, task_id)
        title_item.setToolTip(title)
        self.task_table.setItem(row, 0, title_item)

        status_item = QTableWidgetItem(self._get_status_display(DownloadStatus.QUEUED.value))
        status_item.setForeground(self._get_status_color(DownloadStatus.QUEUED.value))
        self.task_table.setItem(row, 1, status_item)

        progress_widget = QWidget()
        progress_layout = QHBoxLayout(progress_widget)
        progress_layout.setContentsMargins(4, 2, 4, 2)
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setTextVisible(True)
        progress_bar.setFixedHeight(20)
        progress_bar.setStyleSheet(self._get_progress_bar_style())
        progress_bar.setObjectName(f"progress_{task_id}")
        progress_layout.addWidget(progress_bar)
        self.task_table.setCellWidget(row, 2, progress_widget)

        speed_item = QTableWidgetItem("--")
        speed_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.task_table.setItem(row, 3, speed_item)

        self._update_empty_state()

    def update_task(self, task_id: str, status: str, progress: float = 0, speed: str = ""):
        """更新任务状态

        Args:
            task_id: 任务ID
            status: 任务状态
            progress: 进度百分比 (0-100)
            speed: 下载速度字符串
        """
        if task_id not in self._tasks:
            return

        self._tasks[task_id]['status'] = status
        self._tasks[task_id]['progress'] = progress
        self._tasks[task_id]['speed'] = speed

        for row in range(self.task_table.rowCount()):
            item = self.task_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == task_id:
                status_item = self.task_table.item(row, 1)
                if status_item:
                    status_item.setText(self._get_status_display(status))
                    status_item.setForeground(self._get_status_color(status))

                progress_widget = self.task_table.cellWidget(row, 2)
                if progress_widget:
                    progress_bar = progress_widget.findChild(QProgressBar)
                    if progress_bar:
                        if status == DownloadStatus.COMPLETED.value:
                            progress_bar.setValue(100)
                            progress_bar.setStyleSheet(self._get_progress_bar_style(status))
                        elif status == DownloadStatus.FAILED.value:
                            progress_bar.setStyleSheet(self._get_progress_bar_style(status))
                        else:
                            progress_bar.setValue(int(progress))

                speed_item = self.task_table.item(row, 3)
                if speed_item:
                    speed_item.setText(speed if speed else "--")

                break

        self._update_total_progress()

    def remove_task(self, task_id: str):
        """移除任务

        Args:
            task_id: 任务ID
        """
        if task_id not in self._tasks:
            return

        for row in range(self.task_table.rowCount()):
            item = self.task_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == task_id:
                self.task_table.removeRow(row)
                break

        del self._tasks[task_id]
        self._update_empty_state()

    def clear_completed(self):
        """清除已完成任务"""
        completed_ids = [
            task_id for task_id, info in self._tasks.items()
            if info.get('status') == DownloadStatus.COMPLETED.value
        ]

        for task_id in completed_ids:
            self.remove_task(task_id)

    def get_task_count(self) -> int:
        """获取任务数量"""
        return len(self._tasks)

    def get_active_task_count(self) -> int:
        """获取活动任务数量（下载中或等待中）"""
        return sum(
            1 for t in self._tasks.values()
            if t.get('status') in [DownloadStatus.DOWNLOADING.value, DownloadStatus.QUEUED.value]
        )

    def get_failed_task_count(self) -> int:
        """获取失败任务数量"""
        return sum(
            1 for t in self._tasks.values()
            if t.get('status') == DownloadStatus.FAILED.value
        )

    def update_buttons_state(self, has_active: bool = None, has_failed: bool = None):
        """更新按钮状态

        Args:
            has_active: 是否有活动任务（可选，不传则自动计算）
            has_failed: 是否有失败任务（可选，不传则自动计算）
        """
        if has_active is None:
            has_active = self.get_active_task_count() > 0
        if has_failed is None:
            has_failed = self.get_failed_task_count() > 0

        self.pause_all_btn.setEnabled(has_active)
        self.resume_all_btn.setEnabled(has_active)
        self.retry_failed_btn.setEnabled(has_failed)

        has_completed = any(
            t.get('status') == DownloadStatus.COMPLETED.value
            for t in self._tasks.values()
        )
        self.clear_completed_btn.setEnabled(has_completed)

    def apply_theme(self, theme: str):
        """应用主题"""
        self._theme = theme
        if theme == 'light':
            self._apply_light_theme()
        else:
            self._apply_dark_theme()

    def _apply_light_theme(self):
        """应用浅色主题"""
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                color: #1a1a1a;
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
            QLabel {
                color: #1a1a1a;
                background-color: transparent;
            }
            QTableWidget {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                gridline-color: #e0e0e0;
                color: #1a1a1a;
                alternate-background-color: #ffffff;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #e0e0e0;
                color: #1a1a1a;
                background-color: #ffffff;
            }
            QTableWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 10px;
                border: 1px solid #c0c0c0;
                font-weight: bold;
                color: #1a1a1a;
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
        """)
        
        self.total_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                text-align: center;
                font-size: 11px;
                background-color: #f0f0f0;
                color: #1a1a1a;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        
        self.empty_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 16px;
                padding: 40px;
            }
        """)
    
    def _get_progress_bar_style(self, status: str = None) -> str:
        """获取进度条样式"""
        if self._theme == 'light':
            if status == DownloadStatus.COMPLETED.value:
                return """
                    QProgressBar {
                        border: 2px solid #4CAF50;
                        border-radius: 4px;
                        text-align: center;
                        font-size: 10px;
                        background-color: #e8f5e9;
                        color: #1a1a1a;
                    }
                    QProgressBar::chunk {
                        background-color: #4CAF50;
                        border-radius: 3px;
                    }
                """
            elif status == DownloadStatus.FAILED.value:
                return """
                    QProgressBar {
                        border: 2px solid #f44336;
                        border-radius: 4px;
                        text-align: center;
                        font-size: 10px;
                        background-color: #ffebee;
                        color: #1a1a1a;
                    }
                    QProgressBar::chunk {
                        background-color: #f44336;
                        border-radius: 3px;
                    }
                """
            else:
                return """
                    QProgressBar {
                        border: 2px solid #2196F3;
                        border-radius: 4px;
                        text-align: center;
                        font-size: 10px;
                        background-color: #e3f2fd;
                        color: #1a1a1a;
                    }
                    QProgressBar::chunk {
                        background-color: #2196F3;
                        border-radius: 3px;
                    }
                """
        else:
            if status == DownloadStatus.COMPLETED.value:
                return """
                    QProgressBar {
                        border: 1px solid #4CAF50;
                        border-radius: 3px;
                        text-align: center;
                        font-size: 10px;
                    }
                    QProgressBar::chunk {
                        background-color: #4CAF50;
                    }
                """
            elif status == DownloadStatus.FAILED.value:
                return """
                    QProgressBar {
                        border: 1px solid #f44336;
                        border-radius: 3px;
                        text-align: center;
                        font-size: 10px;
                    }
                    QProgressBar::chunk {
                        background-color: #f44336;
                    }
                """
            else:
                return """
                    QProgressBar {
                        border: 1px solid #2196F3;
                        border-radius: 3px;
                        text-align: center;
                        font-size: 10px;
                    }
                    QProgressBar::chunk {
                        background-color: #2196F3;
                    }
                """

    def _apply_dark_theme(self):
        """应用深色主题"""
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QGroupBox {
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
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
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #666666;
            }
            QLabel {
                color: #ffffff;
            }
        """)
        
        self._apply_table_style(self.task_table)
        
        self.total_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 3px;
                text-align: center;
                font-size: 11px;
                background-color: #3d3d3d;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)
        
        self.empty_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 16px;
                padding: 40px;
            }
        """)
