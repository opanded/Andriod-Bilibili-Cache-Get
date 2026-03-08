"""错误处理模块 - 提供友好的错误消息和统一的错误对话框"""
from enum import Enum
from typing import List, Optional, Tuple
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush


class ErrorType(Enum):
    """错误类型枚举"""
    ADB_CONNECTION = "adb_connection"
    DEVICE_NOT_FOUND = "device_not_found"
    BILIBILI_NOT_INSTALLED = "bilibili_not_installed"
    DISK_SPACE_INSUFFICIENT = "disk_space_insufficient"
    DOWNLOAD_FAILED = "download_failed"
    FILE_TRANSFER_FAILED = "file_transfer_failed"
    VIDEO_MERGE_FAILED = "video_merge_failed"
    PERMISSION_DENIED = "permission_denied"
    NETWORK_ERROR = "network_error"
    FILE_NOT_FOUND = "file_not_found"
    ADB_NOT_INSTALLED = "adb_not_installed"
    USB_DEBUGGING_DISABLED = "usb_debugging_disabled"
    DEVICE_OFFLINE = "device_offline"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """错误信息数据类"""
    title: str
    description: str
    possible_causes: List[str]
    solutions: List[str]
    icon_type: str = "error"
    severity: str = "high"


ERROR_MESSAGES: dict[ErrorType, ErrorInfo] = {
    ErrorType.ADB_CONNECTION: ErrorInfo(
        title="ADB连接失败",
        description="无法与设备建立ADB连接，请检查设备连接状态和ADB配置。",
        possible_causes=[
            "ADB驱动未正确安装",
            "USB数据线损坏或接触不良",
            "设备USB调试未开启",
            "ADB服务未启动或已崩溃",
            "设备授权未通过"
        ],
        solutions=[
            "重新插拔USB数据线，确保连接稳定",
            "检查设备是否弹出授权对话框，点击\"允许\"",
            "在设备上开启USB调试：设置 → 开发者选项 → USB调试",
            "重启ADB服务：在命令行执行 adb kill-server && adb start-server",
            "安装或更新ADB驱动程序",
            "尝试更换USB端口或数据线"
        ],
        icon_type="error",
        severity="high"
    ),
    
    ErrorType.DEVICE_NOT_FOUND: ErrorInfo(
        title="未发现设备",
        description="系统未检测到任何已连接的Android设备。",
        possible_causes=[
            "设备未通过USB连接",
            "USB调试未开启",
            "驱动程序未安装或损坏",
            "USB连接模式不正确（如仅充电模式）",
            "无线调试未开启或IP/端口配置错误"
        ],
        solutions=[
            "确保设备已通过USB连接到电脑",
            "在设备上开启USB调试：设置 → 开发者选项 → USB调试",
            "在设备上选择\"文件传输\"或\"MTP\"模式",
            "安装设备对应的USB驱动程序",
            "如使用无线连接，请确认设备IP地址和端口正确",
            "尝试执行 adb devices 查看设备状态"
        ],
        icon_type="warning",
        severity="medium"
    ),
    
    ErrorType.BILIBILI_NOT_INSTALLED: ErrorInfo(
        title="B站客户端未安装",
        description="当前设备未检测到B站（哔哩哔哩）客户端应用。",
        possible_causes=[
            "设备上未安装B站客户端",
            "B站客户端被冻结或禁用",
            "B站客户端安装在无法访问的分区"
        ],
        solutions=[
            "在设备上安装B站客户端（哔哩哔哩）",
            "从官方应用商店下载最新版本",
            "检查应用是否被禁用：设置 → 应用管理 → 哔哩哔哩",
            "确保B站客户端版本为最新版本"
        ],
        icon_type="info",
        severity="low"
    ),
    
    ErrorType.DISK_SPACE_INSUFFICIENT: ErrorInfo(
        title="磁盘空间不足",
        description="目标存储位置剩余空间不足以完成下载操作。",
        possible_causes=[
            "磁盘剩余空间不足",
            "下载的视频文件较大",
            "临时文件占用大量空间"
        ],
        solutions=[
            "清理磁盘空间，删除不需要的文件",
            "选择其他存储位置进行下载",
            "清空回收站释放空间",
            "使用系统磁盘清理工具",
            "检查并清理临时文件夹"
        ],
        icon_type="warning",
        severity="high"
    ),
    
    ErrorType.DOWNLOAD_FAILED: ErrorInfo(
        title="下载失败",
        description="视频下载过程中发生错误，下载任务未能完成。",
        possible_causes=[
            "设备连接中断",
            "缓存文件损坏或不完整",
            "存储权限被拒绝",
            "目标路径无法访问",
            "网络连接不稳定"
        ],
        solutions=[
            "检查设备连接状态，确保连接稳定",
            "在B站客户端中重新缓存该视频",
            "检查目标文件夹的写入权限",
            "更换下载保存位置",
            "重试下载任务",
            "重启应用程序后重试"
        ],
        icon_type="error",
        severity="high"
    ),
    
    ErrorType.FILE_TRANSFER_FAILED: ErrorInfo(
        title="文件传输失败",
        description="从设备传输文件到电脑时发生错误。",
        possible_causes=[
            "ADB连接不稳定",
            "设备存储空间不足",
            "文件被其他进程占用",
            "传输过程中设备断开",
            "文件权限问题"
        ],
        solutions=[
            "确保设备连接稳定，避免传输过程中断开",
            "检查设备存储空间是否充足",
            "关闭设备上可能占用文件的应用",
            "重新建立ADB连接后重试",
            "检查文件是否存在于设备上"
        ],
        icon_type="error",
        severity="high"
    ),
    
    ErrorType.VIDEO_MERGE_FAILED: ErrorInfo(
        title="视频合并失败",
        description="合并视频和音频文件时发生错误，无法生成最终视频文件。",
        possible_causes=[
            "视频或音频文件损坏",
            "FFmpeg工具未正确配置",
            "输出路径权限不足",
            "磁盘空间不足",
            "文件格式不兼容"
        ],
        solutions=[
            "在B站客户端中重新缓存该视频",
            "检查输出目录的写入权限",
            "确保磁盘有足够的剩余空间",
            "尝试单独下载视频和音频文件",
            "检查FFmpeg是否正确安装",
            "重启应用后重试"
        ],
        icon_type="error",
        severity="high"
    ),
    
    ErrorType.PERMISSION_DENIED: ErrorInfo(
        title="权限被拒绝",
        description="应用程序缺少执行此操作所需的权限。",
        possible_causes=[
            "ADB授权未通过",
            "设备USB调试授权已过期",
            "应用缺少存储访问权限",
            "系统安全策略限制"
        ],
        solutions=[
            "在设备上重新授权USB调试",
            "撤销USB调试授权后重新连接",
            "检查并授予应用必要的权限",
            "在设备上：设置 → 开发者选项 → 撤销USB调试授权，然后重新连接"
        ],
        icon_type="error",
        severity="high"
    ),
    
    ErrorType.NETWORK_ERROR: ErrorInfo(
        title="网络连接错误",
        description="网络连接出现问题，无法完成网络相关操作。",
        possible_causes=[
            "网络连接断开",
            "DNS解析失败",
            "防火墙阻止连接",
            "代理设置问题"
        ],
        solutions=[
            "检查网络连接状态",
            "尝试访问其他网站确认网络正常",
            "检查防火墙设置",
            "检查代理设置是否正确",
            "尝试切换网络连接"
        ],
        icon_type="warning",
        severity="medium"
    ),
    
    ErrorType.FILE_NOT_FOUND: ErrorInfo(
        title="文件未找到",
        description="指定的文件或路径不存在。",
        possible_causes=[
            "文件已被删除或移动",
            "路径输入错误",
            "文件名包含特殊字符",
            "存储设备已移除"
        ],
        solutions=[
            "确认文件是否存在于指定位置",
            "检查文件路径是否正确",
            "刷新文件列表后重试",
            "检查存储设备是否正确连接"
        ],
        icon_type="warning",
        severity="medium"
    ),
    
    ErrorType.ADB_NOT_INSTALLED: ErrorInfo(
        title="ADB未安装",
        description="系统中未检测到ADB（Android Debug Bridge）工具。",
        possible_causes=[
            "ADB工具未安装",
            "ADB未添加到系统环境变量",
            "ADB安装路径配置错误"
        ],
        solutions=[
            "安装Android SDK Platform Tools",
            "将ADB路径添加到系统环境变量PATH中",
            "在应用设置中配置ADB路径",
            "从官方下载ADB工具并解压到指定目录"
        ],
        icon_type="error",
        severity="high"
    ),
    
    ErrorType.USB_DEBUGGING_DISABLED: ErrorInfo(
        title="USB调试未开启",
        description="设备的USB调试功能未启用，无法进行ADB操作。",
        possible_causes=[
            "开发者选项未启用",
            "USB调试开关未打开",
            "系统安全限制"
        ],
        solutions=[
            "启用开发者选项：设置 → 关于手机 → 连续点击版本号7次",
            "开启USB调试：设置 → 开发者选项 → USB调试",
            "部分设备需要同时开启\"USB安装\"选项",
            "重新连接设备并授权"
        ],
        icon_type="info",
        severity="medium"
    ),
    
    ErrorType.DEVICE_OFFLINE: ErrorInfo(
        title="设备离线",
        description="设备已连接但处于离线状态，无法进行操作。",
        possible_causes=[
            "USB调试授权未通过",
            "ADB服务异常",
            "设备系统问题"
        ],
        solutions=[
            "检查设备上是否弹出授权对话框",
            "撤销USB调试授权后重新连接",
            "重启ADB服务：adb kill-server && adb start-server",
            "重新插拔USB连接",
            "重启设备后重试"
        ],
        icon_type="warning",
        severity="medium"
    ),
    
    ErrorType.UNKNOWN: ErrorInfo(
        title="未知错误",
        description="发生了未预期的错误。",
        possible_causes=[
            "系统异常",
            "程序内部错误",
            "资源不足"
        ],
        solutions=[
            "重启应用程序",
            "检查系统资源使用情况",
            "查看日志文件获取详细信息",
            "如问题持续，请联系开发者"
        ],
        icon_type="error",
        severity="high"
    )
}


