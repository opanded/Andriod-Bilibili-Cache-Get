"""成就通知组件"""
from typing import List
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsOpacityEffect, QFrame
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont

from src.gui.utils.achievements import Achievement


class AchievementNotification(QWidget):
    """成就解锁通知弹窗"""
    
    closed = pyqtSignal()
    
    def __init__(self, achievements: List[Achievement], parent=None):
        super().__init__(parent)
        self._achievements = achievements
        self._current_index = 0
        self._init_ui()
        self._setup_animation()
        
    def _init_ui(self):
        """初始化UI"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        self.setFixedSize(380, 120)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self._frame = QFrame()
        self._frame.setStyleSheet("""
            QFrame {
                background-color: rgba(76, 175, 80, 0.95);
                border: 3px solid #4CAF50;
                border-radius: 15px;
            }
        """)
        
        frame_layout = QVBoxLayout(self._frame)
        frame_layout.setContentsMargins(20, 15, 20, 15)
        frame_layout.setSpacing(8)
        
        title_layout = QHBoxLayout()
        self._title_label = QLabel("🎉 成就解锁！")
        self._title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(self._title_label)
        title_layout.addStretch()
        frame_layout.addLayout(title_layout)
        
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        
        self._icon_label = QLabel()
        self._icon_label.setStyleSheet("""
            QLabel {
                font-size: 40px;
            }
        """)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setFixedSize(50, 50)
        content_layout.addWidget(self._icon_label)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        self._name_label = QLabel()
        self._name_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        info_layout.addWidget(self._name_label)
        
        self._desc_label = QLabel()
        self._desc_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
            }
        """)
        self._desc_label.setWordWrap(True)
        info_layout.addWidget(self._desc_label)
        
        content_layout.addLayout(info_layout, 1)
        frame_layout.addLayout(content_layout)
        
        self._counter_label = QLabel()
        self._counter_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 11px;
            }
        """)
        self._counter_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        frame_layout.addWidget(self._counter_label)
        
        layout.addWidget(self._frame)
        
        self._update_content()
        
    def _setup_animation(self):
        """设置动画"""
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        
        self._fade_in = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_in.setDuration(300)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self._fade_out = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_out.setDuration(300)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_out.finished.connect(self._on_fade_out_finished)
        
        self._display_timer = QTimer(self)
        self._display_timer.setSingleShot(True)
        self._display_timer.timeout.connect(self._start_fade_out)
        
    def _update_content(self):
        """更新内容"""
        if self._current_index >= len(self._achievements):
            return
            
        achievement = self._achievements[self._current_index]
        self._icon_label.setText(achievement.icon)
        self._name_label.setText(achievement.name)
        self._desc_label.setText(achievement.description)
        
        if len(self._achievements) > 1:
            self._counter_label.setText(f"{self._current_index + 1} / {len(self._achievements)}")
        else:
            self._counter_label.setText("")
            
    def _on_fade_out_finished(self):
        """淡出完成"""
        self._current_index += 1
        
        if self._current_index < len(self._achievements):
            self._update_content()
            self._fade_in.start()
            self._display_timer.start(3000)
        else:
            self.hide()
            self.closed.emit()
            self.deleteLater()
            
    def _start_fade_out(self):
        """开始淡出"""
        self._fade_out.start()
        
    def show_notification(self):
        """显示通知"""
        if not self._achievements:
            return
            
        self._play_sound()
        
        self._fade_in.start()
        self.show()
        self._display_timer.start(3000)
        
    def _play_sound(self):
        """播放音效"""
        try:
            import winsound
            winsound.Beep(880, 100)
            winsound.Beep(1100, 100)
            winsound.Beep(1320, 150)
        except Exception:
            pass


class AchievementNotificationManager:
    """成就通知管理器"""
    
    def __init__(self, parent=None):
        self._parent = parent
        self._current_notification: AchievementNotification = None
        self._pending_achievements: List[Achievement] = []
        
    def show_achievements(self, achievements: List[Achievement]):
        """显示成就通知"""
        if not achievements:
            return
            
        if self._current_notification and self._current_notification.isVisible():
            self._pending_achievements.extend(achievements)
        else:
            self._show_notification(achievements)
            
    def _show_notification(self, achievements: List[Achievement]):
        """显示通知"""
        self._current_notification = AchievementNotification(achievements, self._parent)
        self._current_notification.closed.connect(self._on_notification_closed)
        
        if self._parent:
            parent_rect = self._parent.geometry()
            x = parent_rect.x() + (parent_rect.width() - self._current_notification.width()) // 2
            y = parent_rect.y() + 50
            self._current_notification.move(x, y)
            
        self._current_notification.show_notification()
        
    def _on_notification_closed(self):
        """通知关闭"""
        if self._pending_achievements:
            achievements = self._pending_achievements.copy()
            self._pending_achievements.clear()
            self._show_notification(achievements)
