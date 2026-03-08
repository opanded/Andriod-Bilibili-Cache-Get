"""首次使用引导对话框模块"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QWidget, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class WelcomeDialog(QDialog):
    """首次使用引导对话框"""
    
    start_clicked = pyqtSignal(bool)
    
    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self._theme = theme
        self._dont_show_again = False
        self._setup_ui()
        self._apply_theme()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("欢迎使用 B站缓存视频下载工具")
        self.setMinimumSize(520, 480)
        self.setMaximumSize(600, 600)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 20)
        
        title_label = QLabel("ヾ(≧▽≦*)o 欢迎使用！")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("B站缓存视频下载工具 v0.2-GLM5")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setObjectName("subtitleLabel")
        layout.addWidget(subtitle_label)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("separatorLine")
        layout.addWidget(line)
        
        guide_label = QLabel("快速上手指南")
        guide_label.setObjectName("guideLabel")
        layout.addWidget(guide_label)
        
        steps_widget = QWidget()
        steps_layout = QVBoxLayout(steps_widget)
        steps_layout.setSpacing(12)
        steps_layout.setContentsMargins(10, 0, 0, 0)
        
        steps = [
            ("🔌 连接设备", "使用USB连接Android设备，或通过无线调试连接"),
            ("📱 选择设备", "在左侧设备列表中选择已安装B站客户端的设备"),
            ("📺 浏览视频", "自动扫描并显示设备上的B站缓存视频"),
            ("⬇️ 下载视频", "选择需要的视频，点击下载即可保存到本地"),
        ]
        
        for step_title, step_desc in steps:
            step_widget = self._create_step_widget(step_title, step_desc)
            steps_layout.addWidget(step_widget)
        
        layout.addWidget(steps_widget)
        
        tips_label = QLabel("💡 提示：请确保设备已开启USB调试模式，并授权此电脑进行调试")
        tips_label.setObjectName("tipsLabel")
        tips_label.setWordWrap(True)
        layout.addWidget(tips_label)
        
        layout.addStretch()
        
        self.dont_show_check = QCheckBox("不再显示此引导")
        self.dont_show_check.stateChanged.connect(self._on_dont_show_changed)
        layout.addWidget(self.dont_show_check)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        skip_btn = QPushButton("跳过")
        skip_btn.setObjectName("skipBtn")
        skip_btn.clicked.connect(self._on_skip)
        btn_layout.addWidget(skip_btn)
        
        start_btn = QPushButton("开始使用")
        start_btn.setObjectName("startBtn")
        start_btn.setDefault(True)
        start_btn.clicked.connect(self._on_start)
        btn_layout.addWidget(start_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_step_widget(self, title: str, description: str) -> QWidget:
        """创建步骤控件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(title)
        title_label.setObjectName("stepTitle")
        layout.addWidget(title_label)
        
        desc_label = QLabel(f"    {description}")
        desc_label.setObjectName("stepDesc")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        return widget
    
    def _on_dont_show_changed(self, state):
        """不再显示选项改变"""
        self._dont_show_again = state == Qt.CheckState.Checked.value
    
    def _on_skip(self):
        """跳过按钮点击"""
        self.start_clicked.emit(self._dont_show_again)
        self.reject()
    
    def _on_start(self):
        """开始使用按钮点击"""
        self.start_clicked.emit(self._dont_show_again)
        self.accept()
    
    def _apply_theme(self):
        """应用主题"""
        if self._theme == 'light':
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
                font-size: 28px;
                font-weight: bold;
                color: #4CAF50;
            }
            QLabel#subtitleLabel {
                font-size: 14px;
                color: #888888;
                margin-bottom: 10px;
            }
            QLabel#guideLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2196F3;
            }
            QLabel#stepTitle {
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
            }
            QLabel#stepDesc {
                font-size: 12px;
                color: #aaaaaa;
            }
            QLabel#tipsLabel {
                font-size: 12px;
                color: #FF9800;
                padding: 10px;
                background-color: #3d3d3d;
                border-radius: 5px;
            }
            QFrame#separatorLine {
                background-color: #555555;
                max-height: 1px;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 10px 24px;
                color: #ffffff;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            QPushButton:pressed {
                background-color: #5d5d5d;
            }
            QPushButton#startBtn {
                background-color: #4CAF50;
                border: none;
                font-weight: bold;
            }
            QPushButton#startBtn:hover {
                background-color: #45a049;
            }
            QPushButton#skipBtn {
                background-color: transparent;
                border: 1px solid #555;
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
                font-size: 28px;
                font-weight: bold;
                color: #4CAF50;
            }
            QLabel#subtitleLabel {
                font-size: 14px;
                color: #666666;
                margin-bottom: 10px;
            }
            QLabel#guideLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2196F3;
            }
            QLabel#stepTitle {
                font-size: 14px;
                font-weight: bold;
                color: #1a1a1a;
            }
            QLabel#stepDesc {
                font-size: 12px;
                color: #555555;
            }
            QLabel#tipsLabel {
                font-size: 12px;
                color: #E65100;
                padding: 10px;
                background-color: #fff3e0;
                border-radius: 5px;
                border: 1px solid #FFB74D;
            }
            QFrame#separatorLine {
                background-color: #cccccc;
                max-height: 1px;
            }
            QCheckBox {
                color: #1a1a1a;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #888888;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QCheckBox::indicator:hover {
                border-color: #2196F3;
            }
            QCheckBox::indicator:checked {
                background-color: #2196F3;
                border-color: #2196F3;
            }
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                padding: 10px 24px;
                color: #1a1a1a;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e8f4fc;
                border-color: #2196F3;
            }
            QPushButton:pressed {
                background-color: #cce8f7;
            }
            QPushButton#startBtn {
                background-color: #4CAF50;
                border: none;
                color: white;
                font-weight: bold;
            }
            QPushButton#startBtn:hover {
                background-color: #45a049;
            }
            QPushButton#skipBtn {
                background-color: transparent;
            }
        """)
