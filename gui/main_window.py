"""主窗口模块 - 优化性能版本"""
import sys
import os
import time
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from queue import Queue
from threading import Thread

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QFileDialog, QMessageBox,
    QSplitter, QStatusBar, QMenuBar, QMenu, QApplication, QSystemTrayIcon,
    QTabWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QObject, pyqtSlot
from PyQt6.QtGui import QPixmap, QColor, QFont, QAction, QIcon, QPainter, QPen, QBrush, QKeySequence, QShortcut

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import Config
from src.utils.logger import setup_logger
from src.utils.i18n import TranslationManager, tr
from src.models.database import Database
from src.models.settings import UserSettings
from src.services.adb_service import ADBService
from src.services.cache_parser import CacheParser
from src.services.cover_cache import CoverCacheService
from src.services.settings_service import SettingsService
from src.services.backup_service import BackupService
from src.services.notification_service import NotificationService
from src.core.container import ServiceContainer
from src.core.device_manager import DeviceManager
from src.core.video_manager import VideoManager
from src.core.file_transfer import FileTransfer
from src.core.state import StateManager, StateKey, DownloadTaskState
from src.models.device import Device
from src.models.video import Video
from src.interfaces import DownloadStatus, DownloadRequest
from src.gui.panels import DevicePanel, VideoPanel, DownloadPanel
from src.gui.dialogs import WirelessConnectDialog, SettingsDialog, BackupDialog, DownloadHistoryDialog, WelcomeDialog, ShortcutHelpDialog
from src.gui.components.mascot import MascotWidget, MascotState, MascotType, MascotMessageHelper
from src.gui.components.mascot.floating_mascot import FloatingMascot
from src.gui.dialogs.about_dialog import AboutDialog
from src.gui.themes import get_cute_stylesheet
from src.gui.utils.achievements import AchievementManager
from src.gui.components.achievement_notification import AchievementNotificationManager


class EventBridge(QObject):
    """事件桥接器 - 使用信号实现线程安全通信"""
    event_received = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()


class EventPublisher:
    """事件发布器 - 线程安全"""
    def __init__(self, bridge: EventBridge):
        self.bridge = bridge

    def publish(self, event_type: str, data):
        self.bridge.event_received.emit(event_type, data)


class CoverLoader(QThread):
    """封面加载线程 - 异步加载封面避免UI卡顿"""
    cover_loaded = pyqtSignal(str, QPixmap)
    cover_failed = pyqtSignal(str)

    def __init__(self, cover_cache, adb_service, queue):
        super().__init__()
        self.cover_cache = cover_cache
        self.adb_service = adb_service
        self.queue = queue
        self._running = True

    def run(self):
        while self._running:
            try:
                item = self.queue.get(timeout=0.5)
                if item is None:
                    continue

                video_id, cover_path, device_id = item

                try:
                    if cover_path:
                        if cover_path.startswith('http'):
                            local_path = self.cover_cache.download_cover(video_id, cover_path)
                        else:
                            import tempfile
                            temp_dir = Path(tempfile.gettempdir()) / "bili_covers_v02"
                            temp_dir.mkdir(parents=True, exist_ok=True)
                            local_path = temp_dir / f"{video_id}_cover.jpg"
                            if not local_path.exists():
                                self.adb_service.pull_file(device_id, cover_path, str(local_path))

                        if local_path and local_path.exists():
                            pixmap = QPixmap(str(local_path))
                            if not pixmap.isNull():
                                scaled = pixmap.scaled(
                                    120, 68,
                                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                    Qt.TransformationMode.SmoothTransformation
                                )
                                self.cover_loaded.emit(video_id, scaled)
                                continue

                    self.cover_failed.emit(video_id)
                except Exception as e:
                    self.cover_failed.emit(video_id)

            except:
                pass

    def stop(self):
        self._running = False
        self.wait()


class VideoLoadWorker(QThread):
    """视频加载工作线程"""
    progress = pyqtSignal(str, int)
    completed = pyqtSignal(list, int)
    error = pyqtSignal(str, int)

    def __init__(self, cache_parser, device_id, request_id: int, db=None):
        super().__init__()
        self.cache_parser = cache_parser
        self.device_id = device_id
        self.request_id = request_id
        self.db = db
        self._is_running = True

    def run(self):
        try:
            self.progress.emit("正在扫描缓存视频...", self.request_id)

            with self.db.session() as session:
                videos = self.cache_parser.get_cached_videos(self.device_id, session)

            if self._is_running:
                self.progress.emit(f"找到 {len(videos)} 个视频", self.request_id)
                self.completed.emit(videos, self.request_id)

        except Exception as e:
            if self._is_running:
                self.error.emit(str(e), self.request_id)

    def stop(self):
        self._is_running = False
        self.wait(1000)


from src.gui.utils.kaomoji import KaomojiHelper


