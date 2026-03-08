"""独立浮动吉祥物窗口"""
import logging
from typing import Optional

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QRect
from PyQt6.QtGui import QPixmap

from src.gui.components.mascot.mascot_widget import MascotWidget
from src.gui.components.mascot.mascot_states import MascotType, MascotState

from src.gui.components.mascot.mascot_resources import mascot_resources

logger = logging.getLogger(__name__)


class FloatingMascot(QWidget):
    """独立浮动吉祥物窗口 - 可拖拽，始终置顶"""
    
    position_changed = pyqtSignal(QPoint)
    mascot_clicked = pyqtSignal()
    mascot_long_pressed = pyqtSignal()
    mascot_double_clicked = pyqtSignal()
    
    def __init__(
        self,
        mascot_type: MascotType = MascotType.RABBIT_FROG,
        size: str = "medium",
        parent=None
    ):
        super().__init__(parent)
        
        self._mascot_type = mascot_type
        self._size = size
        self._drag_pos = None
        self._saved_position = None
        
        self._setup_window()
        self._setup_mascot_widget()
        self._load_saved_position()
    
    def _setup_window(self):
        """设置窗口属性"""
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setMouseTracking(True)
    
    def _setup_mascot_widget(self):
        """设置内部吉祥物组件"""
        self._mascot_widget = MascotWidget(
            mascot_type=self._mascot_type,
            size=self._size,
            parent=self
        )
        self._mascot_widget.clicked.connect(self._on_mascot_clicked)
        self._mascot_widget.long_pressed.connect(self._on_mascot_long_pressed)
        self._mascot_widget.double_clicked.connect(self._on_mascot_double_clicked)
        
        self._mascot_widget.move(0, 0)
        self._mascot_widget.show()
        
        self.adjustSize()
    
    def adjustSize(self):
        """调整窗口大小以适应内容"""
        self._mascot_widget.adjustSize()
        
        hint = self._mascot_widget.sizeHint()
        
        self.setFixedSize(hint)
    
    def _load_saved_position(self):
        """加载保存的位置"""
        try:
            mascot_resources.initialize()
            position = mascot_resources.get_saved_position()
            if position:
                self._saved_position = position
                self.move(position)
        except Exception as e:
            logger.warning(f"加载吉祥物位置失败: {e}")
    
    def save_position(self):
        """保存当前位置"""
        try:
            mascot_resources.save_position(self.pos())
        except Exception as e:
            logger.warning(f"保存吉祥物位置失败: {e}")
    
    def _on_mascot_clicked(self):
        """吉祥物点击事件"""
        self.mascot_clicked.emit()
    
    def _on_mascot_long_pressed(self):
        """吉祥物长按事件"""
        self.mascot_long_pressed.emit()
    
    def _on_mascot_double_clicked(self):
        """吉祥物双击事件"""
        self.mascot_double_clicked.emit()
    
    def _get_available_screen_geometry(self) -> QRect:
        """获取所有屏幕的总几何范围（支持多显示器和4K屏幕）"""
        screens = QApplication.screens()
        if not screens:
            return QApplication.primaryScreen().availableGeometry()
        
        virtual_geometry = screens[0].availableGeometry()
        for screen in screens[1:]:
            virtual_geometry = virtual_geometry.united(screen.availableGeometry())
        
        return virtual_geometry
    
    def _clamp_position_to_screen(self, pos: QPoint) -> QPoint:
        """将位置限制在屏幕范围内，确保窗口完全可见"""
        screen_geometry = self._get_available_screen_geometry()
        widget_size = self.size()
        
        min_x = screen_geometry.left()
        max_x = screen_geometry.right() - widget_size.width() + 1
        min_y = screen_geometry.top()
        max_y = screen_geometry.bottom() - widget_size.height() + 1
        
        clamped_x = max(min_x, min(max_x, pos.x()))
        clamped_y = max(min_y, min(max_y, pos.y()))
        
        return QPoint(clamped_x, clamped_y)
    
    def mousePressEvent(self, event):
        """鼠标点击事件 - 开始拖拽"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖拽窗口"""
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            clamped_pos = self._clamp_position_to_screen(new_pos)
            self.move(clamped_pos)
            self.position_changed.emit(clamped_pos)
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 结束拖拽"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.save_position()
        super().mouseReleaseEvent(event)
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)
    
    def set_mascot_type(self, mascot_type: MascotType):
        """设置吉祥物类型"""
        if self._mascot_type != mascot_type:
            self._mascot_type = mascot_type
            self._mascot_widget.set_mascot_type(mascot_type)
    
    def set_size(self, size: str):
        """设置大小"""
        if self._size != size:
            self._size = size
            self._mascot_widget.set_size(size)
            self.adjustSize()
    
    def set_state(self, state: MascotState, animate: bool = True):
        """设置状态"""
        self._mascot_widget.set_state(state, animate)
        self.adjustSize()
    
    def show_temp_message(self, message: str, duration: int = 3000, state: MascotState = None):
        """显示临时消息"""
        self._mascot_widget.show_temp_message(message, duration, state)
        self.adjustSize()
    
    def apply_theme(self, theme: str):
        """应用主题"""
        self._mascot_widget.apply_theme(theme)
        self.adjustSize()
    
    def set_message_visible(self, visible: bool):
        """设置消息可见性"""
        self._mascot_widget.set_message_visible(visible)
        self.adjustSize()
    
    def set_animation_enabled(self, enabled: bool):
        """设置动画启用状态"""
        self._mascot_widget.set_animation_enabled(enabled)
    
    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        self.activateWindow()
    
    def hideEvent(self, event):
        """隐藏事件"""
        super().hideEvent(event)
    
    def closeEvent(self, event):
        """关闭事件"""
        self.save_position()
        super().closeEvent(event)
