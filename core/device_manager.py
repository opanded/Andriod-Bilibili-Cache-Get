"""设备管理模块"""
import threading
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime

from ..interfaces import IEventPublisher, IDeviceService
from ..models.device import Device
from ..models.database import Database, DeviceModel
from ..services.adb_service import ADBService

logger = logging.getLogger(__name__)


class DeviceManager(IDeviceService):
    """设备管理核心类 - 实现 IDeviceService 接口"""

    def __init__(self, config, adb_service: ADBService,
                 event_publisher: IEventPublisher, db: Database):
        self.config = config
        self.adb_service = adb_service
        self.event_publisher = event_publisher
        self.db = db

        self._monitor_thread: Optional[threading.Thread] = None
        self._monitoring = False
        self._devices: Dict[str, Device] = {}
        self._lock = threading.Lock()

        self._load_devices_from_db()

    def _load_devices_from_db(self):
        """从数据库加载设备列表"""
        try:
            with self.db.session() as session:
                devices = DeviceModel.get_all(session)
                for device_model in devices:
                    device = Device(
                        device_id=device_model.device_id,
                        device_name=device_model.device_name,
                        device_serial=device_model.device_serial,
                        device_manufacturer=device_model.device_manufacturer,
                        market_name=device_model.market_name,
                        android_version=device_model.android_version,
                        bili_version=device_model.bili_version,
                        connection_type=device_model.connection_type,
                        connection_status=device_model.connection_status,
                        bilibili_installed=device_model.bilibili_installed,
                        bilibili_check_time=device_model.bilibili_check_time,
                        last_seen_time=device_model.last_seen_time
                    )
                    self._devices[device.device_id] = device
                logger.info(f"从数据库加载了 {len(devices)} 个设备")
        except Exception as e:
            logger.error(f"从数据库加载设备失败: {e}")

    def start_monitoring(self):
        """启动设备监控"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("设备监控已启动")

    def stop_monitoring(self):
        """停止设备监控"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("设备监控已停止")

    def _monitor_loop(self):
        """设备监控循环"""
        while self._monitoring:
            try:
                self._check_devices()
            except Exception as e:
                logger.error(f"设备检查出错: {e}")

            time.sleep(self.config.DEVICE_CHECK_INTERVAL)

    def _check_devices(self):
        """检查设备状态"""
        connected_devices = self.adb_service.get_devices()
        connected_ids = {d['device_id'] for d in connected_devices if d.get('status') == 'device'}

        with self._lock:
            for device_info in connected_devices:
                device_id = device_info.get('device_id')
                status = device_info.get('status')

                if status != 'device':
                    continue

                if device_id in self._devices:
                    if self._devices[device_id].connection_status != 'online':
                        self._update_device_status(device_id, 'online')
                    continue

                if ':' in device_id:
                    try:
                        serial = self.adb_service.get_device_serial(device_id)
                        if serial:
                            matched_device_id = self._find_device_by_serial(serial)
                            if matched_device_id:
                                logger.info(f"设备 {matched_device_id} 重新连接为 {device_id}")
                                self._update_device_id(matched_device_id, device_id)
                                self._update_device_status(device_id, 'online')
                                continue
                    except Exception as e:
                        logger.warning(f"获取设备序列号失败: {e}")

                self._add_new_device(device_id, device_info)

            for device_id, device in list(self._devices.items()):
                if device.connection_status == 'online' and device_id not in connected_ids:
                    self._update_device_status(device_id, 'offline')

        self.event_publisher.publish('device.list_updated', self.get_online_devices())

    def _find_device_by_serial(self, serial: str) -> Optional[str]:
        """通过序列号查找设备ID"""
        for device_id, device in self._devices.items():
            if device.device_serial == serial:
                return device_id
        return None

    def _update_device_id(self, old_id: str, new_id: str):
        """更新设备ID"""
        if old_id in self._devices:
            device = self._devices[old_id]
            device.device_id = new_id
            self._devices[new_id] = device
            del self._devices[old_id]
            logger.info(f"设备ID更新: {old_id} -> {new_id}")

            with self.db.session() as session:
                from ..models.database import VideoModel
                DeviceModel.save_or_update(session, device)
                VideoModel.update_device_id(session, old_id, new_id)

    def _add_new_device(self, device_id: str, device_info: dict):
        """添加新设备"""
        logger.info(f"发现新设备: {device_id}")

        info = self.adb_service.get_device_info(device_id)

        bili_installed = -1
        bili_version = None
        try:
            if self.adb_service.check_package_installed(device_id, self.config.BILI_PACKAGE_NAME):
                bili_installed = 1
                bili_version = self.adb_service.get_package_version(device_id, self.config.BILI_PACKAGE_NAME)
            else:
                bili_installed = 0
        except Exception as e:
            logger.warning(f"检查B站安装状态失败: {e}")

        market_name = info.get('market_name')
        model = info.get('model')
        device_display_name = market_name if market_name and market_name != 'Unknown' else model

        device = Device(
            device_id=device_id,
            device_name=device_display_name,
            device_serial=info.get('serial'),
            device_manufacturer=info.get('manufacturer'),
            market_name=market_name,
            android_version=info.get('android_version'),
            bili_version=bili_version,
            connection_type='usb',
            connection_status='online',
            bilibili_installed=bili_installed,
            bilibili_check_time=datetime.now() if bili_installed != -1 else None,
            last_seen_time=datetime.now()
        )

        self._devices[device_id] = device

        with self.db.session() as session:
            DeviceModel.save_or_update(session, device)

        try:
            self.adb_service.keep_screen_on(device_id)
        except Exception as e:
            logger.warning(f"设置屏幕常亮失败: {e}")

        self.event_publisher.publish('device.connected', device)
        if bili_installed != -1:
            self.event_publisher.publish('device.bilibili_status', {
                'device_id': device_id,
                'installed': bili_installed == 1
            })

    def _update_device_status(self, device_id: str, status: str):
        """更新设备状态"""
        if device_id in self._devices:
            device = self._devices[device_id]
            device.connection_status = status

            if status == 'online':
                device.last_seen_time = datetime.now()
                logger.info(f"设备重新连接: {device_id}")
                self.event_publisher.publish('device.connected', device)
            else:
                logger.info(f"设备断开连接: {device_id}")
                self.event_publisher.publish('device.disconnected', device_id)

            with self.db.session() as session:
                DeviceModel.save_or_update(session, device)

    def get_online_devices(self) -> List[Device]:
        """获取在线设备列表"""
        with self._lock:
            return [d for d in self._devices.values() if d.is_online]

    def get_all_devices(self) -> List[Device]:
        """获取所有设备列表"""
        with self._lock:
            return list(self._devices.values())

    def get_device(self, device_id: str) -> Optional[Device]:
        """获取指定设备"""
        with self._lock:
            return self._devices.get(device_id)

    def check_bilibili_installed(self, device_id: str) -> bool:
        """检查设备是否安装了B站"""
        device = self.get_device(device_id)
        if not device:
            return False

        if device.bilibili_installed != -1:
            return device.has_bilibili

        try:
            installed = self.adb_service.check_package_installed(
                device_id, self.config.BILI_PACKAGE_NAME
            )
            device.bilibili_installed = 1 if installed else 0
            device.bilibili_check_time = datetime.now()

            if installed:
                device.bili_version = self.adb_service.get_package_version(
                    device_id, self.config.BILI_PACKAGE_NAME
                )

            with self.db.session() as session:
                DeviceModel.save_or_update(session, device)

            self.event_publisher.publish('device.bilibili_status', {
                'device_id': device_id,
                'installed': installed
            })

            return installed
        except Exception as e:
            logger.error(f"检查B站安装状态失败: {e}")
            return False

    def verify_connection(self, device_id: str) -> bool:
        """验证设备连接是否有效"""
        try:
            devices = self.adb_service.get_devices()
            for d in devices:
                if ':' in device_id and ':' in d['device_id']:
                    device_ip = device_id.split(':')[0]
                    current_ip = d['device_id'].split(':')[0]
                    if device_ip == current_ip and d.get('status') == 'device':
                        return True
                elif d['device_id'] == device_id and d.get('status') == 'device':
                    return True
            return False
        except Exception as e:
            logger.error(f"验证设备连接失败: {e}")
            return False

    def cleanup_expired_devices(self, days: int = 30) -> int:
        """清理过期设备"""
        try:
            with self.db.session() as session:
                count = DeviceModel.delete_expired(session, days)

            self._devices.clear()
            self._load_devices_from_db()

            logger.info(f"清理了 {count} 个过期设备")
            return count
        except Exception as e:
            logger.error(f"清理过期设备失败: {e}")
            return 0

    def refresh_devices(self):
        """立即刷新设备列表"""
        self._check_devices()
