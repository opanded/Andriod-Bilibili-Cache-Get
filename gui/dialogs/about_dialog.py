"""关于对话框 - v2.1萌化版本"""
import webbrowser
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush


class AboutDialog(QDialog):
    """关于对话框"""
    
    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self._theme = theme
        self._setup_ui()
        self._apply_theme()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("关于 B站缓存视频下载工具")
        self.setMinimumSize(480, 520)
        self.setMaximumSize(520, 580)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(30, 30, 30, 20)
        
        title_label = QLabel("🐰🐸 B站缓存视频下载工具")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)
        
        version_label = QLabel("Version 2.1.2 (萌化版)")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setObjectName("versionLabel")
        layout.addWidget(version_label)
        
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setObjectName("separatorLine")
        layout.addWidget(line1)
        
        mascot_widget = self._create_mascot_widget()
        layout.addWidget(mascot_widget)
        
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setObjectName("separatorLine")
        layout.addWidget(line2)
        
        creator_widget = self._create_creator_widget()
        layout.addWidget(creator_widget)
        
        ai_label = QLabel("AI辅助开发: 墨汁乌鸫 (GLM-5)")
        ai_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ai_label.setObjectName("aiLabel")
        layout.addWidget(ai_label)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        homepage_btn = QPushButton("访问主页")
        homepage_btn.setObjectName("homepageBtn")
        homepage_btn.clicked.connect(self._open_homepage)
        btn_layout.addWidget(homepage_btn)
        
        source_btn = QPushButton("查看源码")
        source_btn.setObjectName("sourceBtn")
        source_btn.clicked.connect(self._open_source)
        btn_layout.addWidget(source_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.setObjectName("okBtn")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_mascot_widget(self) -> QWidget:
        """创建吉祥物展示组件"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 10, 0, 10)
        
        rabbit_frog = self._create_mascot_label("兔蛙酱", "🐰🐸", "#98D8C8")
        layout.addWidget(rabbit_frog)
        
        donut = self._create_mascot_label("圈圈子", "🍩", "#FFD93D")
        layout.addWidget(donut)
        
        return widget
    
    def _create_mascot_label(self, name: str, emoji: str, color: str) -> QWidget:
        """创建吉祥物标签"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        mascot_label = QLabel()
        mascot_label.setFixedSize(80, 80)
        mascot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        pixmap = QPixmap(80, 80)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(10, 10, 60, 60)
        
        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        painter.setFont(QFont("Segoe UI Emoji", 24))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, emoji)
        
        painter.end()
        mascot_label.setPixmap(pixmap)
        layout.addWidget(mascot_label)
        
        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setObjectName("mascotName")
        layout.addWidget(name_label)
        
        return widget
    
    def _create_creator_widget(self) -> QWidget:
        """创建制作人信息组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        creator1 = self._create_creator_item(
            "制作人", "OPandED君 🐇🐸",
            "space.bilibili.com/4262942",
            "https://space.bilibili.com/4262942"
        )
        layout.addWidget(creator1)
        
        creator2 = self._create_creator_item(
            "挂名", "物语系列圈 �",
            "space.bilibili.com/31643812",
            "https://space.bilibili.com/31643812"
        )
        layout.addWidget(creator2)
        
        return widget
    
    def _create_creator_item(self, role: str, name: str, link_text: str, link_url: str) -> QWidget:
        """创建制作人条目"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        
        role_label = QLabel(f"{role}:")
        role_label.setObjectName("roleLabel")
        role_label.setFixedWidth(50)
        layout.addWidget(role_label)
        
        name_label = QLabel(name)
        name_label.setObjectName("creatorName")
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        link_label = QLabel(f'<a href="{link_url}" style="text-decoration:none;">{link_text}</a>')
        link_label.setObjectName("linkLabel")
        link_label.setOpenExternalLinks(True)
        link_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(link_label)
        
        return widget
    
    def _open_homepage(self):
        """打开主页"""
        webbrowser.open("https://space.bilibili.com/4262942")
    
    def _open_source(self):
        """打开源码"""
        webbrowser.open("https://github.com")
    
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
                font-size: 24px;
                font-weight: bold;
                color: #4CAF50;
            }
            QLabel#versionLabel {
                font-size: 14px;
                color: #888888;
            }
            QLabel#mascotName {
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
            }
            QLabel#roleLabel {
                font-size: 13px;
                color: #888888;
            }
            QLabel#creatorName {
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
            }
            QLabel#linkLabel {
                font-size: 12px;
                color: #2196F3;
            }
            QLabel#aiLabel {
                font-size: 12px;
                color: #888888;
            }
            QFrame#separatorLine {
                background-color: #555555;
                max-height: 1px;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 10px 20px;
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
                font-size: 24px;
                font-weight: bold;
                color: #4CAF50;
            }
            QLabel#versionLabel {
                font-size: 14px;
                color: #666666;
            }
            QLabel#mascotName {
                font-size: 14px;
                font-weight: bold;
                color: #1a1a1a;
            }
            QLabel#roleLabel {
                font-size: 13px;
                color: #666666;
            }
            QLabel#creatorName {
                font-size: 14px;
                font-weight: bold;
                color: #1a1a1a;
            }
            QLabel#linkLabel {
                font-size: 12px;
                color: #2196F3;
            }
            QLabel#aiLabel {
                font-size: 12px;
                color: #666666;
            }
            QFrame#separatorLine {
                background-color: #cccccc;
                max-height: 1px;
            }
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                padding: 10px 20px;
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
                font-size: 24px;
                font-weight: bold;
                color: #98D8C8;
            }
            QLabel#versionLabel {
                font-size: 14px;
                color: #8B7D8B;
            }
            QLabel#mascotName {
                font-size: 14px;
                font-weight: bold;
                color: #5D4E60;
            }
            QLabel#roleLabel {
                font-size: 13px;
                color: #8B7D8B;
            }
            QLabel#creatorName {
                font-size: 14px;
                font-weight: bold;
                color: #5D4E60;
            }
            QLabel#linkLabel {
                font-size: 12px;
                color: #98D8C8;
            }
            QLabel#aiLabel {
                font-size: 12px;
                color: #8B7D8B;
            }
            QFrame#separatorLine {
                background-color: #FFD1DC;
                max-height: 2px;
            }
            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #FFD1DC;
                border-radius: 12px;
                padding: 10px 20px;
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
            QPushButton#homepageBtn {
                background-color: #FFD93D;
                border: none;
                color: #5D4E60;
            }
            QPushButton#homepageBtn:hover {
                background-color: #FFC700;
            }
        """)
