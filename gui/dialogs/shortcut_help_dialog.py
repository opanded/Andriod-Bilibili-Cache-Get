"""快捷键说明对话框"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QWidget, QScrollArea
)
from PyQt6.QtCore import Qt


class ShortcutHelpDialog(QDialog):
    """快捷键说明对话框"""
    
    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self._theme = theme
        self._setup_ui()
        self._apply_theme()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("快捷键说明")
        self.setMinimumSize(400, 450)
        self.setMaximumSize(500, 550)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(30, 30, 30, 20)
        
        title_label = QLabel("⌨️ 快捷键说明")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)
        
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setObjectName("separatorLine")
        layout.addWidget(line1)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("scrollArea")
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        shortcuts_widget = self._create_shortcuts_widget()
        scroll_area.setWidget(shortcuts_widget)
        layout.addWidget(scroll_area)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        ok_btn = QPushButton("确定")
        ok_btn.setObjectName("okBtn")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_shortcuts_widget(self) -> QWidget:
        """创建快捷键列表组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        from src.gui.shortcuts import ShortcutManager
        
        shortcuts = ShortcutManager.DEFAULT_SHORTCUTS.copy()
        shortcuts['show_help'] = ('F1', '显示快捷键说明')
        
        for action_id, (key_sequence, description) in shortcuts.items():
            item_widget = self._create_shortcut_item(key_sequence, description)
            layout.addWidget(item_widget)
        
        layout.addStretch()
        
        return widget
    
    def _create_shortcut_item(self, key_sequence: str, description: str) -> QWidget:
        """创建快捷键条目"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 4, 0, 4)
        
        key_label = QLabel(key_sequence)
        key_label.setObjectName("keyLabel")
        key_label.setFixedWidth(100)
        key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(key_label)
        
        desc_label = QLabel(description)
        desc_label.setObjectName("descLabel")
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        return widget
    
    def _apply_theme(self):
        """应用主题"""
        if self._theme == 'cute':
            self._apply_cute_theme()
        elif self._theme == 'light':
            self._apply_light_theme()
        else:
            self._apply_dark_theme()
    
    def _apply_dark_theme(self):
        """应用深色主题"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
            }
            QLabel {
                color: #ffffff;
            }
            QLabel#titleLabel {
                font-size: 20px;
                font-weight: bold;
                color: #4CAF50;
            }
            QLabel#keyLabel {
                font-size: 13px;
                font-weight: bold;
                color: #4CAF50;
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 10px;
            }
            QLabel#descLabel {
                font-size: 13px;
                color: #ffffff;
            }
            QFrame#separatorLine {
                background-color: #555555;
                max-height: 1px;
            }
            QScrollArea#scrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea#scrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 10px 30px;
                color: #ffffff;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            QPushButton#okBtn {
                background-color: #4CAF50;
                border: none;
                font-weight: bold;
            }
            QPushButton#okBtn:hover {
                background-color: #45a049;
            }
        """)
    
    def _apply_light_theme(self):
        """应用浅色主题"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #1a1a1a;
            }
            QLabel#titleLabel {
                font-size: 20px;
                font-weight: bold;
                color: #4CAF50;
            }
            QLabel#keyLabel {
                font-size: 13px;
                font-weight: bold;
                color: #ffffff;
                background-color: #4CAF50;
                border: none;
                border-radius: 4px;
                padding: 6px 10px;
            }
            QLabel#descLabel {
                font-size: 13px;
                color: #1a1a1a;
            }
            QFrame#separatorLine {
                background-color: #cccccc;
                max-height: 1px;
            }
            QScrollArea#scrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea#scrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                padding: 10px 30px;
                color: #1a1a1a;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e8f4fc;
                border-color: #2196F3;
            }
            QPushButton#okBtn {
                background-color: #4CAF50;
                border: none;
                color: white;
                font-weight: bold;
            }
            QPushButton#okBtn:hover {
                background-color: #45a049;
            }
        """)
    
    def _apply_cute_theme(self):
        """应用萌系主题"""
        self.setStyleSheet("""
            QDialog {
                background-color: #FFF5F8;
            }
            QLabel {
                color: #5D4E60;
            }
            QLabel#titleLabel {
                font-size: 20px;
                font-weight: bold;
                color: #98D8C8;
            }
            QLabel#keyLabel {
                font-size: 13px;
                font-weight: bold;
                color: #ffffff;
                background-color: #98D8C8;
                border: none;
                border-radius: 8px;
                padding: 6px 10px;
            }
            QLabel#descLabel {
                font-size: 13px;
                color: #5D4E60;
            }
            QFrame#separatorLine {
                background-color: #FFD1DC;
                max-height: 2px;
            }
            QScrollArea#scrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea#scrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #FFD1DC;
                border-radius: 12px;
                padding: 10px 30px;
                color: #5D4E60;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #FFF0F5;
                border-color: #FFB6C1;
            }
            QPushButton#okBtn {
                background-color: #98D8C8;
                border: none;
                color: white;
                font-weight: bold;
            }
            QPushButton#okBtn:hover {
                background-color: #7FCDBB;
            }
        """)
