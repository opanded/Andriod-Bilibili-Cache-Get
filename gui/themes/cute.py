"""萌系主题配色 - 兔蛙绿 + 贝果金"""
from typing import Dict


CUTE_COLORS: Dict[str, str] = {
    "primary": "#98D8C8",
    "secondary": "#FFD93D",
    "background": "#FFF5F8",
    "surface": "#FFFFFF",
    "card": "#FFF0F5",
    "text_primary": "#5D4E60",
    "text_secondary": "#8B7D8B",
    "text_hint": "#B8A9B8",
    "success": "#98D8C8",
    "warning": "#FFD93D",
    "error": "#FF8B94",
    "info": "#A8D8EA",
    "border": "#FFD1DC",
    "divider": "#FFE4E9",
    "accent": "#FFB6C1",
    "accent_dark": "#FF69B4",
}


CUTE_STYLESHEET = """
QMainWindow {
    background-color: #FFF5F8;
}

QWidget {
    background-color: #FFF5F8;
    color: #5D4E60;
    font-size: 13px;
}

QGroupBox {
    border: 2px solid #FFD1DC;
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 14px;
    font-weight: bold;
    color: #5D4E60;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 10px;
    color: #5D4E60;
}

QPushButton {
    background-color: #FFFFFF;
    border: 2px solid #FFD1DC;
    border-radius: 12px;
    padding: 10px 20px;
    color: #5D4E60;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #FFF0F5;
    border-color: #FFB6C1;
}

QPushButton:pressed {
    background-color: #FFE4E9;
}

QPushButton:disabled {
    background-color: #F5F5F5;
    color: #B8A9B8;
    border-color: #E0E0E0;
}

QPushButton#primaryBtn {
    background-color: #98D8C8;
    border: none;
    color: #FFFFFF;
    font-weight: bold;
}

QPushButton#primaryBtn:hover {
    background-color: #7FCDBB;
}

QPushButton#secondaryBtn {
    background-color: #FFD93D;
    border: none;
    color: #5D4E60;
    font-weight: bold;
}

QPushButton#secondaryBtn:hover {
    background-color: #FFC700;
}

QListWidget {
    background-color: #FFFFFF;
    border: 2px solid #FFD1DC;
    border-radius: 12px;
    color: #5D4E60;
}

QListWidget::item {
    padding: 12px;
    border-radius: 8px;
    color: #5D4E60;
}

QListWidget::item:selected {
    background-color: #98D8C8;
    color: #FFFFFF;
}

QListWidget::item:hover {
    background-color: #FFF0F5;
}

QLabel {
    color: #5D4E60;
    background-color: transparent;
}

QLineEdit {
    background-color: #FFFFFF;
    border: 2px solid #FFD1DC;
    border-radius: 12px;
    padding: 8px 14px;
    color: #5D4E60;
}

QLineEdit:focus {
    border-color: #98D8C8;
}

QLineEdit::placeholder {
    color: #B8A9B8;
}

QStatusBar {
    background-color: #FFF0F5;
    border-top: 2px solid #FFD1DC;
    color: #5D4E60;
}

QMenuBar {
    background-color: #FFF0F5;
    color: #5D4E60;
}

QMenuBar::item {
    padding: 8px 14px;
    color: #5D4E60;
}

QMenuBar::item:selected {
    background-color: #FFE4E9;
    border-radius: 6px;
}

QMenu {
    background-color: #FFFFFF;
    border: 2px solid #FFD1DC;
    border-radius: 8px;
    color: #5D4E60;
}

QMenu::item {
    padding: 8px 30px;
    color: #5D4E60;
}

QMenu::item:selected {
    background-color: #98D8C8;
    color: #FFFFFF;
}

QSplitter::handle {
    background-color: #FFD1DC;
}

QScrollBar:vertical {
    background-color: #FFF0F5;
    width: 14px;
    border-radius: 7px;
}

QScrollBar::handle:vertical {
    background-color: #FFD1DC;
    border-radius: 7px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background-color: #FFB6C1;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QProgressBar {
    background-color: #FFF0F5;
    border: 2px solid #FFD1DC;
    border-radius: 8px;
    text-align: center;
    color: #5D4E60;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #98D8C8, stop:0.5 #FFD93D, stop:1 #FFB6C1);
    border-radius: 6px;
}

QCheckBox {
    color: #5D4E60;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #FFD1DC;
    border-radius: 6px;
    background-color: #FFFFFF;
}

QCheckBox::indicator:hover {
    border-color: #98D8C8;
}

QCheckBox::indicator:checked {
    background-color: #98D8C8;
    border-color: #98D8C8;
}

QComboBox {
    background-color: #FFFFFF;
    border: 2px solid #FFD1DC;
    border-radius: 8px;
    padding: 6px 12px;
    color: #5D4E60;
}

QComboBox:hover {
    border-color: #98D8C8;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 2px solid #FFD1DC;
    border-radius: 8px;
    selection-background-color: #98D8C8;
}

QTabWidget::pane {
    border: 2px solid #FFD1DC;
    border-radius: 8px;
    background-color: #FFFFFF;
}

QTabBar::tab {
    background-color: #FFF0F5;
    border: 2px solid #FFD1DC;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 16px;
    color: #5D4E60;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #98D8C8;
    font-weight: bold;
}

QTabBar::tab:hover {
    background-color: #FFE4E9;
}

QSpinBox, QDoubleSpinBox {
    background-color: #FFFFFF;
    border: 2px solid #FFD1DC;
    border-radius: 8px;
    padding: 6px 12px;
    color: #5D4E60;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #98D8C8;
}

QSlider::groove:horizontal {
    background-color: #FFF0F5;
    height: 8px;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background-color: #98D8C8;
    width: 18px;
    height: 18px;
    margin: -5px 0;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background-color: #7FCDBB;
}

QSlider::sub-page:horizontal {
    background-color: #98D8C8;
    border-radius: 4px;
}
"""


def get_cute_stylesheet() -> str:
    """获取萌系主题样式表"""
    return CUTE_STYLESHEET


def get_cute_colors() -> Dict[str, str]:
    """获取萌系主题颜色"""
    return CUTE_COLORS.copy()