def get_error_info(error_type: ErrorType) -> ErrorInfo:
    """获取错误信息"""
    return ERROR_MESSAGES.get(error_type, ERROR_MESSAGES[ErrorType.UNKNOWN])


def detect_error_type(error_message: str) -> ErrorType:
    """根据错误消息自动检测错误类型"""
    error_message_lower = error_message.lower()
    
    if "device not found" in error_message_lower or "no devices" in error_message_lower:
        return ErrorType.DEVICE_NOT_FOUND
    elif "offline" in error_message_lower:
        return ErrorType.DEVICE_OFFLINE
    elif "unauthorized" in error_message_lower or "permission denied" in error_message_lower:
        return ErrorType.PERMISSION_DENIED
    elif "cannot connect" in error_message_lower or "connection refused" in error_message_lower:
        return ErrorType.ADB_CONNECTION
    elif "disk" in error_message_lower and ("full" in error_message_lower or "space" in error_message_lower):
        return ErrorType.DISK_SPACE_INSUFFICIENT
    elif "bilibili" in error_message_lower or "未安装" in error_message:
        return ErrorType.BILIBILI_NOT_INSTALLED
    elif "merge" in error_message_lower or "合并" in error_message:
        return ErrorType.VIDEO_MERGE_FAILED
    elif "transfer" in error_message_lower or "传输" in error_message:
        return ErrorType.FILE_TRANSFER_FAILED
    elif "download" in error_message_lower or "下载" in error_message:
        return ErrorType.DOWNLOAD_FAILED
    elif "network" in error_message_lower or "网络" in error_message:
        return ErrorType.NETWORK_ERROR
    elif "not found" in error_message_lower or "未找到" in error_message:
        return ErrorType.FILE_NOT_FOUND
    elif "adb" in error_message_lower and ("not found" in error_message_lower or "未安装" in error_message):
        return ErrorType.ADB_NOT_INSTALLED
    elif "usb debugging" in error_message_lower or "usb调试" in error_message:
        return ErrorType.USB_DEBUGGING_DISABLED
    else:
        return ErrorType.UNKNOWN


