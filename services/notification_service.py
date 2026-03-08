"""系统通知服务模块

提供跨平台的系统通知功能。
Windows 使用原生 Toast 通知，Linux/Mac 使用系统通知服务。
"""
import platform
import logging
import subprocess
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class NotificationService:
    """系统通知服务"""

    def __init__(self):
        self._enabled = True
        self._tray_icon = None

    def set_tray_icon(self, tray_icon):
        """设置系统托盘图标用于显示通知"""
        self._tray_icon = tray_icon

    def notify(self, title: str, message: str, icon_path: str = None):
        """发送系统通知

        Args:
            title: 通知标题
            message: 通知内容
            icon_path: 图标路径（可选）
        """
        if not self._enabled:
            logger.debug("通知已禁用，跳过发送")
            return

        try:
            if self._tray_icon and self._tray_icon.isVisible():
                from PyQt6.QtWidgets import QSystemTrayIcon
                from PyQt6.QtGui import QPixmap, QIcon

                icon = QSystemTrayIcon.MessageIcon.Information
                if icon_path and Path(icon_path).exists():
                    pixmap = QPixmap(icon_path)
                    if not pixmap.isNull():
                        pass

                self._tray_icon.showMessage(
                    title,
                    message,
                    icon,
                    5000
                )
                logger.debug(f"已通过系统托盘发送通知: {title}")
            else:
                self._send_native_notification(title, message, icon_path)

        except Exception as e:
            logger.error(f"通知发送失败: {e}")

    def _send_native_notification(self, title: str, message: str, icon_path: str = None):
        """发送原生系统通知"""
        try:
            system = platform.system()

            if system == 'Windows':
                self._send_windows_notification(title, message, icon_path)
            elif system == 'Darwin':
                self._send_macos_notification(title, message)
            elif system == 'Linux':
                self._send_linux_notification(title, message, icon_path)
            else:
                logger.warning(f"不支持的操作系统: {system}")

        except Exception as e:
            logger.error(f"原生通知发送失败: {e}")

    def _send_windows_notification(self, title: str, message: str, icon_path: str = None):
        """Windows 系统通知"""
        try:
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(
                    title,
                    message,
                    icon_path=icon_path,
                    duration=5,
                    threaded=True
                )
                logger.debug("已通过 win10toast 发送通知")
                return
            except ImportError:
                pass

            try:
                from win11toast import toast
                toast(title, message)
                logger.debug("已通过 win11toast 发送通知")
                return
            except ImportError:
                pass

            self._send_powershell_notification(title, message)

        except Exception as e:
            logger.warning(f"Windows 通知发送失败: {e}")

    def _send_powershell_notification(self, title: str, message: str):
        """使用 PowerShell 发送 Windows 通知"""
        try:
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

            $template = @"
            <toast>
                <visual>
                    <binding template="ToastText02">
                        <text id="1">{title}</text>
                        <text id="2">{message}</text>
                    </binding>
                </visual>
            </toast>
"@

            $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
            $xml.LoadXml($template)
            $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("B站缓存下载工具").Show($toast)
            '''

            subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            logger.debug("已通过 PowerShell 发送 Windows Toast 通知")

        except Exception as e:
            logger.warning(f"PowerShell 通知发送失败: {e}")

    def _send_macos_notification(self, title: str, message: str):
        """macOS 系统通知"""
        try:
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(['osascript', '-e', script], check=True, timeout=10)
            logger.debug("已发送 macOS 通知")
        except Exception as e:
            logger.warning(f"macOS 通知发送失败: {e}")

    def _send_linux_notification(self, title: str, message: str, icon_path: str = None):
        """Linux 系统通知 (notify-send)"""
        try:
            cmd = ['notify-send', title, message]
            if icon_path and Path(icon_path).exists():
                cmd.extend(['--icon', icon_path])
            subprocess.run(cmd, check=True, timeout=10)
            logger.debug("已发送 Linux notify-send 通知")
        except FileNotFoundError:
            logger.warning("notify-send 未安装，无法发送通知")
        except Exception as e:
            logger.warning(f"Linux 通知发送失败: {e}")

    def set_enabled(self, enabled: bool):
        """启用/禁用通知

        Args:
            enabled: True 启用，False 禁用
        """
        self._enabled = enabled
        logger.info(f"通知服务已{'启用' if enabled else '禁用'}")

    def is_enabled(self) -> bool:
        """检查通知是否启用"""
        return self._enabled

    def notify_download_completed(self, video_title: str, file_path: str = None):
        """发送下载完成通知

        Args:
            video_title: 视频标题
            file_path: 文件路径（可选）
        """
        message = f"《{video_title}》下载完成"
        if file_path:
            message += f"\n保存至: {file_path}"
        self.notify("下载完成", message)

    def notify_download_failed(self, video_title: str, error_message: str = None):
        """发送下载失败通知

        Args:
            video_title: 视频标题
            error_message: 错误信息（可选）
        """
        message = f"《{video_title}》下载失败"
        if error_message:
            message += f"\n原因: {error_message}"
        self.notify("下载失败", message)

    def notify_batch_completed(self, success_count: int, failed_count: int = 0):
        """发送批量下载完成通知

        Args:
            success_count: 成功数量
            failed_count: 失败数量
        """
        if failed_count > 0:
            message = f"成功: {success_count} 个，失败: {failed_count} 个"
        else:
            message = f"全部 {success_count} 个视频下载完成"
        self.notify("批量下载完成", message)