class MainWindow(QMainWindow):
    """主窗口 - 优化性能版本"""

    video_status_updated = pyqtSignal(str, str, str, str, str)

    def __init__(self):
        super().__init__()
        
        self.state_manager = StateManager.get_instance()

        self.config = Config()
        self.config.ensure_directories()

        self.settings_service = SettingsService(self.config.DATA_DIR)
        self.user_settings = self.settings_service.get()
        
        TranslationManager.get_instance().load_language(self.user_settings.language)

        self.logger = setup_logger('gui', self.config)

        self.db = Database(str(self.config.DATABASE_PATH))
        self.db.create_tables()

        self.adb_service = ADBService(str(Config.get_adb_path()))
        
        self.event_bridge = EventBridge()
        self.event_publisher = EventPublisher(self.event_bridge)
        self.event_bridge.event_received.connect(self.handle_event)

        self.device_manager = DeviceManager(
            self.config, self.adb_service, self.event_publisher, self.db
        )
        
        self.notification_service = NotificationService()
        self.notification_service.set_enabled(self.user_settings.enable_notification)
        
        self.video_manager = VideoManager(
            self.config, self.device_manager, self.adb_service,
            self.event_publisher, self.db
        )
        self.file_transfer = FileTransfer(
            self.config, self.device_manager, self.adb_service,
            self.event_publisher, self.db, self.notification_service
        )

        self.cache_parser = CacheParser(self.adb_service, self.config.BILI_CACHE_PATH)
        self.cover_cache = CoverCacheService(self.config.COVER_CACHE_DIR)
        
        self.backup_service = BackupService(self.db, self.settings_service)

        self.container = ServiceContainer()
        self.container.register('config', self.config)
        self.container.register('adb_service', self.adb_service)
        self.container.register('device_manager', self.device_manager)
        self.container.register('video_manager', self.video_manager)
        self.container.register('file_transfer', self.file_transfer)
        self.container.register('db', self.db)
        self.container.register('settings_service', self.settings_service)
        self.container.register('cache_parser', self.cache_parser)
        self.container.register('cover_cache', self.cover_cache)
        self.container.register('event_publisher', self.event_publisher)
        self.container.register('state_manager', self.state_manager)
        self.container.register('logger', self.logger)
        self.container.register('notification_service', self.notification_service)

        self._video_load_worker: Optional[VideoLoadWorker] = None
        self._current_load_request_id: int = 0

        self._video_cache: Dict[str, list] = {}
        self._video_cache_time: Dict[str, float] = {}
        self._video_cache_ttl: int = 300

        self._task_video_map: Dict[str, str] = {}

        self._cover_queue = Queue()
        self._cover_loader = CoverLoader(self.cover_cache, self.adb_service, self._cover_queue)
        self._cover_loader.cover_loaded.connect(self._on_cover_loaded)
        self._cover_loader.cover_failed.connect(self._on_cover_failed)
        self._cover_loader.start()

        self.video_status_updated.connect(self._on_video_status_updated)
        
        self._setup_state_subscriptions()

        self.init_ui()
        
        self._restore_window_state()

        self.device_manager.start_monitoring()

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_devices)
        self.refresh_timer.start(5000)

        self.video_refresh_timer = QTimer()
        self.video_refresh_timer.timeout.connect(self._auto_refresh_videos)
        if self.user_settings.auto_refresh:
            interval = getattr(self.user_settings, 'refresh_interval', 30) * 1000
            self.video_refresh_timer.start(interval)

        self.video_panel.show_empty_guide("no_device")
        self.refresh_devices()
        
        self._restore_download_tasks()
        
        self._consistency_timer = QTimer(self)
        self._consistency_timer.timeout.connect(self._check_status_consistency)
        self._consistency_timer.start(30000)
        
        self._achievement_manager = AchievementManager()
        self._achievement_notification_manager = AchievementNotificationManager(self)
        
        self._init_system_tray()
        
        QTimer.singleShot(500, self._check_and_show_welcome)
        QTimer.singleShot(1000, self._check_first_launch)
    
    def _init_system_tray(self):
        """初始化系统托盘"""
        self._tray_icon = QSystemTrayIcon(self)
        self._tray_icon.setIcon(self._create_tray_icon())
        self._tray_icon.setToolTip("B站缓存视频下载工具")
        
        self._tray_menu = QMenu(self)
        self._tray_menu.setStyleSheet("""
            QMenu {
                background-color: #3d3d3d;
                border: 1px solid #555;
                color: #ffffff;
            }
            QMenu::item {
                padding: 8px 20px;
            }
            QMenu::item:selected {
                background-color: #2196F3;
            }
        """)
        
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self._show_window)
        self._tray_menu.addAction(show_action)
        
        hide_action = QAction("隐藏主窗口", self)
        hide_action.triggered.connect(self.hide)
        self._tray_menu.addAction(hide_action)
        
        self._tray_menu.addSeparator()
        
        history_action = QAction("查看下载历史", self)
        history_action.triggered.connect(self._show_download_history)
        self._tray_menu.addAction(history_action)
        
        self._tray_menu.addSeparator()
        
        quit_action = QAction("退出程序", self)
        quit_action.triggered.connect(self._quit_app)
        self._tray_menu.addAction(quit_action)
        
        self._tray_icon.setContextMenu(self._tray_menu)
        self._tray_icon.activated.connect(self._on_tray_activated)
        self._tray_icon.messageClicked.connect(self._show_window)
        self._tray_icon.show()
        
        self._download_progress_text = ""
    
    def _create_tray_icon(self) -> QIcon:
        """创建托盘图标"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setPen(QPen(QColor("#4CAF50"), 3))
        painter.setBrush(QBrush(QColor("#4CAF50")))
        painter.drawEllipse(8, 8, 48, 48)
        
        painter.setPen(QPen(QColor("#ffffff"), 4))
        painter.drawLine(20, 32, 32, 44)
        painter.drawLine(32, 44, 48, 20)
        
        painter.end()
        
        return QIcon(pixmap)
    
    def _create_progress_icon(self, progress: int) -> QIcon:
        """创建带进度的托盘图标"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(QColor("#3d3d3d"), 4)
        painter.setPen(pen)
        painter.drawEllipse(8, 8, 48, 48)
        
        pen = QPen(QColor("#4CAF50"), 4)
        painter.setPen(pen)
        
        span_angle = int(-360 * progress / 100 * 16)
        painter.drawArc(8, 8, 48, 48, 90 * 16, span_angle)
        
        painter.setPen(QColor("#ffffff"))
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(8, 8, 48, 48, Qt.AlignmentFlag.AlignCenter, f"{progress}%")
        
        painter.end()
        
        return QIcon(pixmap)
    
    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()
        elif reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            self._show_download_history()
    
    def _show_window(self):
        """显示窗口"""
        self.show()
        self.activateWindow()
        self.raise_()
    
    def _quit_app(self):
        """退出应用"""
        self._force_quit = True
        self.close()
    
    def _check_and_show_welcome(self):
        """检查并显示欢迎对话框"""
        if self.settings_service.is_first_run():
            dialog = WelcomeDialog(self, theme=self.user_settings.theme)
            dialog.start_clicked.connect(self._on_welcome_closed)
            dialog.exec()
    
    def _on_welcome_closed(self, dont_show_again: bool):
        """欢迎对话框关闭回调"""
        self.settings_service.set_welcome_shown(dont_show_again)
    
    def _check_first_launch(self):
        """检查首次启动成就"""
        unlocked = self._achievement_manager.on_first_launch()
        if unlocked:
            self._achievement_notification_manager.show_achievements(unlocked)
    
    def _setup_state_subscriptions(self):
        """设置状态订阅"""
        self.state_manager.subscribe_strong(StateKey.CURRENT_DEVICE, self._on_current_device_changed)
        self.state_manager.subscribe_strong(StateKey.DEVICES, self._on_devices_changed)
        self.state_manager.subscribe_strong(StateKey.VIDEOS, self._on_videos_changed)
        self.state_manager.subscribe_strong(StateKey.SELECTED_VIDEOS, self._on_selected_videos_changed)
        self.state_manager.subscribe_strong(StateKey.DOWNLOAD_TASKS, self._on_download_tasks_changed)
        self.state_manager.subscribe_strong(StateKey.SEARCH_FILTER, self._on_search_filter_changed)
    
    def _check_status_consistency(self):
        """检查下载状态一致性"""
        if not self.file_transfer:
            return
        
        download_panel_tasks = self.download_panel.get_task_count() if self.download_panel else 0
        
        active_tasks = self.file_transfer.get_active_tasks()
        failed_tasks = self.file_transfer.get_failed_tasks()
        
        for video in self.current_videos:
            video_id = video.video_id
            if video.download_status in [DownloadStatus.DOWNLOADING.value, DownloadStatus.QUEUED.value]:
                task_found = False
                for task_id in active_tasks:
                    if self._task_video_map.get(task_id) == video_id:
                        task_found = True
                        break
                
                if not task_found:
                    self.logger.warning(f"检测到状态不一致: 视频 {video_id} 显示{video.download_status}，但没有活动任务")
                    video.download_status = DownloadStatus.NOT_DOWNLOADED.value
                    self._refresh_video_row(video_id)
        
        self.logger.debug("状态一致性检查完成")
    
    def _on_current_device_changed(self, key: StateKey, device):
        """当前设备变更回调"""
        pass
    
    def _on_devices_changed(self, key: StateKey, devices):
        """设备列表变更回调"""
        self.device_panel.set_devices(devices)
        
        if not hasattr(self, '_last_device_count'):
            self._last_device_count = 0
        
        current_count = len(devices) if devices else 0
        
        if not devices:
            self.video_panel.show_empty_guide("no_device")
            self.status_bar.showMessage("未发现设备，请检查连接")
        else:
            self.status_bar.showMessage(f"发现 {current_count} 个在线设备")
            
            if current_count > self._last_device_count:
                msg, state = MascotMessageHelper.device_found(current_count)
                self._show_mascot_message(msg, state=state)
        
        self._last_device_count = current_count
    
    def _on_videos_changed(self, key: StateKey, videos):
        """视频列表变更回调"""
        pass
    
    def _on_selected_videos_changed(self, key: StateKey, selected_videos):
        """选中视频变更回调"""
        self.video_panel.set_download_enabled(len(selected_videos) > 0)
    
    def _on_download_tasks_changed(self, key: StateKey, tasks):
        """下载任务变更回调"""
        pass
    
    def _on_search_filter_changed(self, key: StateKey, search_filter):
        """搜索过滤器变更回调"""
        pass
    
    @property
    def current_device(self) -> Optional[Device]:
        """获取当前设备"""
        return self.state_manager.get(StateKey.CURRENT_DEVICE)
    
    @current_device.setter
    def current_device(self, value: Optional[Device]):
        """设置当前设备"""
        self.state_manager.set(StateKey.CURRENT_DEVICE, value)
    
    @property
    def current_videos(self) -> List[Video]:
        """获取当前视频列表"""
        return self.state_manager.get(StateKey.VIDEOS) or []
    
    @current_videos.setter
    def current_videos(self, value: List[Video]):
        """设置当前视频列表"""
        self.state_manager.set(StateKey.VIDEOS, value)
    
    @property
    def selected_videos(self) -> set:
        """获取选中的视频"""
        return self.state_manager.get(StateKey.SELECTED_VIDEOS) or set()
    
    @selected_videos.setter
    def selected_videos(self, value: set):
        """设置选中的视频"""
        self.state_manager.set(StateKey.SELECTED_VIDEOS, value)

    def get_service(self, name: str) -> Any:
        """通过容器获取服务实例"""
        return self.container.get(name)

    def has_service(self, name: str) -> bool:
        """检查服务是否已注册"""
        return self.container.has(name)

    def _on_cover_loaded(self, video_id: str, pixmap: QPixmap):
        """封面加载完成 - 在主线程执行"""
        self.video_panel.update_cover(video_id, pixmap)

    def _on_cover_failed(self, video_id: str):
        """封面加载失败"""
        pass

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("B站缓存视频下载工具 v2.1 萌化版  |  🐰🐸 OPandED君 x 🥯🍳 物语系列圈 x 墨汁乌鸫")
        self.setGeometry(100, 100, 1280, 850)

        self.create_menu_bar()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(KaomojiHelper.random('WELCOME'))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        self.device_panel = DevicePanel(theme=self.user_settings.theme)
        self.device_panel.refresh_requested.connect(self.refresh_devices)
        self.device_panel.device_selected.connect(self.on_device_selected)
        self.device_panel.wireless_connect_requested.connect(self._on_wireless_connect_requested)
        splitter.addWidget(self.device_panel)

        self.video_panel = VideoPanel()
        if self.user_settings.download_dir:
            self.video_panel.set_download_dir(self.user_settings.download_dir)
        else:
            self.video_panel.set_download_dir(str(self.config.DOWNLOAD_DIR))
        self._connect_video_panel_signals()
        splitter.addWidget(self.video_panel)

        self.download_panel = DownloadPanel(theme=self.user_settings.theme)
        self.download_panel.set_database(self.db)
        self.download_panel.cancel_task.connect(self._on_cancel_task_requested)
        self.download_panel.retry_failed.connect(self._retry_failed_downloads)
        self.download_panel.open_file_requested.connect(self.open_video_file)
        self.download_panel.open_folder_requested.connect(self._open_file_location)
        self.download_panel.delete_history_requested.connect(self._delete_history_record)
        splitter.addWidget(self.download_panel)

        splitter.setSizes([280, 700, 300])

        self._setup_mascot()
        self._setup_shortcuts()
        self._apply_dark_theme()
    
    def _setup_mascot(self):
        """设置吉祥物"""
        if not getattr(self.user_settings, 'show_mascot', True):
            return
        
        mascot_type_str = getattr(self.user_settings, 'mascot_type', 'rabbit_frog')
        mascot_type = MascotType.RABBIT_FROG if mascot_type_str == 'rabbit_frog' else MascotType.DONUT
        mascot_size = getattr(self.user_settings, 'mascot_size', 'medium')
        
        self.mascot = FloatingMascot(mascot_type=mascot_type, size=mascot_size)
        self.mascot.mascot_clicked.connect(self._on_mascot_clicked)
        
        if hasattr(self.mascot, 'mascot_long_pressed'):
            self.mascot.mascot_long_pressed.connect(self._on_mascot_long_pressed)
        if hasattr(self.mascot, 'mascot_double_clicked'):
            self.mascot.mascot_double_clicked.connect(self._on_mascot_double_clicked)
        
        idle_actions = getattr(self.user_settings, 'mascot_idle_actions', True)
        
        self.mascot.show()
        self.mascot.apply_theme(self.user_settings.theme)
    
    def _show_mascot_message(self, message: str, duration: int = 3000, state: MascotState = None):
        """通过吉祥物显示临时消息
        
        Args:
            message: 消息内容
            duration: 显示时长(毫秒)，默认3秒
            state: 吉祥物状态，None则保持当前状态
        """
        if hasattr(self, 'mascot') and self.mascot:
            self.mascot.show_temp_message(message, duration, state)
    
    def _on_mascot_clicked(self):
        """吉祥物点击事件"""
        unlocked = self._achievement_manager.on_mascot_click()
        if unlocked:
            self._achievement_notification_manager.show_achievements(unlocked)
    
    def _on_mascot_long_pressed(self):
        """吉祥物长按事件"""
        self._achievement_manager.unlock_achievement('hidden_egg_finder')
        if hasattr(self, 'mascot'):
            self.mascot.show_temp_message("发现隐藏彩蛋啦！(◕‿◕✿)", 3000)
    
    def _on_mascot_double_clicked(self):
        """吉祥物双击事件"""
        if hasattr(self, 'mascot'):
            self.mascot.show_temp_message("🎉 好开心！", 2000)
    
    def _is_working(self) -> bool:
        """检查是否处于工作状态"""
        if not self.file_transfer:
            return False
        active_tasks = self.file_transfer.get_active_tasks()
        return len(active_tasks) > 0
    
    def _explain_element(self, element_type: str, widget_name: str = None):
        """解释UI元素
        
        Args:
            element_type: 元素类型
            widget_name: 控件名称（可选）
        """
        if self._is_working():
            return
        
        from src.gui.components.mascot.mascot_states import UI_ELEMENT_DESCRIPTIONS, MascotState
        import random
        
        element_info = UI_ELEMENT_DESCRIPTIONS.get(element_type, {})
        if not element_info:
            return
        
        title = element_info.get('title', '')
        desc = element_info.get('desc', '')
        tip = element_info.get('tip', '')
        
        messages = [
            f"💡 这是「{title}」\n{desc}",
            f"💡 {title}\n{desc}",
        ]
        
        message = random.choice(messages)
        if tip and random.random() > 0.5:
            message += f"\n{tip}"
        
        if hasattr(self, 'mascot'):
            self.mascot.show_temp_message(message, 4000, MascotState.THINKING)
    
    def _on_video_clicked(self, video):
        """视频点击事件 - 显示视频信息"""
        if self._is_working():
            return
        
        from src.gui.components.mascot.mascot_states import MascotState
        import os
        
        title_short = video.title[:25] + "..." if len(video.title) > 25 else video.title
        
        if video.download_status == DownloadStatus.COMPLETED.value:
            if video.local_path and os.path.exists(video.local_path):
                folder = os.path.dirname(video.local_path)
                message = f"✅ 「{title_short}」\n已下载完成！\n📁 点击可打开文件夹"
            else:
                message = f"✅ 「{title_short}」\n已下载（文件已移动）"
        elif video.download_status == DownloadStatus.DOWNLOADING.value:
            message = f"⏳ 「{title_short}」\n正在下载中..."
        elif video.download_status == DownloadStatus.QUEUED.value:
            message = f"⏳ 「{title_short}」\n等待下载中..."
        elif video.download_status == DownloadStatus.FAILED.value:
            message = f"❌ 「{title_short}」\n下载失败了..."
        else:
            owner = video.owner_name[:10] if video.owner_name else "未知"
            duration = video.duration_str if hasattr(video, 'duration_str') and video.duration_str else "未知"
            size = f"{video.file_size / (1024*1024):.1f}MB" if video.file_size else "未知"
            message = f"📹 「{title_short}」\nUP主: {owner}\n时长: {duration} | 大小: {size}"
        
        if hasattr(self, 'mascot'):
            self.mascot.show_temp_message(message, 4000, MascotState.THINKING)
    
    def set_mascot_state(self, state: MascotState):
        """设置吉祥物状态"""
        if hasattr(self, 'mascot'):
            self.mascot.set_state(state)

    def _setup_shortcuts(self):
        """设置键盘快捷键"""
        from src.gui.shortcuts import ShortcutManager
        
        self.shortcut_manager = ShortcutManager(self)
        
        callbacks = {
            'refresh_devices': self.refresh_devices,
            'search_video': self._focus_search,
            'select_all': self.select_all_videos,
            'download_selected': self.download_selected,
            'open_settings': self._show_settings_dialog,
            'refresh_videos': self.refresh_videos,
            'delete_selected': self._delete_selected_videos,
            'show_help': self.show_shortcut_help,
        }
        
        registered = self.shortcut_manager.register_all(self, callbacks)
        self.logger.info(f"已注册 {registered} 个快捷键")
        
        self.shortcut_escape = QShortcut(QKeySequence("Escape"), self)
        self.shortcut_escape.activated.connect(self._clear_search)

    def _connect_video_panel_signals(self):
        """连接视频面板信号"""
        self.video_panel.select_all.connect(self.select_all_videos)
        self.video_panel.select_none.connect(self.select_none_videos)
        self.video_panel.refresh_requested.connect(self.refresh_videos)
        self.video_panel.cancel_downloads.connect(self.cancel_all_downloads)
        self.video_panel.download_requested.connect(self.download_selected)
        self.video_panel.browse_download_path.connect(self.browse_download_path)
        self.video_panel.search_changed.connect(self._on_search_text_changed)
        self.video_panel.cell_double_clicked.connect(self.on_cell_double_clicked)
        self.video_panel.cover_clicked.connect(self.show_cover_preview)
        self.video_panel.open_video_requested.connect(self.open_video_file)
        self.video_panel.video_clicked.connect(self._on_video_clicked)

    def _focus_search(self):
        """聚焦搜索框"""
        self.video_panel.search_input.setFocus()
        self.video_panel.search_input.selectAll()

    def _apply_dark_theme(self):
        """应用主题"""
        theme = getattr(self.user_settings, 'theme', 'dark')
        
        if theme == 'light':
            self._apply_light_theme()
        elif theme == 'cute':
            self._apply_cute_theme()
        else:
            self._apply_dark_theme_style()
        
        if hasattr(self, 'video_panel'):
            self.video_panel.apply_theme(theme)
        if hasattr(self, 'download_panel'):
            self.download_panel.apply_theme(theme)
        if hasattr(self, 'device_panel'):
            self.device_panel.apply_theme(theme)
        if hasattr(self, 'mascot'):
            self.mascot.apply_theme(theme)
    
    def _apply_cute_theme(self):
        """应用萌系主题"""
        self.setStyleSheet(get_cute_stylesheet())

    def _apply_dark_theme_style(self):
        """应用深色主题"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d2d2d;
            }
            QWidget {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QGroupBox {
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 12px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            QPushButton:pressed {
                background-color: #5d5d5d;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #666666;
            }
            QListWidget {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
            }
            QListWidget::item:hover {
                background-color: #4d4d4d;
            }
            QLabel {
                color: #ffffff;
            }
            QStatusBar {
                background-color: #252525;
                border-top: 1px solid #555;
            }
            QMenuBar {
                background-color: #252525;
            }
            QMenuBar::item:selected {
                background-color: #3d3d3d;
            }
            QMenu {
                background-color: #3d3d3d;
                border: 1px solid #555;
            }
            QMenu::item:selected {
                background-color: #2196F3;
            }
            QSplitter::handle {
                background-color: #555;
            }
            QScrollBar:vertical {
                background-color: #3d3d3d;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def _apply_light_theme(self):
        """应用浅色主题"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QWidget {
                background-color: #f0f0f0;
                color: #1a1a1a;
                font-size: 13px;
            }
            QGroupBox {
                border: 2px solid #c0c0c0;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
                color: #1a1a1a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #1a1a1a;
            }
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #a0a0a0;
                border-radius: 5px;
                padding: 8px 16px;
                color: #1a1a1a;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e8f4fc;
                border-color: #2196F3;
            }
            QPushButton:pressed {
                background-color: #cce8f7;
            }
            QPushButton:disabled {
                background-color: #e8e8e8;
                color: #888888;
                border-color: #d0d0d0;
            }
            QListWidget {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                color: #1a1a1a;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 4px;
                color: #1a1a1a;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e8f4fc;
            }
            QLabel {
                color: #1a1a1a;
                background-color: transparent;
            }
            QStatusBar {
                background-color: #e8e8e8;
                border-top: 2px solid #c0c0c0;
                color: #1a1a1a;
            }
            QMenuBar {
                background-color: #e8e8e8;
                color: #1a1a1a;
            }
            QMenuBar::item {
                padding: 6px 12px;
                color: #1a1a1a;
            }
            QMenuBar::item:selected {
                background-color: #d0d0d0;
            }
            QMenu {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                color: #1a1a1a;
            }
            QMenu::item {
                padding: 8px 24px;
                color: #1a1a1a;
            }
            QMenu::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QSplitter::handle {
                background-color: #c0c0c0;
            }
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 14px;
            }
            QScrollBar::handle:vertical {
                background-color: #b0b0b0;
                border-radius: 7px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QTableWidget {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                gridline-color: #d0d0d0;
                color: #1a1a1a;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #e0e0e0;
                color: #1a1a1a;
            }
            QTableWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QHeaderView::section {
                background-color: #e8e8e8;
                padding: 10px;
                border: 1px solid #c0c0c0;
                font-weight: bold;
                color: #1a1a1a;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                padding: 8px;
                color: #1a1a1a;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
            QComboBox {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                padding: 8px;
                color: #1a1a1a;
            }
            QComboBox:hover {
                border-color: #2196F3;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                color: #1a1a1a;
                selection-background-color: #2196F3;
            }
            QCheckBox {
                color: #1a1a1a;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #808080;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QCheckBox::indicator:hover {
                border-color: #2196F3;
                background-color: #e8f4fc;
            }
            QCheckBox::indicator:checked {
                background-color: #2196F3;
                border-color: #2196F3;
            }
            QCheckBox::indicator:disabled {
                background-color: #e8e8e8;
                border-color: #c0c0c0;
            }
            QSpinBox {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                padding: 6px;
                color: #1a1a1a;
            }
            QSpinBox:focus {
                border-color: #2196F3;
            }
            QProgressBar {
                background-color: #e0e0e0;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                text-align: center;
                color: #1a1a1a;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
            QTabWidget::pane {
                border: 2px solid #c0c0c0;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #e8e8e8;
                color: #1a1a1a;
                padding: 10px 20px;
                border: 2px solid #c0c0c0;
            }
            QTabBar::tab:selected {
                background-color: #2196F3;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #d0d0d0;
            }
            QTextEdit, QPlainTextEdit {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                color: #1a1a1a;
            }
            QToolTip {
                background-color: #ffffff;
                border: 1px solid #c0c0c0;
                color: #1a1a1a;
            }
        """)

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        file_menu = menubar.addMenu(tr("文件"))
        settings_action = QAction(tr("设置"), self)
        settings_action.triggered.connect(self._show_settings_dialog)
        file_menu.addAction(settings_action)
        file_menu.addSeparator()
        exit_action = QAction(tr("退出"), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        tools_menu = menubar.addMenu(tr("工具"))
        refresh_action = QAction(tr("刷新设备"), self)
        refresh_action.triggered.connect(self.refresh_devices)
        tools_menu.addAction(refresh_action)
        tools_menu.addSeparator()
        clear_cache_action = QAction(tr("清理封面缓存"), self)
        clear_cache_action.triggered.connect(self._clear_cover_cache)
        tools_menu.addAction(clear_cache_action)
        tools_menu.addSeparator()
        history_action = QAction(tr("查看历史"), self)
        history_action.triggered.connect(self._show_download_history)
        tools_menu.addAction(history_action)
        statistics_action = QAction(tr("查看统计"), self)
        statistics_action.triggered.connect(self._show_statistics)
        tools_menu.addAction(statistics_action)

        data_menu = menubar.addMenu(tr("数据管理"))
        export_video_action = QAction(tr("导出视频列表"), self)
        export_video_action.triggered.connect(self._export_video_list)
        data_menu.addAction(export_video_action)
        data_menu.addSeparator()
        export_action = QAction(tr("导出数据"), self)
        export_action.triggered.connect(self._show_backup_dialog)
        data_menu.addAction(export_action)
        import_action = QAction(tr("导入数据"), self)
        import_action.triggered.connect(self._show_backup_dialog_import)
        data_menu.addAction(import_action)

        help_menu = menubar.addMenu(tr("帮助"))
        shortcut_help_action = QAction(tr("快捷键说明"), self)
        shortcut_help_action.triggered.connect(self.show_shortcut_help)
        help_menu.addAction(shortcut_help_action)
        help_menu.addSeparator()
        about_action = QAction(tr("关于"), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def refresh_devices(self):
        """刷新设备列表"""
        self.device_manager.refresh_devices()
        devices = self.device_manager.get_online_devices()
        self.state_manager.set(StateKey.DEVICES, devices)

    def _on_wireless_connect_requested(self):
        """处理无线连接请求"""
        dialog = WirelessConnectDialog(self.adb_service, self, theme=self.user_settings.theme)
        dialog.connection_requested.connect(self._on_wireless_connection_requested)
        dialog.exec()

    def _on_wireless_connection_requested(self, ip: str, port: int):
        """处理无线连接请求"""
        try:
            self.status_bar.showMessage(f"正在连接 {ip}:{port}...")
            success = self.adb_service.connect_wireless(ip, port)
            if success:
                self.status_bar.showMessage(f"已连接到 {ip}:{port}")
                QTimer.singleShot(500, self.refresh_devices)
                
                unlocked = self._achievement_manager.on_wireless_connect()
                if unlocked:
                    self._achievement_notification_manager.show_achievements(unlocked)
            else:
                QMessageBox.warning(self, "连接失败", f"无法连接到 {ip}:{port}\n请确认设备IP地址正确且已开启无线调试。")
                self.status_bar.showMessage("无线连接失败")
        except Exception as e:
            QMessageBox.warning(self, "连接错误", f"连接时发生错误: {e}")
            self.status_bar.showMessage("无线连接失败")

    def on_device_selected(self, device: Device):
        """设备被选中"""
        self.current_device = device

        self.video_panel.set_refresh_enabled(True)

        if not device.has_bilibili:
            QMessageBox.warning(self, "提示", "该设备未安装B站客户端")
            self.video_panel.show_empty_guide("no_videos")
            return

        self.adb_service.keep_screen_on(device.device_id)

        self._load_videos_async(device.device_id)

    def _load_videos_async(self, device_id: str, force_refresh: bool = False):
        """异步加载视频列表"""
        self._current_load_request_id += 1
        current_request_id = self._current_load_request_id

        if self._video_load_worker and self._video_load_worker.isRunning():
            self._video_load_worker.stop()
            self._video_load_worker = None

        if not force_refresh and device_id in self._video_cache:
            cache_time = self._video_cache_time.get(device_id, 0)
            if time.time() - cache_time < self._video_cache_ttl:
                cached_videos = self._video_cache[device_id]
                self.status_bar.showMessage(f"使用缓存: {len(cached_videos)} 个视频")
                self._on_video_load_completed(cached_videos, current_request_id)
                return

        self.current_videos = []
        self.state_manager.clear_video_selection()
        self.video_panel.set_download_enabled(False)

        self.video_panel.set_refresh_enabled(False)

        self._show_loading_kaomoji()
        self.video_panel.show_loading()

        self._video_load_worker = VideoLoadWorker(self.cache_parser, device_id, current_request_id, self.db)
        self._video_load_worker.progress.connect(self._on_video_load_progress)
        self._video_load_worker.completed.connect(self._on_video_load_completed)
        self._video_load_worker.error.connect(self._on_video_load_error)
        self._video_load_worker.start()

    def _on_video_load_progress(self, message: str, request_id: int):
        if request_id != self._current_load_request_id:
            return
        self.status_bar.showMessage(message)

    def _on_video_load_completed(self, videos: list, request_id: int):
        if request_id != self._current_load_request_id:
            return

        if self.db and videos:
            with self.db.session() as session:
                from src.models.database import VideoModel
                import json
                for video in videos:
                    saved_video = VideoModel.get_by_video_and_device(session, video.video_id, video.device_id)
                    if saved_video and saved_video.download_status:
                        if saved_video.download_status == DownloadStatus.COMPLETED.value:
                            video.download_status = saved_video.download_status
                            video.local_path = saved_video.local_path
                            video.download_time = saved_video.download_time
                            if saved_video.all_local_paths:
                                video.all_local_paths = json.loads(saved_video.all_local_paths)
                            if saved_video.local_path and not os.path.exists(saved_video.local_path):
                                video.download_status = DownloadStatus.NOT_DOWNLOADED.value
                                video.local_path = None
                                video.all_local_paths = None
                        elif saved_video.download_status in [DownloadStatus.QUEUED.value, DownloadStatus.DOWNLOADING.value]:
                            video.download_status = DownloadStatus.NOT_DOWNLOADED.value
                        else:
                            video.download_status = saved_video.download_status

        if self.current_device and videos:
            self._video_cache[self.current_device.device_id] = videos
            self._video_cache_time[self.current_device.device_id] = time.time()

        self.video_manager._current_device_id = self.current_device.device_id if self.current_device else None
        self.video_manager._current_videos = videos

        if not videos:
            self.video_panel.show_empty_guide("no_videos")
        else:
            self.current_videos = videos
            self.video_panel.set_videos(videos)
            for video in videos:
                self._cover_queue.put((video.video_id, video.cover_path, video.device_id))

        self.status_bar.showMessage(f"已加载 {len(videos)} 个视频")
        self.video_panel.set_refresh_enabled(True)
        self.video_panel.set_download_enabled(False)
        self.video_panel.hide_loading()
        self._hide_loading_kaomoji()

    def _on_video_load_error(self, error_msg: str, request_id: int):
        if request_id != self._current_load_request_id:
            return
        self.status_bar.showMessage(f"加载视频失败: {error_msg}")
        QMessageBox.warning(self, "提示", f"无法加载视频列表: {error_msg}")
        self.video_panel.set_refresh_enabled(True)
        self.video_panel.show_empty_guide("no_videos")
        self.video_panel.hide_loading()
        self._hide_loading_kaomoji()

    def _show_loading_kaomoji(self):
        """显示加载颜文字"""
        self._hide_loading_kaomoji()
        
        self._loading_kaomoji_label = QLabel(self.video_panel.video_list)
        self._loading_kaomoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_kaomoji_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 28px;
                font-weight: bold;
                background-color: rgba(45, 45, 45, 230);
                border: 2px solid #4CAF50;
                border-radius: 10px;
                padding: 30px;
            }
        """)

        self._loading_kaomojis = KaomojiHelper.LOADING
        self._loading_tips = KaomojiHelper.TIPS
        self._loading_kaomoji_index = 0
        self._loading_tip_index = 0
        self._update_loading_kaomoji_text()

        self._loading_kaomoji_label.setFixedSize(500, 200)
        self._center_loading_kaomoji()

        self._loading_kaomoji_label.show()
        self._loading_kaomoji_label.raise_()

        self._loading_kaomoji_timer = QTimer(self)
        self._loading_kaomoji_timer.timeout.connect(self._update_loading_kaomoji)
        self._loading_kaomoji_timer.start(800)

    def _center_loading_kaomoji(self):
        if hasattr(self, '_loading_kaomoji_label') and self._loading_kaomoji_label:
            list_rect = self.video_panel.video_list.geometry()
            x = (list_rect.width() - self._loading_kaomoji_label.width()) // 2
            y = (list_rect.height() - self._loading_kaomoji_label.height()) // 2
            self._loading_kaomoji_label.move(x, y)

    def _update_loading_kaomoji_text(self):
        if hasattr(self, '_loading_kaomoji_label') and self._loading_kaomoji_label:
            kaomoji = self._loading_kaomojis[self._loading_kaomoji_index % len(self._loading_kaomojis)]
            tip = self._loading_tips[self._loading_tip_index % len(self._loading_tips)]
            self._loading_kaomoji_label.setText(f"{kaomoji}\n\n{tip}")

    def _update_loading_kaomoji(self):
        self._loading_kaomoji_index += 1
        if self._loading_kaomoji_index % 3 == 0:
            self._loading_tip_index += 1
        self._update_loading_kaomoji_text()

    def _hide_loading_kaomoji(self):
        if hasattr(self, '_loading_kaomoji_timer') and self._loading_kaomoji_timer:
            self._loading_kaomoji_timer.stop()
            self._loading_kaomoji_timer = None
        if hasattr(self, '_loading_kaomoji_label') and self._loading_kaomoji_label:
            self._loading_kaomoji_label.hide()
            self._loading_kaomoji_label.deleteLater()
            self._loading_kaomoji_label = None

    def _on_search_text_changed(self, text: str):
        """搜索文本变化时筛选视频 - 使用防抖"""
        self.video_panel.clear_search_btn.setVisible(bool(text.strip()))
        
        if not text.strip():
            if hasattr(self, '_search_debounce_timer'):
                self._search_debounce_timer.stop()
            self._apply_search_filter()
            return
        
        if not hasattr(self, '_search_debounce_timer'):
            self._search_debounce_timer = QTimer()
            self._search_debounce_timer.setSingleShot(True)
            self._search_debounce_timer.timeout.connect(self._apply_search_filter)
        
        self._search_debounce_timer.start(300)

    def _clear_search(self):
        """清除搜索"""
        self.video_panel.search_input.clear()
        self.video_panel.clear_search_btn.setVisible(False)

    def _apply_search_filter(self):
        """应用搜索筛选"""
        search_text = self.video_panel.search_input.text().strip().lower()
        
        if not search_text:
            self.video_panel.filter_videos("")
            return
        
        self.video_panel.filter_videos(search_text)

    def _download_single_video(self, video: Video):
        """下载单个视频"""
        if not self.current_device:
            return
        
        self.state_manager.set(StateKey.SELECTED_VIDEOS, {video.video_id})
        self.download_selected()

    def _copy_to_clipboard(self, text: str):
        """复制文本到剪贴板"""
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.status_bar.showMessage(f"已复制: {text[:30]}{'...' if len(text) > 30 else ''}")

    def _open_file_location(self, file_path: str, all_paths: list = None):
        """打开文件所在位置"""
        if all_paths and len(all_paths) > 1:
            from PyQt6.QtWidgets import QMenu
            
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    border: 1px solid #555;
                }
                QMenu::item:selected {
                    background-color: #2196F3;
                }
            """)
            
            for i, path in enumerate(all_paths):
                file_name = os.path.basename(path)
                action = menu.addAction(f"P{i+1}: {file_name}")
                action.triggered.connect(lambda checked, p=path: self._open_single_file_location(p))
            
            menu.addSeparator()
            open_all_action = menu.addAction("打开所有分P所在文件夹")
            open_all_action.triggered.connect(lambda: self._open_all_file_locations(all_paths))
            
            menu.exec(self.cursor().pos())
        else:
            self._open_single_file_location(file_path)
    
    def _open_single_file_location(self, file_path: str):
        """打开单个文件所在位置"""
        if file_path and os.path.exists(file_path):
            import subprocess
            subprocess.Popen(f'explorer /select,"{file_path}"')
    
    def _open_all_file_locations(self, file_paths: list):
        """打开所有文件所在文件夹"""
        folders = set()
        for path in file_paths:
            if os.path.exists(path):
                folder = os.path.dirname(path)
                folders.add(folder)
        
        for folder in folders:
            import subprocess
            subprocess.Popen(f'explorer "{folder}"')

    def on_cell_double_clicked(self, row: int, column: int):
        video = self.video_panel.get_video_at_row(row)
        if not video:
            return
        
        if column == 1:
            self.show_cover_preview(video)
        elif column == 2:
            self._download_single_video_by_double_click(video)

    def _download_single_video_by_double_click(self, video: Video):
        """双击标题下载单个视频"""
        if not self.current_device:
            QMessageBox.warning(self, "提示", "请先选择设备")
            return

        if video.download_status == DownloadStatus.COMPLETED.value:
            if video.local_path and os.path.exists(video.local_path):
                reply = QMessageBox.question(
                    self, "确认",
                    f"该视频已下载，是否重新下载？\n\n{video.title}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            else:
                video.download_status = DownloadStatus.NOT_DOWNLOADED.value
                video.local_path = None

        if video.download_status in [DownloadStatus.DOWNLOADING.value, DownloadStatus.QUEUED.value]:
            QMessageBox.information(self, "提示", "该视频正在下载中")
            return

        download_dir = self.video_panel.get_download_dir()
        is_sufficient, free_gb, message = self.config.check_disk_space()
        if not is_sufficient:
            QMessageBox.warning(self, "空间不足", message)
            return

        video.download_status = DownloadStatus.QUEUED.value
        self._update_video_status_in_db(video)

        request = DownloadRequest(
            device_id=video.device_id,
            video_id=video.video_id,
            video_title=video.title,
            cache_video_path=video.cache_video_path,
            cache_audio_path=video.cache_audio_path,
            cache_info_path=video.cache_info_path,
            local_dir=download_dir
        )

        task_id = self.file_transfer.submit_download(request)
        self._task_video_map[task_id] = video.video_id
        self._refresh_video_row(video.video_id)
        self.download_panel.add_task(task_id, video.title)
        
        msg, state = MascotMessageHelper.download_start(video.title, video.owner_name)
        self._show_mascot_message(msg, state=state)
        self.status_bar.showMessage(f"已添加下载: {video.title}")

    def show_cover_preview(self, video: Video):
        """显示封面预览"""
        if not video.cover_path:
            QMessageBox.information(self, "提示", "该视频没有封面")
            return

        try:
            if video.cover_path.startswith('http'):
                local_path = self.cover_cache.download_cover(video.video_id, video.cover_path)
            else:
                import tempfile
                temp_dir = Path(tempfile.gettempdir()) / "bili_covers_v02"
                temp_dir.mkdir(parents=True, exist_ok=True)
                local_path = temp_dir / f"{video.video_id}_cover_preview.jpg"
                if not local_path.exists():
                    self.adb_service.pull_file(video.device_id, video.cover_path, str(local_path))

            if not local_path or not local_path.exists():
                QMessageBox.warning(self, "提示", "封面下载失败")
                return

            self._show_cover_dialog(str(local_path), video.title)

        except Exception as e:
            QMessageBox.warning(self, "提示", f"封面预览失败: {e}")

    def _show_cover_dialog(self, cover_path: str, title: str):
        """显示封面预览对话框 - 支持缩放"""
        from PyQt6.QtWidgets import QDialog, QScrollArea, QSlider

        dialog = QDialog(self)
        dialog.setWindowTitle(f"封面预览 - {title}")
        dialog.setMinimumSize(900, 700)
        dialog.resize(1100, 800)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_area.setStyleSheet("QScrollArea { background-color: #1a1a1a; border: none; }")

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pixmap = QPixmap(cover_path)
        if not pixmap.isNull():
            original_width = pixmap.width()
            original_height = pixmap.height()

            image_label = QLabel()
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setPixmap(pixmap)
            image_label.setStyleSheet("background-color: transparent;")

            container_layout.addWidget(image_label)

            info_layout = QHBoxLayout()
            info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            info_label = QLabel(f"📐 原始尺寸: {original_width} x {original_height} 像素")
            info_label.setStyleSheet("color: #888; font-size: 12px;")
            info_layout.addWidget(info_label)

            size_label = QLabel(f"  |  当前: 100%")
            size_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
            info_layout.addWidget(size_label)

            container_layout.addLayout(info_layout)

            control_layout = QHBoxLayout()
            control_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            zoom_out_btn = QPushButton("🔍−")
            zoom_out_btn.setFixedSize(40, 30)
            zoom_out_btn.setStyleSheet("""
                QPushButton { background-color: #3d3d3d; color: white; border: 1px solid #555; border-radius: 4px; font-size: 16px; }
                QPushButton:hover { background-color: #4d4d4d; }
            """)
            control_layout.addWidget(zoom_out_btn)

            zoom_slider = QSlider(Qt.Orientation.Horizontal)
            zoom_slider.setMinimum(10)
            zoom_slider.setMaximum(300)
            zoom_slider.setValue(100)
            zoom_slider.setFixedWidth(200)
            zoom_slider.setStyleSheet("""
                QSlider::groove:horizontal { height: 8px; background: #3d3d3d; border-radius: 4px; }
                QSlider::handle:horizontal { background: #4CAF50; width: 18px; margin: -5px 0; border-radius: 9px; }
                QSlider::sub-page:horizontal { background: #4CAF50; border-radius: 4px; }
            """)
            control_layout.addWidget(zoom_slider)

            zoom_in_btn = QPushButton("🔍+")
            zoom_in_btn.setFixedSize(40, 30)
            zoom_in_btn.setStyleSheet("""
                QPushButton { background-color: #3d3d3d; color: white; border: 1px solid #555; border-radius: 4px; font-size: 16px; }
                QPushButton:hover { background-color: #4d4d4d; }
            """)
            control_layout.addWidget(zoom_in_btn)

            reset_btn = QPushButton("↺ 重置")
            reset_btn.setFixedSize(60, 30)
            reset_btn.setStyleSheet("""
                QPushButton { background-color: #2196F3; color: white; border: none; border-radius: 4px; font-size: 12px; }
                QPushButton:hover { background-color: #1976D2; }
            """)
            control_layout.addWidget(reset_btn)

            fit_btn = QPushButton("⊞ 适应窗口")
            fit_btn.setFixedSize(90, 30)
            fit_btn.setStyleSheet("""
                QPushButton { background-color: #FF9800; color: white; border: none; border-radius: 4px; font-size: 12px; }
                QPushButton:hover { background-color: #F57C00; }
            """)
            control_layout.addWidget(fit_btn)

            main_layout.addLayout(control_layout)

            def update_zoom(value):
                scale = value / 100.0
                new_width = int(original_width * scale)
                new_height = int(original_height * scale)
                scaled = pixmap.scaled(
                    new_width, new_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                image_label.setPixmap(scaled)
                size_label.setText(f"  |  当前: {value}%")

            def zoom_in():
                new_value = min(300, zoom_slider.value() + 10)
                zoom_slider.setValue(new_value)

            def zoom_out():
                new_value = max(10, zoom_slider.value() - 10)
                zoom_slider.setValue(new_value)

            def fit_to_window():
                available_width = scroll_area.width() - 40
                available_height = scroll_area.height() - 80
                scale_w = available_width / original_width
                scale_h = available_height / original_height
                scale = min(scale_w, scale_h, 1.0)
                zoom_slider.setValue(int(scale * 100))

            zoom_slider.valueChanged.connect(update_zoom)
            zoom_in_btn.clicked.connect(zoom_in)
            zoom_out_btn.clicked.connect(zoom_out)
            reset_btn.clicked.connect(lambda: zoom_slider.setValue(100))
            fit_btn.clicked.connect(fit_to_window)

        else:
            error_label = QLabel("无法加载封面图片")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("color: #f44336; font-size: 16px;")
            container_layout.addWidget(error_label)

        scroll_area.setWidget(container)
        main_layout.insertWidget(0, scroll_area, 1)

        dialog.setLayout(main_layout)
        dialog.exec()

    def refresh_videos(self):
        if not self.current_device:
            return
        self._load_videos_async(self.current_device.device_id, force_refresh=True)

    def _auto_refresh_videos(self):
        """自动刷新视频列表"""
        if not self.current_device:
            return
        if not self.user_settings.auto_refresh:
            return
        self._load_videos_async(self.current_device.device_id, force_refresh=True)

    def on_video_checked(self, video_id: str, state):
        if state == Qt.CheckState.Checked.value:
            self.state_manager.add_video_to_selection(video_id)
        else:
            self.state_manager.remove_video_from_selection(video_id)

    def select_all_videos(self):
        self.video_panel.select_all_videos()

    def select_none_videos(self):
        self.video_panel.deselect_all_videos()
    
    def _delete_selected_videos(self):
        """删除选中的视频（从设备缓存中删除）"""
        selected_videos = self.video_panel.get_selected_videos()
        if not selected_videos:
            QMessageBox.information(self, "提示", "请先选择要删除的视频")
            return
        
        titles = "\n".join([f"- {v.title}" for v in selected_videos[:5]])
        if len(selected_videos) > 5:
            titles += f"\n... 等共 {len(selected_videos)} 个视频"
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要从设备缓存中删除以下视频吗？\n此操作不可恢复！\n\n{titles}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        deleted_count = 0
        failed_count = 0
        
        for video in selected_videos:
            try:
                if self._delete_video_from_cache(video):
                    deleted_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                self.logger.error(f"删除视频失败: {video.title} - {e}")
                failed_count += 1
        
        if deleted_count > 0:
            self.status_bar.showMessage(f"已删除 {deleted_count} 个视频")
            self.refresh_videos()
        
        if failed_count > 0:
            QMessageBox.warning(self, "提示", f"{failed_count} 个视频删除失败")
    
    def _delete_video_from_cache(self, video: Video) -> bool:
        """从设备缓存中删除视频
        
        Args:
            video: 视频对象
            
        Returns:
            是否删除成功
        """
        if not self.current_device:
            return False
        
        try:
            cache_dir = None
            if video.cache_path:
                cache_dir = video.cache_path
            elif video.cache_video_path:
                import os
                cache_dir = os.path.dirname(video.cache_video_path)
            
            if cache_dir:
                self.adb_service.run_command(
                    self.current_device.device_id,
                    f"rm -rf '{cache_dir}'"
                )
                return True
        except Exception as e:
            self.logger.error(f"删除视频缓存失败: {e}")
        
        return False

    def update_download_button(self):
        selected = self.state_manager.get(StateKey.SELECTED_VIDEOS) or set()
        self.video_panel.set_download_enabled(len(selected) > 0)

    def browse_download_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择下载目录", str(self.config.DOWNLOAD_DIR))
        if path:
            self.video_panel.set_download_dir(path)

    def download_selected(self):
        selected_videos = self.video_panel.get_selected_videos()
        if not selected_videos:
            return

        download_dir = self.video_panel.get_download_dir()

        is_sufficient, free_gb, message = self.config.check_disk_space()
        if not is_sufficient:
            QMessageBox.warning(self, "空间不足", message)
            return

        videos_to_download = []
        already_downloaded = []

        for video in selected_videos:
            if video.download_status == DownloadStatus.COMPLETED.value:
                if video.local_path and os.path.exists(video.local_path):
                    already_downloaded.append(video)
                    continue
            videos_to_download.append(video)

        if already_downloaded:
            titles = "\n".join([f"- {v.title}" for v in already_downloaded[:5]])
            if len(already_downloaded) > 5:
                titles += f"\n... 等共 {len(already_downloaded)} 个视频"
            QMessageBox.information(self, "提示", f"以下视频已下载，将跳过:\n{titles}")

        if not videos_to_download:
            self.status_bar.showMessage("所有选中视频已下载")
            return

        self.video_panel.show_progress(0)
        self.status_bar.showMessage(f"开始下载 {len(videos_to_download)} 个视频...")

        for video in videos_to_download:
            video.download_status = DownloadStatus.QUEUED.value
            self._update_video_status_in_db(video)

            request = DownloadRequest(
                device_id=video.device_id,
                video_id=video.video_id,
                video_title=video.title,
                cache_video_path=video.cache_video_path,
                cache_audio_path=video.cache_audio_path,
                cache_info_path=video.cache_info_path,
                local_dir=download_dir
            )

            task_id = self.file_transfer.submit_download(request)
            self._task_video_map[task_id] = video.video_id
            self._refresh_video_row(video.video_id)
            self.download_panel.add_task(task_id, video.title)

        unlocked = self._achievement_manager.on_batch_download(len(videos_to_download))
        if unlocked:
            self._achievement_notification_manager.show_achievements(unlocked)

        QMessageBox.information(self, "提示", f"已添加 {len(videos_to_download)} 个视频到下载队列")

    def handle_event(self, event_type: str, data):
        if event_type.startswith('download.'):
            self._handle_download_event(event_type, data)
        elif event_type.startswith('device.'):
            self._handle_device_event(event_type, data)

    def _handle_download_event(self, event_type: str, data: dict):
        task_id = data.get('task_id') if isinstance(data, dict) else None
        video_id = data.get('video_id') if isinstance(data, dict) else None

        if event_type == 'download.queued':
            self.video_status_updated.emit(task_id, None, video_id, None, DownloadStatus.QUEUED.value)
            self._update_tray_for_download("等待中", video_id)
        elif event_type == 'download.started':
            self.video_status_updated.emit(task_id, None, video_id, None, DownloadStatus.DOWNLOADING.value)
            self._update_tray_for_download("开始下载", video_id)
        elif event_type == 'download.completed':
            local_path = data.get('local_path') if isinstance(data, dict) else None
            video_title = data.get('video_title') if isinstance(data, dict) else None
            all_files = data.get('all_files') if isinstance(data, dict) else None
            self.video_status_updated.emit(task_id, local_path, video_id, video_title, DownloadStatus.COMPLETED.value)
            if all_files and video_id:
                self._update_video_all_files(video_id, all_files)
            self._on_download_completed(video_title or "视频")
        elif event_type == 'download.error':
            error_msg = data.get('error') if isinstance(data, dict) else str(data)
            self.status_bar.showMessage(f"下载错误: {error_msg}")
            self.video_status_updated.emit(task_id, None, video_id, None, DownloadStatus.FAILED.value)
            self._on_download_failed(video_id or "视频", error_msg)
        elif event_type == 'download.cancelled':
            self.video_status_updated.emit(task_id, None, video_id, None, DownloadStatus.CANCELLED.value)
            self._update_tray_for_download("已取消", video_id)
        elif event_type == 'download.progress':
            progress = data.get('progress', 0) if isinstance(data, dict) else 0
            self.video_panel.show_progress(int(progress))
            if video_id:
                self._update_video_progress(video_id, progress)
            self._update_tray_progress(progress, video_id)
    
    def _update_tray_for_download(self, status: str, video_id: str = None):
        """更新托盘状态"""
        active_count = self.download_panel.get_active_task_count() if self.download_panel else 0
        if active_count > 0:
            self._tray_icon.setToolTip(f"B站缓存视频下载工具 - {active_count}个任务进行中")
        else:
            self._tray_icon.setToolTip("B站缓存视频下载工具")
    
    def _update_tray_progress(self, progress: float, video_id: str = None):
        """更新托盘进度显示"""
        active_count = self.download_panel.get_active_task_count() if self.download_panel else 0
        
        if active_count > 0:
            self._tray_icon.setIcon(self._create_progress_icon(int(progress)))
            self._tray_icon.setToolTip(f"B站缓存视频下载工具 - 下载中 {int(progress)}%")
        else:
            self._tray_icon.setIcon(self._create_tray_icon())
            self._tray_icon.setToolTip("B站缓存视频下载工具")
    
    def _on_download_completed(self, video_title: str):
        """下载完成通知"""
        self._tray_icon.setIcon(self._create_tray_icon())
        self._tray_icon.setToolTip("B站缓存视频下载工具")
        
        if not hasattr(self, '_last_complete_msg_time'):
            self._last_complete_msg_time = 0
        
        import time
        current_time = time.time()
        
        if current_time - self._last_complete_msg_time > 5:
            msg, state = MascotMessageHelper.download_complete()
            self._show_mascot_message(msg, state=state)
            self._last_complete_msg_time = current_time
        
        if self.notification_service.is_enabled():
            self._tray_icon.showMessage(
                "下载完成",
                f"{video_title[:30]}{'...' if len(video_title) > 30 else ''}\n已成功下载",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
        
        self._update_tray_for_download("完成")
        
        unlocked = self._achievement_manager.on_video_downloaded()
        if unlocked:
            self._achievement_notification_manager.show_achievements(unlocked)
    
    def _on_download_failed(self, video_title: str, error_msg: str):
        """下载失败通知"""
        self._tray_icon.setIcon(self._create_tray_icon())
        
        if self.notification_service.is_enabled():
            self._tray_icon.showMessage(
                "下载失败",
                f"{video_title[:20]}{'...' if len(video_title) > 20 else ''}\n错误: {error_msg[:50]}",
                QSystemTrayIcon.MessageIcon.Warning,
                5000
            )

    def _handle_device_event(self, event_type: str, data):
        if event_type == 'device.connected':
            device_name = data.display_name if hasattr(data, 'display_name') else str(data)
            device_id = data.device_id if hasattr(data, 'device_id') else str(data)
            
            if not hasattr(self, '_connected_devices'):
                self._connected_devices = set()
            
            if device_id in self._connected_devices:
                return
            
            self._connected_devices.add(device_id)
            self.status_bar.showMessage(f"设备已连接: {device_name}")
            
            unlocked = self._achievement_manager.on_device_connected(device_id)
            if unlocked:
                self._achievement_notification_manager.show_achievements(unlocked)
        elif event_type == 'device.disconnected':
            device_id = data if isinstance(data, str) else (data.device_id if hasattr(data, 'device_id') else str(data))
            
            if hasattr(self, '_connected_devices') and device_id in self._connected_devices:
                self._connected_devices.discard(device_id)
            
            self.status_bar.showMessage(f"设备已断开: {device_id}")
            if self.file_transfer:
                self.file_transfer.handle_device_disconnected(device_id)

    def _on_video_status_updated(self, task_id: str, local_path: str, video_id: str = None,
                                  video_title: str = None, status: str = None):
        try:
            if status == DownloadStatus.COMPLETED.value:
                self.status_bar.showMessage(f"下载完成: {local_path}")
                self.video_panel.hide_progress()

            matched_video = None
            videos = self.current_videos

            for video in videos:
                if video_id and video.video_id == video_id:
                    matched_video = video
                    break
                if task_id and task_id in self._task_video_map:
                    mapped_video_id = self._task_video_map.get(task_id)
                    if mapped_video_id and video.video_id == mapped_video_id:
                        matched_video = video
                        break

            if matched_video:
                matched_video.download_status = status
                if local_path:
                    matched_video.local_path = local_path

                self.video_panel.update_video_status(video_id or matched_video.video_id, status, local_path)
                self._update_video_status_in_db(matched_video)
                self._update_cancel_all_button()

                if status == DownloadStatus.COMPLETED.value and task_id:
                    if task_id in self._task_video_map:
                        del self._task_video_map[task_id]
                    self.download_panel.update_task(task_id, status, 100)

        except Exception as e:
            self.logger.error(f"更新视频状态失败: {e}")

    def _update_video_all_files(self, video_id: str, all_files: list):
        video = self.state_manager.get_video_by_id(video_id)
        if video:
            video.all_local_paths = all_files
        
        self.video_panel.update_video_all_local_paths(video_id, all_files)
        
        if video:
            with self.db.session() as session:
                from src.models.database import VideoModel
                import json
                db_video = VideoModel.get_by_video_and_device(session, video.video_id, video.device_id)
                if db_video:
                    db_video.all_local_paths = json.dumps(all_files)

    def _cancel_download(self, video_id: str):
        task_id = None
        for tid, vid in self._task_video_map.items():
            if vid == video_id:
                task_id = tid
                break

        if task_id:
            if self.file_transfer.cancel_task(task_id):
                self.status_bar.showMessage(f"已取消下载任务")
                del self._task_video_map[task_id]
                video = self.state_manager.get_video_by_id(video_id)
                if video:
                    video.download_status = DownloadStatus.CANCELLED.value
                    self._update_video_status_in_db(video)
                self._refresh_video_row(video_id)
                self._update_cancel_all_button()
                self.download_panel.update_task(task_id, DownloadStatus.CANCELLED.value)

    def cancel_all_downloads(self):
        reply = QMessageBox.question(
            self, "确认取消", "确定要取消所有下载任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        cancelled_count = self.file_transfer.cancel_batch(list(self._task_video_map.keys()))

        for task_id, video_id in list(self._task_video_map.items()):
            video = self.state_manager.get_video_by_id(video_id)
            if video:
                video.download_status = DownloadStatus.CANCELLED.value
                self._update_video_status_in_db(video)
                self._refresh_video_row(video_id)
            self.download_panel.update_task(task_id, DownloadStatus.CANCELLED.value)

        self._task_video_map.clear()
        self._update_cancel_all_button()
        self.status_bar.showMessage(f"已取消 {cancelled_count} 个下载任务")

    def _update_cancel_all_button(self):
        videos = self.current_videos
        has_active_tasks = any(
            video.download_status in [DownloadStatus.QUEUED.value, DownloadStatus.DOWNLOADING.value]
            for video in videos
        )
        self.video_panel.set_cancel_enabled(has_active_tasks)

    def _retry_download(self, video: Video):
        download_dir = self.video_panel.get_download_dir()

        video.download_status = DownloadStatus.QUEUED.value
        video.local_path = None
        video.all_local_paths = None
        self._update_video_status_in_db(video)

        request = DownloadRequest(
            device_id=video.device_id,
            video_id=video.video_id,
            video_title=video.title,
            cache_video_path=video.cache_video_path,
            cache_audio_path=video.cache_audio_path,
            cache_info_path=video.cache_info_path,
            local_dir=download_dir
        )

        task_id = self.file_transfer.submit_download(request)
        self._task_video_map[task_id] = video.video_id
        self._refresh_video_row(video.video_id)
        self.download_panel.add_task(task_id, video.title)
        self.status_bar.showMessage(f"已重新添加下载: {video.title}")

    def _refresh_video_row(self, video_id: str):
        video = self.state_manager.get_video_by_id(video_id)
        if video:
            self.video_panel.update_video_status(video_id, video.download_status, video.local_path)

    def _update_video_status_in_db(self, video: Video):
        with self.db.session() as session:
            from src.models.database import VideoModel
            VideoModel.save_or_update(session, video)

    def _update_video_progress(self, video_id: str, progress: float):
        try:
            self.video_panel.update_video_status(video_id, DownloadStatus.DOWNLOADING.value, progress=int(progress))
        except Exception as e:
            self.logger.debug(f"更新进度条失败: {e}")

    def _on_cancel_task_requested(self, task_id: str):
        if task_id in self._task_video_map:
            video_id = self._task_video_map[task_id]
            self._cancel_download(video_id)

    def _get_video_by_id(self, video_id: str) -> Optional[Video]:
        """根据视频ID获取视频对象"""
        return self.state_manager.get_video_by_id(video_id)

    def _retry_failed_downloads(self):
        """重试所有失败的下载任务"""
        failed_tasks = self.file_transfer.get_failed_tasks()
        if not failed_tasks:
            QMessageBox.information(self, "提示", "没有失败的任务需要重试")
            return
        
        retry_count = 0
        for task_id in failed_tasks:
            video_id = self._task_video_map.get(task_id)
            if video_id:
                video = self._get_video_by_id(video_id)
                if video:
                    self._retry_download(video)
                    retry_count += 1
        
        self.status_bar.showMessage(f"已重新提交 {retry_count} 个失败任务")
        if retry_count > 0:
            QMessageBox.information(self, "提示", f"已重新提交 {retry_count} 个失败任务到下载队列")

    def _restore_download_tasks(self):
        """恢复未完成的下载任务"""
        try:
            self.file_transfer.restore_tasks()
            self.logger.info("下载任务恢复完成")
        except Exception as e:
            self.logger.error(f"恢复下载任务失败: {e}")

    def _delete_history_record(self, task_id: str):
        """删除历史记录"""
        try:
            with self.db.session() as session:
                from src.models.database import DownloadTaskModel
                DownloadTaskModel.delete_by_task_id(session, task_id)
            self.status_bar.showMessage("已删除历史记录")
        except Exception as e:
            self.logger.error(f"删除历史记录失败: {e}")

    def open_video_file(self, file_path: str, all_paths: list = None):
        try:
            import platform

            if all_paths and len(all_paths) > 1:
                from PyQt6.QtWidgets import QMenu
                
                menu = QMenu(self)
                menu.setStyleSheet("""
                    QMenu {
                        background-color: #3d3d3d;
                        color: #ffffff;
                        border: 1px solid #555;
                    }
                    QMenu::item:selected {
                        background-color: #2196F3;
                    }
                """)
                
                for i, path in enumerate(all_paths):
                    file_name = os.path.basename(path)
                    action = menu.addAction(f"P{i+1}: {file_name}")
                    action.triggered.connect(lambda checked, p=path: self._open_single_file(p))
                
                menu.addSeparator()
                open_all_action = menu.addAction("打开所有分P")
                open_all_action.triggered.connect(lambda: self._open_all_files(all_paths))
                
                menu.exec(self.cursor().pos())
            else:
                self._open_single_file(file_path)

        except Exception as e:
            QMessageBox.warning(self, "提示", f"无法打开视频: {e}")
    
    def _open_single_file(self, file_path: str):
        """打开单个视频文件"""
        try:
            import platform

            if not os.path.exists(file_path):
                QMessageBox.warning(self, "提示", f"文件不存在: {file_path}")
                return

            system = platform.system()
            if system == 'Windows':
                os.startfile(file_path)
            elif system == 'Darwin':
                import subprocess
                subprocess.run(['open', file_path])
            else:
                import subprocess
                subprocess.run(['xdg-open', file_path])

            self.status_bar.showMessage(f"已打开: {file_path}")
        except Exception as e:
            QMessageBox.warning(self, "提示", f"无法打开视频: {e}")
    
    def _open_all_files(self, file_paths: list):
        """打开所有视频文件"""
        for path in file_paths:
            self._open_single_file(path)

    def _clear_cover_cache(self):
        count = self.cover_cache.clear_cache(0)
        QMessageBox.information(self, "完成", f"已清理 {count} 个封面缓存文件")

    def _show_download_history(self):
        """显示下载历史对话框"""
        dialog = DownloadHistoryDialog(self.db, self, theme=self.user_settings.theme)
        dialog.open_file_requested.connect(self.open_video_file)
        dialog.open_folder_requested.connect(self._open_file_location)
        dialog.exec()

    def _show_statistics(self):
        """显示统计对话框"""
        from src.services.statistics_service import StatisticsService
        from src.gui.dialogs.statistics_dialog import StatisticsDialog
        
        statistics_service = StatisticsService(self.db)
        dialog = StatisticsDialog(statistics_service, self)
        dialog.exec()

    def _export_video_list(self):
        """导出视频列表"""
        from src.services.export_service import ExportService
        
        if not self.current_videos:
            QMessageBox.warning(self, "提示", "没有视频可导出")
            return
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "导出视频列表",
            "",
            "CSV文件 (*.csv);;JSON文件 (*.json)"
        )
        
        if not file_path:
            return
        
        export_service = ExportService()
        
        if selected_filter.startswith("CSV"):
            success = export_service.export_to_csv(self.current_videos, file_path)
        else:
            success = export_service.export_to_json(self.current_videos, file_path)
        
        if success:
            QMessageBox.information(self, "成功", f"已导出到 {file_path}")
        else:
            QMessageBox.warning(self, "失败", "导出失败")

    def _show_settings_dialog(self):
        """显示设置对话框"""
        theme = getattr(self.user_settings, 'theme', 'dark')
        dialog = SettingsDialog(self.user_settings, self, theme=theme)
        dialog.settings_saved.connect(self._on_settings_saved)
        dialog.exec()
    
    def _show_backup_dialog(self):
        """显示备份对话框（默认导出标签页）"""
        dialog = BackupDialog(self.backup_service, self, theme=self.user_settings.theme)
        dialog.exec()
    
    def _show_backup_dialog_import(self):
        """显示备份对话框（默认导入标签页）"""
        dialog = BackupDialog(self.backup_service, self, theme=self.user_settings.theme)
        dialog.findChild(QTabWidget).setCurrentIndex(1)
        dialog.exec()
    
    def _on_settings_saved(self, settings: UserSettings):
        """设置保存回调"""
        old_theme = self.user_settings.theme
        old_auto_refresh = self.user_settings.auto_refresh
        old_refresh_interval = getattr(self.user_settings, 'refresh_interval', 30)
        old_language = self.user_settings.language
        
        self.settings_service.settings = settings
        self.settings_service.save()
        self.user_settings = settings
        
        if settings.download_dir:
            self.video_panel.set_download_dir(settings.download_dir)
        
        self.notification_service.set_enabled(settings.enable_notification)
        
        if old_theme != settings.theme:
            self._apply_dark_theme()
            
            unlocked = self._achievement_manager.on_theme_switch()
            if unlocked:
                self._achievement_notification_manager.show_achievements(unlocked)
        
        if old_language != settings.language:
            TranslationManager.get_instance().load_language(settings.language)
            self.status_bar.showMessage(tr("语言设置已更改，部分界面可能需要重启程序才能生效"))
        else:
            self.status_bar.showMessage(tr("设置已保存并生效"))
        
        if hasattr(self, 'video_refresh_timer'):
            if settings.auto_refresh:
                interval = getattr(settings, 'refresh_interval', 30) * 1000
                self.video_refresh_timer.start(interval)
            else:
                self.video_refresh_timer.stop()

    def show_about(self):
        dialog = AboutDialog(self, theme=self.user_settings.theme)
        dialog.exec()
    
    def show_shortcut_help(self):
        """显示快捷键说明"""
        from src.gui.dialogs import ShortcutHelpDialog
        dialog = ShortcutHelpDialog(self, theme=self.user_settings.theme)
        dialog.exec()
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
    
    def closeEvent(self, event):
        if hasattr(self, '_force_quit') and self._force_quit:
            msg, state = MascotMessageHelper.farewell()
            self._show_mascot_message(msg, duration=1500, state=state)
            self._perform_exit_cleanup()
            event.accept()
            return
        
        if hasattr(self, '_is_closing') and self._is_closing:
            event.accept()
            return
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("确认退出")
        msg_box.setText("确定要退出程序吗？\n\n选择\"退出\"将完全关闭程序\n选择\"最小化到后台\"将隐藏窗口继续运行")
        
        close_btn = msg_box.addButton("退出", QMessageBox.ButtonRole.AcceptRole)
        minimize_btn = msg_box.addButton("最小化到后台", QMessageBox.ButtonRole.ActionRole)
        cancel_btn = msg_box.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(close_btn)
        
        msg_box.exec()
        
        clicked_btn = msg_box.clickedButton()
        
        if clicked_btn == minimize_btn:
            self.hide()
            self._tray_icon.showMessage(
                "B站缓存视频下载工具",
                "程序已最小化到系统托盘，双击图标可恢复窗口",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
            event.ignore()
        elif clicked_btn == close_btn:
            self._force_quit = True
            msg, state = MascotMessageHelper.farewell()
            self._show_mascot_message(msg, duration=1500, state=state)
            self._perform_exit_cleanup()
            event.accept()
        else:
            event.ignore()
    
    def changeEvent(self, event):
        """处理窗口状态改变事件"""
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized():
                event.accept()
                QTimer.singleShot(0, self._minimize_to_tray)
                return
        super().changeEvent(event)
    
    def _minimize_to_tray(self):
        """最小化到系统托盘"""
        self.hide()
        self._tray_icon.showMessage(
            "B站缓存视频下载工具",
            "程序已最小化到系统托盘，双击图标可恢复窗口",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
    
    def _perform_exit_cleanup(self):
        """执行退出清理"""
        self._consistency_timer.stop()
        self._is_closing = True
        self._show_closing_animation()
        QTimer.singleShot(100, self._perform_cleanup)

    def _show_closing_animation(self):
        """显示关闭动画"""
        from PyQt6.QtGui import QColor, QPalette

        self._closing_overlay = QWidget(self)
        self._closing_overlay.setGeometry(self.rect())
        self._closing_overlay.setAutoFillBackground(True)

        palette = self._closing_overlay.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(45, 45, 45, 0))
        self._closing_overlay.setPalette(palette)

        layout = QVBoxLayout(self._closing_overlay)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._closing_kaomoji = QLabel(KaomojiHelper.CLOSING[0])
        self._closing_kaomoji.setStyleSheet("""
            QLabel { color: #4CAF50; font-size: 48px; font-weight: bold; background: transparent; }
        """)
        self._closing_kaomoji.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._closing_kaomoji)

        self._closing_dots = QLabel("...")
        self._closing_dots.setStyleSheet("""
            QLabel { color: #4CAF50; font-size: 64px; font-weight: bold; background: transparent; }
        """)
        self._closing_dots.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._closing_dots)

        self._closing_status = QLabel("准备关闭...")
        self._closing_status.setStyleSheet("""
            QLabel { color: #aaaaaa; font-size: 24px; background: transparent; margin-top: 30px; }
        """)
        self._closing_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._closing_status)

        self._closing_overlay.show()
        self._closing_overlay.raise_()

        self._kaomoji_list = KaomojiHelper.CLOSING
        self._kaomoji_index = 0
        self._kaomoji_timer = QTimer(self)
        self._kaomoji_timer.timeout.connect(self._update_closing_kaomoji)
        self._kaomoji_timer.start(400)

        self._dot_count = 0
        self._dot_timer = QTimer(self)
        self._dot_timer.timeout.connect(self._update_closing_dots)
        self._dot_timer.start(250)

    def _update_closing_kaomoji(self):
        if not hasattr(self, '_closing_kaomoji') or self._closing_kaomoji is None:
            return
        self._kaomoji_index = (self._kaomoji_index + 1) % len(self._kaomoji_list)
        self._closing_kaomoji.setText(self._kaomoji_list[self._kaomoji_index])

    def _update_closing_dots(self):
        if not hasattr(self, '_closing_dots') or self._closing_dots is None:
            return
        self._dot_count = (self._dot_count + 1) % 4
        dots = "." * self._dot_count + " " * (3 - self._dot_count)
        self._closing_dots.setText(dots)

    def _update_closing_status(self, status: str):
        if hasattr(self, '_closing_status') and self._closing_status is not None:
            self._closing_status.setText(status)

    def _perform_cleanup(self):
        try:
            self._update_closing_status("正在保存用户设置...")
            self._save_user_settings()

            self._update_closing_status("正在恢复设备设置...")
            self._restore_all_devices_screen()

            self._update_closing_status("正在停止封面加载...")
            self._cover_loader.stop()

            self._update_closing_status("正在停止视频加载...")
            if self._video_load_worker and self._video_load_worker.isRunning():
                self._video_load_worker.stop()

            self._update_closing_status("正在停止设备监控...")
            self.device_manager.stop_monitoring()

            self._update_closing_status("正在停止下载服务...")
            self.file_transfer.stop_fast()

            self._update_closing_status("正在关闭数据库...")
            self.db.close()

            self._update_closing_status("完成！")

        except Exception as e:
            self.logger.error(f"清理过程出错: {e}")

        if hasattr(self, '_kaomoji_timer'):
            self._kaomoji_timer.stop()
        if hasattr(self, '_dot_timer'):
            self._dot_timer.stop()

        QTimer.singleShot(400, self._do_close)

    def _save_user_settings(self):
        """保存用户设置"""
        try:
            current_download_dir = self.video_panel.get_download_dir()
            if current_download_dir:
                self.user_settings.download_dir = current_download_dir
            
            self.user_settings.max_concurrent_downloads = self.config.MAX_CONCURRENT_DOWNLOADS
            
            geometry = self.saveGeometry()
            state = self.saveState()
            self.settings_service.save_window_state(geometry, state)
            
            self.settings_service.save()
            self.logger.info("用户设置已保存")
        except Exception as e:
            self.logger.error(f"保存用户设置失败: {e}")
    
    def _restore_window_state(self):
        """恢复窗口状态"""
        try:
            geometry, state = self.settings_service.load_window_state()
            if geometry:
                self.restoreGeometry(geometry)
            if state:
                self.restoreState(state)
            self.logger.info("窗口状态已恢复")
        except Exception as e:
            self.logger.warning(f"恢复窗口状态失败: {e}")

    def _restore_all_devices_screen(self):
        try:
            devices = self.device_manager.get_online_devices()
            for device in devices:
                try:
                    self.adb_service.restore_screen_timeout(device.device_id)
                except Exception as e:
                    self.logger.warning(f"恢复设备 {device.device_id} 屏幕设置失败: {e}")
        except Exception as e:
            self.logger.error(f"恢复设备屏幕设置失败: {e}")

    def _do_close(self):
        if hasattr(self, '_kaomoji_timer') and self._kaomoji_timer:
            self._kaomoji_timer.stop()
            self._kaomoji_timer = None
        if hasattr(self, '_dot_timer') and self._dot_timer:
            self._dot_timer.stop()
            self._dot_timer = None

        if hasattr(self, '_closing_overlay') and self._closing_overlay is not None:
            self._closing_overlay.deleteLater()
            self._closing_overlay = None
        
        if hasattr(self, '_tray_icon') and self._tray_icon:
            self._tray_icon.hide()
            self._tray_icon = None

        QApplication.quit()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