class ErrorDialog(QDialog):
    """统一的错误对话框"""
    
    retry_requested = pyqtSignal()
    
    def __init__(
        self,
        error_type: ErrorType,
        parent=None,
        theme: str = "dark",
        show_retry: bool = False,
        custom_message: str = None
    ):
        super().__init__(parent)
        self._error_type = error_type
        self._theme = theme
        self._show_retry = show_retry
        self._custom_message = custom_message
        self._error_info = get_error_info(error_type)
        
        self._init_ui()
        self._apply_theme()
    
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle(self._error_info.title)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header_layout = QHBoxLayout()
        
        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        icon_pixmap = self._create_icon()
        icon_label.setPixmap(icon_pixmap)
        header_layout.addWidget(icon_label)
        
        title_layout = QVBoxLayout()
        
        title_label = QLabel(self._error_info.title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        severity_label = QLabel(f"严重程度: {self._get_severity_text()}")
        severity_label.setStyleSheet(f"font-size: 12px; color: {self._get_severity_color()};")
        title_layout.addWidget(severity_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        desc_label = QLabel("问题描述")
        desc_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #888;")
        layout.addWidget(desc_label)
        
        description = self._custom_message or self._error_info.description
        desc_text = QLabel(description)
        desc_text.setWordWrap(True)
        desc_text.setStyleSheet("font-size: 13px; padding: 5px;")
        layout.addWidget(desc_text)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setMinimumHeight(200)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(15)
        
        causes_label = QLabel("可能的原因")
        causes_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFA726;")
        scroll_layout.addWidget(causes_label)
        
        for i, cause in enumerate(self._error_info.possible_causes, 1):
            cause_item = QLabel(f"  {i}. {cause}")
            cause_item.setWordWrap(True)
            cause_item.setStyleSheet("font-size: 12px; padding: 2px;")
            scroll_layout.addWidget(cause_item)
        
        scroll_layout.addSpacing(10)
        
        solutions_label = QLabel("建议的解决方案")
        solutions_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50;")
        scroll_layout.addWidget(solutions_label)
        
        for i, solution in enumerate(self._error_info.solutions, 1):
            solution_item = QLabel(f"  {i}. {solution}")
            solution_item.setWordWrap(True)
            solution_item.setStyleSheet("font-size: 12px; padding: 2px;")
            scroll_layout.addWidget(solution_item)
        
        scroll_layout.addStretch()
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        if self._show_retry:
            self.retry_btn = QPushButton("重试")
            self.retry_btn.setFixedWidth(80)
            self.retry_btn.clicked.connect(self._on_retry)
            btn_layout.addWidget(self.retry_btn)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.setFixedWidth(80)
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def _create_icon(self) -> QPixmap:
        """创建错误图标"""
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        icon_type = self._error_info.icon_type
        
        if icon_type == "error":
            bg_color = QColor("#f44336")
            symbol = "✕"
        elif icon_type == "warning":
            bg_color = QColor("#FF9800")
            symbol = "!"
        else:
            bg_color = QColor("#2196F3")
            symbol = "i"
        
        painter.setPen(QPen(bg_color, 2))
        painter.setBrush(QBrush(bg_color))
        painter.drawEllipse(4, 4, 40, 40)
        
        painter.setPen(QColor("#ffffff"))
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(4, 4, 40, 40, Qt.AlignmentFlag.AlignCenter, symbol)
        
        painter.end()
        return pixmap
    
    def _get_severity_text(self) -> str:
        """获取严重程度文本"""
        severity_map = {
            "high": "高 - 需要立即处理",
            "medium": "中 - 建议尽快处理",
            "low": "低 - 可稍后处理"
        }
        return severity_map.get(self._error_info.severity, "未知")
    
    def _get_severity_color(self) -> str:
        """获取严重程度颜色"""
        color_map = {
            "high": "#f44336",
            "medium": "#FF9800",
            "low": "#4CAF50"
        }
        return color_map.get(self._error_info.severity, "#888888")
    
    def _apply_theme(self):
        """应用主题"""
        if self._theme == 'light':
            self._apply_light_theme()
        else:
            self._apply_dark_theme()
    
    def _apply_dark_theme(self):
        """应用深色主题"""
        self.setStyleSheet("""
            ErrorDialog {
                background-color: #2d2d2d;
            }
            QLabel {
                color: #ffffff;
            }
            QScrollArea {
                background-color: #353535;
                border: 1px solid #444;
                border-radius: 5px;
            }
            QWidget {
                background-color: transparent;
            }
            QFrame {
                background-color: #444;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px 16px;
                color: #ffffff;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            QPushButton:pressed {
                background-color: #5d5d5d;
            }
        """)
    
    def _apply_light_theme(self):
        """应用浅色主题"""
        self.setStyleSheet("""
            ErrorDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #1a1a1a;
            }
            QScrollArea {
                background-color: #ffffff;
                border: 2px solid #e0e0e0;
                border-radius: 5px;
            }
            QWidget {
                background-color: transparent;
            }
            QFrame {
                background-color: #e0e0e0;
            }
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                padding: 8px 16px;
                color: #1a1a1a;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e8f4fc;
                border-color: #2196F3;
            }
            QPushButton:pressed {
                background-color: #cce8f7;
            }
        """)
    
    def _on_retry(self):
        """重试按钮点击"""
        self.retry_requested.emit()
        self.accept()


def show_error_dialog(
    error_type: ErrorType,
    parent=None,
    theme: str = "dark",
    show_retry: bool = False,
    custom_message: str = None
) -> Tuple[bool, bool]:
    """显示错误对话框的便捷函数
    
    Args:
        error_type: 错误类型
        parent: 父窗口
        theme: 主题
        show_retry: 是否显示重试按钮
        custom_message: 自定义错误消息
    
    Returns:
        (accepted, retry_requested): 是否接受，是否请求重试
    """
    dialog = ErrorDialog(error_type, parent, theme, show_retry, custom_message)
    retry_requested = False
    
    def on_retry():
        nonlocal retry_requested
        retry_requested = True
    
    dialog.retry_requested.connect(on_retry)
    result = dialog.exec()
    
    return result == QDialog.DialogCode.Accepted, retry_requested


def show_error_from_message(
    error_message: str,
    parent=None,
    theme: str = "dark",
    show_retry: bool = False
) -> Tuple[bool, bool]:
    """根据错误消息显示错误对话框
    
    Args:
        error_message: 错误消息
        parent: 父窗口
        theme: 主题
        show_retry: 是否显示重试按钮
    
    Returns:
        (accepted, retry_requested): 是否接受，是否请求重试
    """
    error_type = detect_error_type(error_message)
    return show_error_dialog(error_type, parent, theme, show_retry, error_message)


class ErrorHandler:
    """错误处理器 - 提供统一的错误处理接口"""
    
    def __init__(self, parent=None, theme: str = "dark"):
        self._parent = parent
        self._theme = theme
    
    def set_parent(self, parent):
        """设置父窗口"""
        self._parent = parent
    
    def set_theme(self, theme: str):
        """设置主题"""
        self._theme = theme
    
    def show_error(
        self,
        error_type: ErrorType,
        custom_message: str = None,
        show_retry: bool = False
    ) -> Tuple[bool, bool]:
        """显示错误对话框
        
        Args:
            error_type: 错误类型
            custom_message: 自定义错误消息
            show_retry: 是否显示重试按钮
        
        Returns:
            (accepted, retry_requested): 是否接受，是否请求重试
        """
        return show_error_dialog(
            error_type,
            self._parent,
            self._theme,
            show_retry,
            custom_message
        )
    
    def show_error_from_message(
        self,
        error_message: str,
        show_retry: bool = False
    ) -> Tuple[bool, bool]:
        """根据错误消息显示错误对话框
        
        Args:
            error_message: 错误消息
            show_retry: 是否显示重试按钮
        
        Returns:
            (accepted, retry_requested): 是否接受，是否请求重试
        """
        return show_error_from_message(
            error_message,
            self._parent,
            self._theme,
            show_retry
        )
    
    def handle_exception(
        self,
        exception: Exception,
        show_retry: bool = False
    ) -> Tuple[bool, bool]:
        """处理异常
        
        Args:
            exception: 异常对象
            show_retry: 是否显示重试按钮
        
        Returns:
            (accepted, retry_requested): 是否接受，是否请求重试
        """
        error_message = str(exception)
        return self.show_error_from_message(error_message, show_retry)
