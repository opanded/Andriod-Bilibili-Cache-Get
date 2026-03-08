"""空状态组件 - 显示可爱的空状态提示"""
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush

from src.gui.utils.kaomoji import KaomojiHelper


class EmptyStateWidget(QWidget):
    """空状态组件"""
    
    action_clicked = pyqtSignal()
    
    def __init__(
        self, 
        state_type: str = "no_device",
        theme: str = "dark",
        parent=None
    ):
        super().__init__(parent)
        self._state_type = state_type
        self._theme = theme
        self._setup_ui()
        self._apply_theme()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 40, 40, 40)
        
        self._illustration_label = QLabel()
        self._illustration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._illustration_label.setFixedSize(120, 120)
        layout.addWidget(self._illustration_label)
        
        self._message_label = QLabel()
        self._message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._message_label.setWordWrap(True)
        self._message_label.setObjectName("emptyMessage")
        layout.addWidget(self._message_label)
        
        self._tip_label = QLabel()
        self._tip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._tip_label.setWordWrap(True)
        self._tip_label.setObjectName("emptyTip")
        layout.addWidget(self._tip_label)
        
        self._action_btn = QPushButton()
        self._action_btn.setObjectName("actionBtn")
        self._action_btn.clicked.connect(self.action_clicked.emit)
        self._action_btn.setVisible(False)
        layout.addWidget(self._action_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self._update_content()
        self._draw_illustration()
    
    def _get_content(self) -> tuple:
        """获取内容"""
        contents = {
            "no_device": (
                KaomojiHelper.random('EMPTY_DEVICE'),
                KaomojiHelper.random('TIPS'),
                "刷新设备",
                "refresh"
            ),
            "no_video": (
                KaomojiHelper.random('EMPTY_VIDEO'),
                KaomojiHelper.random('TIPS'),
                "刷新视频",
                "refresh"
            ),
            "no_search_result": (
                "(・_・)? 没找到相关内容...",
                "试试其他关键词？",
                "清除搜索",
                "clear"
            ),
            "no_history": (
                "(｡･ω･｡) 还没有下载记录哦~",
                "下载的视频会显示在这里",
                None,
                None
            ),
            "loading": (
                KaomojiHelper.random('LOADING'),
                KaomojiHelper.random('TIPS'),
                None,
                None
            ),
        }
        return contents.get(self._state_type, contents["no_device"])
    
    def _update_content(self):
        """更新内容"""
        message, tip, action_text, action_type = self._get_content()
        
        self._message_label.setText(message)
        self._tip_label.setText(tip)
        
        if action_text:
            self._action_btn.setText(action_text)
            self._action_btn.setVisible(True)
        else:
            self._action_btn.setVisible(False)
    
    def _draw_illustration(self):
        """绘制插图"""
        size = 120
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self._state_type == "no_device":
            self._draw_no_device(painter, size)
        elif self._state_type == "no_video":
            self._draw_no_video(painter, size)
        elif self._state_type == "no_search_result":
            self._draw_no_search(painter, size)
        elif self._state_type == "no_history":
            self._draw_no_history(painter, size)
        else:
            self._draw_loading(painter, size)
        
        painter.end()
        self._illustration_label.setPixmap(pixmap)
    
    def _draw_no_device(self, painter: QPainter, size: int):
        """绘制无设备插图"""
        center_x = size // 2
        center_y = size // 2
        
        body_color = QColor("#FFFFFF")
        accent_color = QColor("#98D8C8")
        
        body_radius = 35
        painter.setBrush(QBrush(body_color))
        painter.setPen(QPen(QColor("#DDDDDD"), 2))
        painter.drawEllipse(
            center_x - body_radius,
            center_y - body_radius + 5,
            body_radius * 2,
            body_radius * 2
        )
        
        ear_width = 12
        ear_height = 25
        ear_spacing = 18
        
        for ear_x in [center_x - ear_spacing, center_x + ear_spacing]:
            painter.setBrush(QBrush(body_color))
            painter.drawEllipse(
                ear_x - ear_width // 2,
                center_y - body_radius - ear_height + 10,
                ear_width,
                ear_height
            )
            painter.setBrush(QBrush(accent_color))
            painter.drawEllipse(
                ear_x - ear_width // 2 + 2,
                center_y - body_radius - ear_height + 14,
                ear_width - 4,
                ear_height - 8
            )
        
        eye_radius = 4
        eye_spacing = 12
        eye_y = center_y - 3
        
        for eye_x in [center_x - eye_spacing, center_x + eye_spacing]:
            painter.setBrush(QBrush(QColor("#333333")))
            painter.drawEllipse(
                eye_x - eye_radius,
                eye_y - eye_radius,
                eye_radius * 2,
                eye_radius * 2
            )
        
        magnifier_size = 30
        magnifier_x = center_x + 20
        magnifier_y = center_y + 15
        
        painter.setBrush(QBrush(QColor("#FFB6C1")))
        painter.setPen(QPen(QColor("#FF69B4"), 2))
        painter.drawEllipse(
            magnifier_x,
            magnifier_y,
            magnifier_size,
            magnifier_size
        )
        
        painter.setPen(QPen(QColor("#FF69B4"), 3))
        painter.drawLine(
            magnifier_x + magnifier_size - 2,
            magnifier_y + magnifier_size - 2,
            magnifier_x + magnifier_size + 10,
            magnifier_y + magnifier_size + 10
        )
    
    def _draw_no_video(self, painter: QPainter, size: int):
        """绘制无视频插图"""
        center_x = size // 2
        center_y = size // 2
        
        bagel_color = QColor("#D4A574")
        egg_color = QColor("#FFD93D")
        
        bagel_radius = 35
        painter.setBrush(QBrush(bagel_color))
        painter.setPen(QPen(QColor("#B8956B"), 2))
        painter.drawEllipse(
            center_x - bagel_radius,
            center_y - bagel_radius + 5,
            bagel_radius * 2,
            bagel_radius * 2
        )
        
        hole_radius = bagel_radius // 2
        painter.setBrush(QBrush(QColor("#FFF5F8")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            center_x - hole_radius,
            center_y - hole_radius + 5,
            hole_radius * 2,
            hole_radius * 2
        )
        
        eye_radius = 4
        eye_spacing = 12
        eye_y = center_y - 3
        
        for eye_x in [center_x - eye_spacing, center_x + eye_spacing]:
            painter.setBrush(QBrush(QColor("#333333")))
            painter.drawEllipse(
                eye_x - eye_radius,
                eye_y - eye_radius,
                eye_radius * 2,
                eye_radius * 2
            )
        
        screen_x = center_x + 25
        screen_y = center_y - 20
        screen_w = 25
        screen_h = 18
        
        painter.setBrush(QBrush(QColor("#3d3d3d")))
        painter.setPen(QPen(QColor("#555"), 1))
        painter.drawRoundedRect(screen_x, screen_y, screen_w, screen_h, 3, 3)
        
        painter.setPen(QPen(QColor("#888"), 1))
        for i in range(3):
            painter.drawLine(
                screen_x + 3,
                screen_y + 4 + i * 5,
                screen_x + screen_w - 3,
                screen_y + 4 + i * 5
            )
    
    def _draw_no_search(self, painter: QPainter, size: int):
        """绘制无搜索结果插图"""
        center_x = size // 2
        center_y = size // 2
        
        body_color = QColor("#FFFFFF")
        accent_color = QColor("#98D8C8")
        
        body_radius = 30
        painter.setBrush(QBrush(body_color))
        painter.setPen(QPen(QColor("#DDDDDD"), 2))
        painter.drawEllipse(
            center_x - body_radius - 15,
            center_y - body_radius,
            body_radius * 2,
            body_radius * 2
        )
        
        painter.drawEllipse(
            center_x - body_radius + 15,
            center_y - body_radius,
            body_radius * 2,
            body_radius * 2
        )
        
        eye_radius = 3
        for x_offset in [-15, 15]:
            eye_x = center_x + x_offset
            painter.setBrush(QBrush(QColor("#333333")))
            painter.drawEllipse(
                eye_x - eye_radius,
                center_y - 3 - eye_radius,
                eye_radius * 2,
                eye_radius * 2
            )
        
        painter.setPen(QPen(QColor("#333333"), 2))
        painter.drawLine(center_x - 10, center_y + 10, center_x + 10, center_y + 10)
        
        question_x = center_x + 35
        question_y = center_y - 20
        painter.setPen(QPen(accent_color, 3))
        painter.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        painter.drawText(question_x, question_y, "?")
    
    def _draw_no_history(self, painter: QPainter, size: int):
        """绘制无历史记录插图"""
        center_x = size // 2
        center_y = size // 2
        
        book_color = QColor("#FFD93D")
        page_color = QColor("#FFFFFF")
        
        book_w = 50
        book_h = 60
        
        painter.setBrush(QBrush(book_color))
        painter.setPen(QPen(QColor("#E6C200"), 2))
        painter.drawRoundedRect(
            center_x - book_w // 2,
            center_y - book_h // 2,
            book_w,
            book_h,
            5,
            5
        )
        
        painter.setBrush(QBrush(page_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(
            center_x - book_w // 2 + 5,
            center_y - book_h // 2 + 5,
            book_w - 10,
            book_h - 10
        )
        
        painter.setPen(QPen(QColor("#DDD"), 1))
        for i in range(4):
            painter.drawLine(
                center_x - book_w // 2 + 10,
                center_y - book_h // 2 + 15 + i * 10,
                center_x + book_w // 2 - 10,
                center_y - book_h // 2 + 15 + i * 10
            )
        
        body_color = QColor("#FFFFFF")
        body_radius = 15
        painter.setBrush(QBrush(body_color))
        painter.setPen(QPen(QColor("#DDDDDD"), 1))
        painter.drawEllipse(
            center_x + 25,
            center_y - 30,
            body_radius * 2,
            body_radius * 2
        )
        
        ear_width = 6
        ear_height = 12
        for ear_x in [center_x + 25, center_x + 35]:
            painter.drawEllipse(
                ear_x - ear_width // 2,
                center_y - 30 - ear_height + 5,
                ear_width,
                ear_height
            )
    
    def _draw_loading(self, painter: QPainter, size: int):
        """绘制加载中插图"""
        center_x = size // 2
        center_y = size // 2
        
        accent_color = QColor("#98D8C8")
        
        for i in range(8):
            angle = i * 45
            import math
            x = center_x + 30 * math.cos(math.radians(angle))
            y = center_y + 30 * math.sin(math.radians(angle))
            
            dot_size = 8 + (i % 2) * 4
            alpha = 255 - i * 25
            
            color = QColor(accent_color)
            color.setAlpha(alpha)
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                int(x - dot_size // 2),
                int(y - dot_size // 2),
                dot_size,
                dot_size
            )
    
    def set_state_type(self, state_type: str):
        """设置状态类型"""
        if self._state_type != state_type:
            self._state_type = state_type
            self._update_content()
            self._draw_illustration()
    
    def set_theme(self, theme: str):
        """设置主题"""
        self._theme = theme
        self._apply_theme()
    
    def _apply_theme(self):
        """应用主题"""
        if self._theme == 'cute':
            self._message_label.setStyleSheet("""
                QLabel#emptyMessage {
                    font-size: 16px;
                    color: #5D4E60;
                    padding: 10px;
                }
            """)
            self._tip_label.setStyleSheet("""
                QLabel#emptyTip {
                    font-size: 13px;
                    color: #8B7D8B;
                    padding: 5px;
                }
            """)
            self._action_btn.setStyleSheet("""
                QPushButton#actionBtn {
                    background-color: #98D8C8;
                    border: none;
                    border-radius: 12px;
                    padding: 10px 24px;
                    color: #FFFFFF;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton#actionBtn:hover {
                    background-color: #7FCDBB;
                }
            """)
        elif self._theme == 'light':
            self._message_label.setStyleSheet("""
                QLabel#emptyMessage {
                    font-size: 16px;
                    color: #1a1a1a;
                    padding: 10px;
                }
            """)
            self._tip_label.setStyleSheet("""
                QLabel#emptyTip {
                    font-size: 13px;
                    color: #666666;
                    padding: 5px;
                }
            """)
            self._action_btn.setStyleSheet("""
                QPushButton#actionBtn {
                    background-color: #4CAF50;
                    border: none;
                    border-radius: 5px;
                    padding: 10px 24px;
                    color: #FFFFFF;
                    font-size: 13px;
                }
                QPushButton#actionBtn:hover {
                    background-color: #45a049;
                }
            """)
        else:
            self._message_label.setStyleSheet("""
                QLabel#emptyMessage {
                    font-size: 16px;
                    color: #ffffff;
                    padding: 10px;
                }
            """)
            self._tip_label.setStyleSheet("""
                QLabel#emptyTip {
                    font-size: 13px;
                    color: #888888;
                    padding: 5px;
                }
            """)
            self._action_btn.setStyleSheet("""
                QPushButton#actionBtn {
                    background-color: #4CAF50;
                    border: none;
                    border-radius: 4px;
                    padding: 10px 24px;
                    color: #FFFFFF;
                    font-size: 13px;
                }
                QPushButton#actionBtn:hover {
                    background-color: #45a049;
                }
            """)
