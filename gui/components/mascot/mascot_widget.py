"""吉祥物组件 - 可爱的双吉祥物系统（使用表情图片）"""
import logging
import random
from pathlib import Path
from typing import Optional, Dict, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsOpacityEffect, QSizePolicy, QApplication
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, 
    QPoint, QSize, pyqtSignal, QRect
)
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush

from src.gui.components.mascot.mascot_states import (
    MascotType, MascotState, MascotMessage,
    get_mascot_message, get_expression_index, EXPRESSION_INDEX_MAP,
    MascotMessageHelper
)
from src.gui.components.mascot.mascot_resources import mascot_resources

logger = logging.getLogger(__name__)


class MascotWidget(QWidget):
    """吉祥物组件 - 使用表情图片（仅负责显示和交互，不处理拖拽）"""
    
    state_changed = pyqtSignal(MascotState)
    clicked = pyqtSignal()
    long_pressed = pyqtSignal()
    double_clicked = pyqtSignal()
    
    LONG_PRESS_DURATION = 500
    DOUBLE_CLICK_INTERVAL = 300
    
    def __init__(
        self, 
        mascot_type: MascotType = MascotType.RABBIT_FROG,
        size: str = "medium",
        parent=None
    ):
        super().__init__(parent)
        self._mascot_type = mascot_type
        self._current_state = MascotState.NORMAL
        self._size = size
        self._click_count = 0
        
        self._idle_timer = QTimer(self)
        self._idle_timer.timeout.connect(self._on_idle)
        self._idle_timeout = 30000
        
        self._message_visible = True
        self._animation_enabled = True
        
        self._long_press_timer = QTimer(self)
        self._long_press_timer.setSingleShot(True)
        self._long_press_timer.timeout.connect(self._on_long_press)
        self._is_long_press = False
        
        self._last_click_time = 0
        
        self._resources_initialized = False
        
        self._setup_ui()
        self._setup_animations()
        self._start_idle_timer()
        
        self.setMinimumSize(self._get_widget_size())
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
    
    def _get_widget_size(self) -> QSize:
        """获取组件最小大小（仅作为初始大小，实际大小动态调整）"""
        mascot_size = self._get_mascot_size()
        min_width = mascot_size + 24
        min_height = mascot_size + 50
        return QSize(min_width, min_height)
    
    def _get_mascot_size(self) -> int:
        """获取吉祥物图片大小"""
        sizes = {
            "small": 64,
            "medium": 96,
            "large": 128,
        }
        return sizes.get(self._size, sizes["medium"])
    
    def _get_mascot_type_str(self) -> str:
        """获取吉祥物类型字符串"""
        if self._mascot_type == MascotType.RABBIT_FROG:
            return "rabbit_frog"
        return "donut"
    
    def sizeHint(self) -> QSize:
        """返回组件的建议大小"""
        mascot_size = self._get_mascot_size()
        
        if self._message_visible and hasattr(self, '_message_label') and self._message_label.text():
            msg_size = self._message_label.sizeHint()
            width = max(mascot_size, msg_size.width()) + 24
            height = mascot_size + msg_size.height() + 32
        else:
            width = mascot_size + 24
            height = mascot_size + 24
        
        return QSize(width, height)
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        self._mascot_label = QLabel()
        self._mascot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._mascot_label.setFixedSize(self._get_mascot_size(), self._get_mascot_size())
        layout.addWidget(self._mascot_label)
        
        self._message_label = QLabel()
        self._message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._message_label.setWordWrap(True)
        self._message_label.setSizePolicy(
            QSizePolicy.Policy.Preferred, 
            QSizePolicy.Policy.Preferred
        )
        screen_width = QApplication.primaryScreen().geometry().width()
        self._message_label.setMaximumWidth(min(int(screen_width * 0.6), 400))
        self._message_label.setMinimumWidth(100)
        self._message_label.setObjectName("mascotMessage")
        layout.addWidget(self._message_label)
        
        self._init_resources()
        self._update_appearance()
    
    def _init_resources(self):
        """初始化资源管理器"""
        try:
            mascot_resources.initialize()
            self._resources_initialized = True
            logger.info("吉祥物资源初始化成功")
        except Exception as e:
            logger.error(f"吉祥物资源初始化失败: {e}")
            self._resources_initialized = False
    
    def _setup_animations(self):
        """设置动画"""
        self._bounce_animation = QPropertyAnimation(self._mascot_label, b"geometry")
        self._bounce_animation.setDuration(500)
        self._bounce_animation.setEasingCurve(QEasingCurve.Type.OutBounce)
        
        self._shake_animation = QPropertyAnimation(self._mascot_label, b"geometry")
        self._shake_animation.setDuration(400)
        self._shake_animation.setEasingCurve(QEasingCurve.Type.OutInQuad)
        
        self._opacity_effect = QGraphicsOpacityEffect(self._mascot_label)
        self._mascot_label.setGraphicsEffect(self._opacity_effect)
        
        self._fade_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_animation.setDuration(300)
        
        self._scale_animation = QPropertyAnimation(self._mascot_label, b"geometry")
        self._scale_animation.setDuration(200)
        self._scale_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def _update_appearance(self):
        """更新外观"""
        self._update_expression()
        self._update_message()
    
    def _update_expression(self):
        """更新表情"""
        if not self._resources_initialized:
            self._draw_fallback_mascot()
            return
        
        mascot_type_str = self._get_mascot_type_str()
        state_str = self._current_state.value
        
        pixmap = mascot_resources.get_expression(
            mascot_type_str,
            state_str,
            self._size,
            random_variant=True
        )
        
        if pixmap:
            self._mascot_label.setPixmap(pixmap)
        else:
            logger.warning(f"无法加载表情: {mascot_type_str}, {state_str}")
            self._draw_fallback_mascot()
    
    def _draw_fallback_mascot(self):
        """绘制备用吉祥物（当资源加载失败时）"""
        size = self._get_mascot_size()
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        center_x = size // 2
        center_y = size // 2
        
        body_color = QColor("#98D8C8") if self._mascot_type == MascotType.RABBIT_FROG else QColor("#D4A574")
        body_radius = size // 3
        
        painter.setBrush(QBrush(body_color))
        painter.setPen(QPen(QColor("#DDDDDD"), 2))
        painter.drawEllipse(
            center_x - body_radius,
            center_y - body_radius + 5,
            body_radius * 2,
            body_radius * 2
        )
        
        eye_radius = size // 20
        eye_spacing = size // 8
        eye_y = center_y - 5
        
        painter.setBrush(QBrush(QColor("#333333")))
        for eye_x in [center_x - eye_spacing, center_x + eye_spacing]:
            painter.drawEllipse(
                eye_x - eye_radius,
                eye_y - eye_radius,
                eye_radius * 2,
                eye_radius * 2
            )
        
        painter.end()
        self._mascot_label.setPixmap(pixmap)
    
    def _update_message(self):
        """更新消息"""
        message = get_mascot_message(self._mascot_type, self._current_state)
        
        mascot_emoji = "🐰🐸" if self._mascot_type == MascotType.RABBIT_FROG else "🍩"
        display_text = f"{mascot_emoji} {message.kaomoji}\n{message.text}"
        
        self._message_label.setText(display_text)
        self._message_label.setVisible(self._message_visible)
        
        font_metrics = self._message_label.fontMetrics()
        max_width = self._message_label.maximumWidth()
        
        text_rect = font_metrics.boundingRect(
            0, 0, max_width, 0,
            Qt.TextFlag.TextWordWrap | Qt.TextFlag.TextExpandTabs,
            display_text
        )
        
        line_height_factor = 1.5
        required_height = int(text_rect.height() * line_height_factor) + 24
        
        self._message_label.setMinimumHeight(required_height)
        self._message_label.setMaximumHeight(16777215)
        
        self._message_label.updateGeometry()
        self.layout().update()
        self.layout().activate()
        
        super().adjustSize()
    
    def set_state(self, state: MascotState, animate: bool = True):
        """设置状态"""
        if self._current_state != state:
            self._current_state = state
            self._update_appearance()
            
            if animate and self._animation_enabled:
                self._play_state_animation(state)
            
            self.state_changed.emit(state)
            self._restart_idle_timer()
    
    def _play_state_animation(self, state: MascotState):
        """播放状态动画"""
        if state == MascotState.HAPPY or state == MascotState.CELEBRATE:
            self._play_bounce_animation()
        elif state == MascotState.SAD:
            self._play_shake_animation()
        elif state == MascotState.SLEEP:
            self._play_sleep_animation()
        elif state == MascotState.LOVE:
            self._play_love_animation()
        elif state == MascotState.SURPRISED:
            self._play_surprised_animation()
        elif state == MascotState.COOL:
            self._play_cool_animation()
    
    def _play_bounce_animation(self):
        """播放弹跳动画"""
        if not self._animation_enabled:
            return
        
        geo = self._mascot_label.geometry()
        self._bounce_animation.setStartValue(geo)
        self._bounce_animation.setKeyValueAt(0.5, QRect(
            geo.x(), geo.y() - 15, geo.width(), geo.height()
        ))
        self._bounce_animation.setEndValue(geo)
        self._bounce_animation.start()
    
    def _play_shake_animation(self):
        """播放摇晃动画"""
        if not self._animation_enabled:
            return
        
        geo = self._mascot_label.geometry()
        self._shake_animation.setStartValue(geo)
        self._shake_animation.setKeyValueAt(0.25, QRect(
            geo.x() - 8, geo.y(), geo.width(), geo.height()
        ))
        self._shake_animation.setKeyValueAt(0.75, QRect(
            geo.x() + 8, geo.y(), geo.width(), geo.height()
        ))
        self._shake_animation.setEndValue(geo)
        self._shake_animation.start()
    
    def _play_sleep_animation(self):
        """播放睡觉动画"""
        self._fade_animation.setStartValue(1.0)
        self._fade_animation.setKeyValueAt(0.5, 0.6)
        self._fade_animation.setEndValue(1.0)
        self._fade_animation.setLoopCount(-1)
        self._fade_animation.start()
    
    def _play_love_animation(self):
        """播放爱心动画"""
        if not self._animation_enabled:
            return
        
        geo = self._mascot_label.geometry()
        self._scale_animation.setStartValue(QRect(
            geo.x() + 5, geo.y() + 5, geo.width() - 10, geo.height() - 10
        ))
        self._scale_animation.setEndValue(geo)
        self._scale_animation.start()
    
    def _play_surprised_animation(self):
        """播放惊讶动画"""
        if not self._animation_enabled:
            return
        
        geo = self._mascot_label.geometry()
        self._scale_animation.setStartValue(QRect(
            geo.x() - 5, geo.y() - 5, geo.width() + 10, geo.height() + 10
        ))
        self._scale_animation.setEndValue(geo)
        self._scale_animation.start()
    
    def _play_cool_animation(self):
        """播放酷动画"""
        self._play_bounce_animation()
    
    def _start_idle_timer(self):
        """启动空闲计时器"""
        self._idle_timer.start(self._idle_timeout)
    
    def _restart_idle_timer(self):
        """重启空闲计时器"""
        self._idle_timer.stop()
        self._fade_animation.stop()
        self._opacity_effect.setOpacity(1.0)
        self._start_idle_timer()
    
    def _on_idle(self):
        """空闲时"""
        if self._current_state != MascotState.SLEEP:
            self.set_state(MascotState.SLEEP)
    
    def _on_long_press(self):
        """长按事件"""
        self._is_long_press = True
        self.set_state(MascotState.LOVE)
        self.long_pressed.emit()
        
        msg, state = MascotMessageHelper.love()
        self._message_label.setText(msg)
    
    def set_mascot_type(self, mascot_type: MascotType):
        """设置吉祥物类型"""
        if self._mascot_type != mascot_type:
            self._mascot_type = mascot_type
            self._update_appearance()
    
    def set_size(self, size: str):
        """设置大小"""
        if self._size != size:
            self._size = size
            self.setMinimumSize(self._get_widget_size())
            self._mascot_label.setFixedSize(self._get_mascot_size(), self._get_mascot_size())
            self._update_appearance()
    
    def set_message_visible(self, visible: bool):
        """设置消息可见性"""
        self._message_visible = visible
        self._message_label.setVisible(visible)
    
    def set_animation_enabled(self, enabled: bool):
        """设置动画启用状态"""
        self._animation_enabled = enabled
        if not enabled:
            self._bounce_animation.stop()
            self._shake_animation.stop()
            self._fade_animation.stop()
            self._scale_animation.stop()
            self._opacity_effect.setOpacity(1.0)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._long_press_timer.start(self.LONG_PRESS_DURATION)
            self._is_long_press = False
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._long_press_timer.stop()
            
            if not self._is_long_press:
                self._handle_click()
        
        self._is_long_press = False
        super().mouseReleaseEvent(event)
    
    def _handle_click(self):
        import time
        
        current_time = int(time.time() * 1000)
        
        if current_time - self._last_click_time < self.DOUBLE_CLICK_INTERVAL:
            self._handle_double_click()
            self._last_click_time = 0
        else:
            self._last_click_time = current_time
            self._handle_single_click()
    
    def _handle_single_click(self):
        self._click_count += 1
        
        if self._current_state == MascotState.SLEEP:
            self.set_state(MascotState.SURPRISED)
            QTimer.singleShot(1000, lambda: self.set_state(MascotState.NORMAL))
        else:
            self.set_state(MascotState.HAPPY)
        
        self.clicked.emit()
        self._restart_idle_timer()
    
    def _handle_double_click(self):
        self.set_state(MascotState.CELEBRATE)
        self.double_clicked.emit()
        
        celebrate_messages = [
            "🎉 好开心！",
            "🎊 太棒啦！",
            "✨ 耶！",
        ]
        self._message_label.setText(random.choice(celebrate_messages))
    
    def enterEvent(self, event):
        if self._current_state == MascotState.SLEEP:
            self.set_state(MascotState.SURPRISED)
            QTimer.singleShot(500, lambda: self.set_state(MascotState.NORMAL))
        else:
            self.set_state(MascotState.HAPPY)
        
        if self._animation_enabled:
                self._play_bounce_animation()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        pass
    
    def apply_theme(self, theme: str):
        if theme == 'cute':
            self._message_label.setStyleSheet("""
                QLabel#mascotMessage {
                    background-color: rgba(255, 240, 245, 220);
                    border-radius: 12px;
                    padding: 12px 16px;
                    color: #5D4E60;
                    font-size: 13px;
                    line-height: 1.5;
                }
            """)
        elif theme == 'light':
            self._message_label.setStyleSheet("""
                QLabel#mascotMessage {
                    background-color: rgba(255, 255, 255, 220);
                    border-radius: 12px;
                    padding: 12px 16px;
                    color: #1a1a1a;
                    font-size: 13px;
                    line-height: 1.5;
                }
            """)
        else:
            self._message_label.setStyleSheet("""
                QLabel#mascotMessage {
                    background-color: rgba(61, 61, 61, 220);
                    border-radius: 12px;
                    padding: 12px 16px;
                    color: #ffffff;
                    font-size: 13px;
                    line-height: 1.5;
                }
            """)
    
    def _calculate_message_duration(self, message: str) -> int:
        """根据消息长度计算显示时间（毫秒）"""
        char_count = len(message)
        if char_count < 10:
            return 3000
        elif char_count <= 30:
            return 5000
        else:
            extra_time = ((char_count - 30) // 10 + 1) * 2000
            return min(5000 + extra_time, 15000)

    def show_temp_message(self, message: str, duration: int = None, state: MascotState = None):
        """显示临时消息
        
        Args:
            message: 消息内容
            duration: 显示时长(毫秒)，None则自动计算
            state: 临时状态，None则保持当前状态
        """
        if duration is None:
            duration = self._calculate_message_duration(message)
        
        if not hasattr(self, '_original_message'):
            self._original_message = self._message_label.text()
            self._original_state = self._current_state
        
        self._message_label.setText(message)
        
        if state and state != self._current_state:
            self.set_state(state, animate=True)
        
        if hasattr(self, '_temp_message_timer'):
            self._temp_message_timer.stop()
        
        self._temp_message_timer = QTimer(self)
        self._temp_message_timer.setSingleShot(True)
        self._temp_message_timer.timeout.connect(self._restore_message)
        self._temp_message_timer.start(duration)
    
    def _restore_message(self):
        if hasattr(self, '_original_message'):
            self._message_label.setText(self._original_message)
            delattr(self, '_original_message')
        
        if hasattr(self, '_original_state'):
            if self._original_state != self._current_state:
                self.set_state(self._original_state, animate=True)
            delattr(self, '_original_state')
        
        if hasattr(self, '_temp_message_timer'):
            self._temp_message_timer.deleteLater()
            delattr(self, '_temp_message_timer')
