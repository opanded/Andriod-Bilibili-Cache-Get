"""动画效果系统 - v2.1萌化版本"""
from typing import Optional, Callable

from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect, QGraphicsDropShadowEffect
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QPoint, QSize, QRect, pyqtSignal, QSequentialAnimationGroup,
    QParallelAnimationGroup
)
from PyQt6.QtGui import QColor


class AnimationHelper:
    """动画帮助类"""
    
    @staticmethod
    def bounce(widget: QWidget, duration: int = 300, distance: int = 10):
        """弹跳动画"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.OutBounce)
        
        original_geo = widget.geometry()
        
        animation.setStartValue(original_geo)
        animation.setKeyValueAt(0.5, QRect(
            original_geo.x(),
            original_geo.y() - distance,
            original_geo.width(),
            original_geo.height()
        ))
        animation.setEndValue(original_geo)
        
        return animation
    
    @staticmethod
    def shake(widget: QWidget, duration: int = 400, distance: int = 5):
        """摇晃动画"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.OutInQuad)
        
        original_geo = widget.geometry()
        
        animation.setStartValue(original_geo)
        animation.setKeyValueAt(0.25, QRect(
            original_geo.x() - distance,
            original_geo.y(),
            original_geo.width(),
            original_geo.height()
        ))
        animation.setKeyValueAt(0.5, QRect(
            original_geo.x() + distance,
            original_geo.y(),
            original_geo.width(),
            original_geo.height()
        ))
        animation.setKeyValueAt(0.75, QRect(
            original_geo.x() - distance,
            original_geo.y(),
            original_geo.width(),
            original_geo.height()
        ))
        animation.setEndValue(original_geo)
        
        return animation
    
    @staticmethod
    def pulse(widget: QWidget, duration: int = 300, scale: float = 1.1):
        """脉冲动画"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.OutInQuad)
        
        original_geo = widget.geometry()
        center = original_geo.center()
        
        scaled_width = int(original_geo.width() * scale)
        scaled_height = int(original_geo.height() * scale)
        
        scaled_geo = QRect(
            center.x() - scaled_width // 2,
            center.y() - scaled_height // 2,
            scaled_width,
            scaled_height
        )
        
        animation.setStartValue(original_geo)
        animation.setKeyValueAt(0.5, scaled_geo)
        animation.setEndValue(original_geo)
        
        return animation
    
    @staticmethod
    def fade_in(widget: QWidget, duration: int = 300):
        """淡入动画"""
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        return animation
    
    @staticmethod
    def fade_out(widget: QWidget, duration: int = 300):
        """淡出动画"""
        effect = widget.graphicsEffect()
        if not effect or not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        return animation
    
    @staticmethod
    def slide_in(widget: QWidget, direction: str = "left", duration: int = 300):
        """滑入动画"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        final_geo = widget.geometry()
        
        if direction == "left":
            start_geo = QRect(-final_geo.width(), final_geo.y(), final_geo.width(), final_geo.height())
        elif direction == "right":
            start_geo = QRect(widget.parent().width(), final_geo.y(), final_geo.width(), final_geo.height())
        elif direction == "top":
            start_geo = QRect(final_geo.x(), -final_geo.height(), final_geo.width(), final_geo.height())
        else:
            start_geo = QRect(final_geo.x(), widget.parent().height(), final_geo.width(), final_geo.height())
        
        animation.setStartValue(start_geo)
        animation.setEndValue(final_geo)
        
        return animation
    
    @staticmethod
    def slide_out(widget: QWidget, direction: str = "right", duration: int = 300):
        """滑出动画"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.InCubic)
        
        start_geo = widget.geometry()
        
        if direction == "left":
            end_geo = QRect(-start_geo.width(), start_geo.y(), start_geo.width(), start_geo.height())
        elif direction == "right":
            end_geo = QRect(widget.parent().width(), start_geo.y(), start_geo.width(), start_geo.height())
        elif direction == "top":
            end_geo = QRect(start_geo.x(), -start_geo.height(), start_geo.width(), start_geo.height())
        else:
            end_geo = QRect(start_geo.x(), widget.parent().height(), start_geo.width(), start_geo.height())
        
        animation.setStartValue(start_geo)
        animation.setEndValue(end_geo)
        
        return animation


class CuteButtonAnimation:
    """可爱按钮动画"""
    
    def __init__(self, button: QWidget):
        self._button = button
        self._original_geo = None
        self._animation = None
    
    def on_press(self):
        """按下动画"""
        if self._animation:
            self._animation.stop()
        
        self._original_geo = self._button.geometry()
        self._animation = QPropertyAnimation(self._button, b"geometry")
        self._animation.setDuration(100)
        self._animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        pressed_geo = QRect(
            self._original_geo.x() + 2,
            self._original_geo.y() + 2,
            self._original_geo.width() - 4,
            self._original_geo.height() - 4
        )
        
        self._animation.setStartValue(self._button.geometry())
        self._animation.setEndValue(pressed_geo)
        self._animation.start()
    
    def on_release(self):
        """释放动画"""
        if self._animation:
            self._animation.stop()
        
        self._animation = QPropertyAnimation(self._button, b"geometry")
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.Type.OutBounce)
        
        self._animation.setStartValue(self._button.geometry())
        self._animation.setEndValue(self._original_geo or self._button.geometry())
        self._animation.start()


class NotificationAnimation:
    """通知动画"""
    
    @staticmethod
    def show_notification(widget: QWidget, duration: int = 300, stay_duration: int = 3000):
        """显示通知动画"""
        widget.setGraphicsEffect(None)
        
        fade_in = AnimationHelper.fade_in(widget, duration)
        
        def on_fade_in_finished():
            QTimer.singleShot(stay_duration, lambda: NotificationAnimation.hide_notification(widget, duration))
        
        fade_in.finished.connect(on_fade_in_finished)
        fade_in.start()
        
        return fade_in
    
    @staticmethod
    def hide_notification(widget: QWidget, duration: int = 300):
        """隐藏通知动画"""
        fade_out = AnimationHelper.fade_out(widget, duration)
        fade_out.finished.connect(widget.hide)
        fade_out.start()
        return fade_out


class ProgressAnimation:
    """进度条动画"""
    
    def __init__(self, progress_bar: QWidget):
        self._progress_bar = progress_bar
        self._color_offset = 0
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_gradient)
    
    def start(self):
        """开始动画"""
        self._timer.start(50)
    
    def stop(self):
        """停止动画"""
        self._timer.stop()
    
    def _update_gradient(self):
        """更新渐变"""
        self._color_offset = (self._color_offset + 1) % 100
        self._progress_bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #98D8C8, 
                    stop:0.3 #FFD93D, 
                    stop:0.6 #FFB6C1, 
                    stop:1 #98D8C8);
                background-position: {self._color_offset}% 0;
            }}
        """)


class GlowEffect:
    """发光效果"""
    
    @staticmethod
    def apply(widget: QWidget, color: QColor = QColor("#98D8C8"), blur_radius: int = 15):
        """应用发光效果"""
        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(blur_radius)
        effect.setColor(color)
        effect.setOffset(0, 0)
        widget.setGraphicsEffect(effect)
        return effect
    
    @staticmethod
    def pulse_glow(widget: QWidget, color: QColor = QColor("#98D8C8"), duration: int = 1000):
        """脉冲发光效果"""
        effect = widget.graphicsEffect()
        if not effect or not isinstance(effect, QGraphicsDropShadowEffect):
            effect = GlowEffect.apply(widget, color)
        
        animation = QPropertyAnimation(effect, b"blurRadius")
        animation.setDuration(duration)
        animation.setStartValue(5)
        animation.setKeyValueAt(0.5, 25)
        animation.setEndValue(5)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.setLoopCount(-1)
        
        return animation
