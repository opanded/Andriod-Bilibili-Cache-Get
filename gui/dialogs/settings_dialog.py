"""设置对话框模块"""
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QLineEdit, QSpinBox, QCheckBox,
    QComboBox, QFileDialog, QMessageBox, QWidget, QTabWidget,
    QScrollArea, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

from ...models.settings import UserSettings
from ..utils.achievements import AchievementManager

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """设置对话框"""
    
    settings_saved = pyqtSignal(object)
    
    def __init__(self, current_settings: UserSettings, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self._original_settings = current_settings
        self.settings = UserSettings.from_dict(current_settings.to_dict())
        self._theme = theme
        self._setup_ui()
        self._load_settings()
        self._apply_theme()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("设置")
        self.setMinimumWidth(550)
        self.setMinimumHeight(500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        self.tab_widget.addTab(self._create_general_tab(), "常规")
        self.tab_widget.addTab(self._create_achievements_tab(), "成就")
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        reset_btn = QPushButton("恢复默认")
        reset_btn.clicked.connect(self._reset_settings)
        btn_layout.addWidget(reset_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("应用")
        apply_btn.clicked.connect(self._apply_settings)
        btn_layout.addWidget(apply_btn)
        
        save_btn = QPushButton("保存")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        self._apply_theme()
    
    def _create_general_tab(self) -> QWidget:
        """创建常规设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        download_group = QGroupBox("下载设置")
        download_layout = QFormLayout()
        
        self.download_dir_edit = QLineEdit()
        self.download_dir_edit.setPlaceholderText("选择默认下载目录")
        self.download_dir_edit.setReadOnly(True)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_download_dir)
        
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.download_dir_edit)
        dir_layout.addWidget(browse_btn)
        
        download_layout.addRow("下载目录:", dir_layout)
        
        self.max_downloads_spin = QSpinBox()
        self.max_downloads_spin.setRange(1, 10)
        self.max_downloads_spin.setValue(3)
        self.max_downloads_spin.setToolTip("同时下载的最大任务数")
        download_layout.addRow("最大并发下载数:", self.max_downloads_spin)
        
        download_group.setLayout(download_layout)
        layout.addWidget(download_group)
        
        refresh_group = QGroupBox("刷新设置")
        refresh_layout = QFormLayout()
        
        self.auto_refresh_check = QCheckBox("启用自动刷新")
        self.auto_refresh_check.setChecked(True)
        refresh_layout.addRow(self.auto_refresh_check)
        
        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setRange(10, 300)
        self.refresh_interval_spin.setValue(30)
        self.refresh_interval_spin.setSuffix(" 秒")
        self.refresh_interval_spin.setToolTip("自动刷新设备列表的时间间隔")
        refresh_layout.addRow("刷新间隔:", self.refresh_interval_spin)
        
        refresh_group.setLayout(refresh_layout)
        layout.addWidget(refresh_group)
        
        appearance_group = QGroupBox("外观设置")
        appearance_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("深色主题", "dark")
        self.theme_combo.addItem("浅色主题", "light")
        appearance_layout.addRow("主题:", self.theme_combo)
        
        self.language_combo = QComboBox()
        self.language_combo.addItem("简体中文", "zh_CN")
        self.language_combo.addItem("English", "en_US")
        self.language_combo.setToolTip("语言设置（需要重启生效）")
        appearance_layout.addRow("语言:", self.language_combo)
        
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        notification_group = QGroupBox("通知设置")
        notification_layout = QFormLayout()
        
        self.notification_check = QCheckBox("启用下载完成通知")
        self.notification_check.setChecked(True)
        self.notification_check.setToolTip("下载完成时发送系统通知")
        notification_layout.addRow(self.notification_check)
        
        notification_group.setLayout(notification_layout)
        layout.addWidget(notification_group)
        
        mascot_group = QGroupBox("吉祥物设置")
        mascot_layout = QFormLayout()
        
        self.mascot_type_combo = QComboBox()
        self.mascot_type_combo.addItem("兔青蛙", "rabbit_frog")
        self.mascot_type_combo.addItem("圈圈子", "donut")
        self.mascot_type_combo.setToolTip("选择显示的吉祥物类型")
        mascot_layout.addRow("吉祥物类型:", self.mascot_type_combo)
        
        self.mascot_idle_check = QCheckBox("启用待机小动作")
        self.mascot_idle_check.setChecked(True)
        self.mascot_idle_check.setToolTip("吉祥物空闲时会有随机表情变化")
        mascot_layout.addRow(self.mascot_idle_check)
        
        mascot_group.setLayout(mascot_layout)
        layout.addWidget(mascot_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_achievements_tab(self) -> QWidget:
        """创建成就标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        manager = AchievementManager()
        unlocked, total = manager.get_progress()
        
        progress_label = QLabel(f"🏆 成就进度: {unlocked}/{total}")
        progress_label.setObjectName("progressLabel")
        progress_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(progress_label)
        
        progress_bar = QLabel()
        progress_bar.setFixedHeight(8)
        progress_ratio = unlocked / total if total > 0 else 0
        progress_bar.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #4CAF50 {progress_ratio},
                stop:{progress_ratio} #4CAF50,
                stop:{progress_ratio + 0.001} #555,
                stop:1 #555);
            border-radius: 4px;
        """)
        layout.addWidget(progress_bar)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(8)
        
        achievements = manager.get_all_achievements()
        achievements.sort(key=lambda a: (not a.unlocked, a.category, a.id))
        
        current_category = None
        category_names = {
            "download": "📥 下载成就",
            "connect": "🔗 连接成就",
            "time": "⏰ 时间成就",
            "interaction": "🎮 互动成就",
            "hidden": "🔒 隐藏成就",
            "general": "📋 一般成就"
        }
        
        for achievement in achievements:
            if achievement.category != current_category:
                current_category = achievement.category
                category_label = QLabel(category_names.get(current_category, current_category))
                category_label.setStyleSheet("""
                    font-size: 14px;
                    font-weight: bold;
                    padding: 8px;
                    margin-top: 10px;
                    background-color: rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                """)
                scroll_layout.addWidget(category_label)
            
            item = self._create_achievement_item(achievement)
            scroll_layout.addWidget(item)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        return widget
    
    def _create_achievement_item(self, achievement) -> QWidget:
        """创建成就条目"""
        widget = QFrame()
        widget.setObjectName("achievementItem")
        
        if achievement.unlocked:
            widget.setStyleSheet("""
                QFrame {
                    background-color: rgba(76, 175, 80, 0.15);
                    border: 1px solid #4CAF50;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
        elif achievement.hidden:
            widget.setStyleSheet("""
                QFrame {
                    background-color: rgba(158, 158, 158, 0.1);
                    border: 1px dashed #666;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
        else:
            widget.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.05);
                    border: 1px solid #444;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)
        
        if achievement.unlocked:
            icon_label = QLabel(achievement.icon)
            icon_label.setStyleSheet("font-size: 28px;")
            name_label = QLabel(achievement.name)
            name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
            desc_label = QLabel(achievement.description)
            desc_label.setStyleSheet("font-size: 12px; color: #aaa;")
            status_label = QLabel("✅")
            status_label.setStyleSheet("font-size: 16px;")
        elif achievement.hidden:
            icon_label = QLabel("🔒")
            icon_label.setStyleSheet("font-size: 28px;")
            name_label = QLabel("???")
            name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #888;")
            desc_label = QLabel("???")
            desc_label.setStyleSheet("font-size: 12px; color: #666;")
            status_label = QLabel("❓")
            status_label.setStyleSheet("font-size: 16px;")
        else:
            icon_label = QLabel(achievement.icon)
            icon_label.setStyleSheet("font-size: 28px; opacity: 0.5;")
            name_label = QLabel(achievement.name)
            name_label.setStyleSheet("font-size: 14px; font-weight: bold; opacity: 0.7;")
            desc_label = QLabel(f"条件: {achievement.condition}")
            desc_label.setStyleSheet("font-size: 12px; color: #888;")
            status_label = QLabel("🔒")
            status_label.setStyleSheet("font-size: 16px;")
        
        icon_label.setFixedWidth(50)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.addWidget(name_label)
        info_layout.addWidget(desc_label)
        
        layout.addLayout(info_layout, 1)
        layout.addWidget(status_label)
        
        return widget
    
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
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: #f5f5f5;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                border: 1px solid #c0c0c0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom-color: #ffffff;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e8e8e8;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #e0e0e0;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #b0b0b0;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #909090;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
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
            QLabel {
                color: #1a1a1a;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                padding: 8px;
                color: #1a1a1a;
            }
            QLineEdit:read-only {
                background-color: #e8e8e8;
            }
            QSpinBox {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                padding: 6px;
                color: #1a1a1a;
            }
            QCheckBox {
                color: #1a1a1a;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #808080;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QCheckBox::indicator:hover {
                border-color: #2196F3;
                background-color: #e8f4fc;
            }
            QCheckBox::indicator:checked {
                background-color: #2196F3;
                border-color: #2196F3;
            }
            QCheckBox::indicator:disabled {
                background-color: #e8e8e8;
                border-color: #c0c0c0;
            }
            QComboBox {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                padding: 6px;
                color: #1a1a1a;
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
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #a0a0a0;
                border-radius: 5px;
                padding: 10px 18px;
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
            QPushButton:default {
                background-color: #2196F3;
                border: none;
                color: white;
            }
            QPushButton:default:hover {
                background-color: #1976D2;
            }
        """)
    
    def _apply_dark_theme(self):
        """应用深色主题"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
            }
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #2d2d2d;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #3d3d3d;
                border: 1px solid #555;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                color: #ffffff;
            }
            QTabBar::tab:selected {
                background-color: #4d4d4d;
                border-bottom-color: #4d4d4d;
            }
            QTabBar::tab:hover:!selected {
                background-color: #454545;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
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
            QLabel {
                color: #ffffff;
            }
            QLineEdit {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
            }
            QLineEdit:read-only {
                background-color: #353535;
            }
            QSpinBox {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px;
                color: #ffffff;
            }
            QCheckBox {
                color: #ffffff;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QComboBox {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px;
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
            QPushButton:default {
                background-color: #2196F3;
                border: none;
            }
            QPushButton:default:hover {
                background-color: #1976D2;
            }
        """)
    
    def _load_settings(self):
        """加载设置到UI"""
        if self.settings.download_dir:
            self.download_dir_edit.setText(self.settings.download_dir)
        
        self.max_downloads_spin.setValue(self.settings.max_concurrent_downloads)
        self.auto_refresh_check.setChecked(self.settings.auto_refresh)
        self.refresh_interval_spin.setValue(self.settings.refresh_interval)
        
        theme_index = self.theme_combo.findData(self.settings.theme)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
        
        lang_index = self.language_combo.findData(self.settings.language)
        if lang_index >= 0:
            self.language_combo.setCurrentIndex(lang_index)
        
        self.notification_check.setChecked(self.settings.enable_notification)
        
        if hasattr(self, 'mascot_type_combo'):
            mascot_type_index = self.mascot_type_combo.findData(self.settings.mascot_type)
            if mascot_type_index >= 0:
                self.mascot_type_combo.setCurrentIndex(mascot_type_index)
        
        if hasattr(self, 'mascot_idle_check'):
            self.mascot_idle_check.setChecked(getattr(self.settings, 'mascot_idle_actions', True))
    
    def _browse_download_dir(self):
        """浏览下载目录"""
        current_dir = self.download_dir_edit.text() or str(Path.home())
        path = QFileDialog.getExistingDirectory(
            self, "选择下载目录", current_dir
        )
        if path:
            self.download_dir_edit.setText(path)
    
    def _reset_settings(self):
        """重置设置"""
        reply = QMessageBox.question(
            self, "确认重置",
            "确定要恢复默认设置吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings = UserSettings()
            self._load_settings()
    
    def _apply_settings(self):
        """应用设置（不关闭对话框）"""
        self.settings.download_dir = self.download_dir_edit.text()
        self.settings.max_concurrent_downloads = self.max_downloads_spin.value()
        self.settings.auto_refresh = self.auto_refresh_check.isChecked()
        self.settings.refresh_interval = self.refresh_interval_spin.value()
        self.settings.theme = self.theme_combo.currentData()
        self.settings.language = self.language_combo.currentData()
        self.settings.enable_notification = self.notification_check.isChecked()
        
        if hasattr(self, 'mascot_type_combo'):
            self.settings.mascot_type = self.mascot_type_combo.currentData()
        if hasattr(self, 'mascot_idle_check'):
            self.settings.mascot_idle_actions = self.mascot_idle_check.isChecked()
        
        self.settings.validate()
        
        new_settings = UserSettings.from_dict(self.settings.to_dict())
        self.settings_saved.emit(new_settings)
    
    def _save_settings(self):
        """保存设置"""
        self.settings.download_dir = self.download_dir_edit.text()
        self.settings.max_concurrent_downloads = self.max_downloads_spin.value()
        self.settings.auto_refresh = self.auto_refresh_check.isChecked()
        self.settings.refresh_interval = self.refresh_interval_spin.value()
        self.settings.theme = self.theme_combo.currentData()
        self.settings.language = self.language_combo.currentData()
        self.settings.enable_notification = self.notification_check.isChecked()
        
        if hasattr(self, 'mascot_type_combo'):
            self.settings.mascot_type = self.mascot_type_combo.currentData()
        if hasattr(self, 'mascot_idle_check'):
            self.settings.mascot_idle_actions = self.mascot_idle_check.isChecked()
        
        self.settings.validate()
        
        new_settings = UserSettings.from_dict(self.settings.to_dict())
        self.settings_saved.emit(new_settings)
        self.accept()
    
    def get_settings(self) -> UserSettings:
        """获取当前设置"""
        return self.settings
