"""设备数据模型"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Device:
    """设备数据类"""
    device_id: str
    device_name: Optional[str] = None
    device_serial: Optional[str] = None
    device_manufacturer: Optional[str] = None
    market_name: Optional[str] = None
    android_version: Optional[str] = None
    bili_version: Optional[str] = None
    connection_type: str = 'usb'
    connection_status: str = 'offline'
    bilibili_installed: int = -1
    bilibili_check_time: Optional[datetime] = None
    last_seen_time: Optional[datetime] = None

    @property
    def is_online(self) -> bool:
        return self.connection_status == 'online'

    @property
    def has_bilibili(self) -> bool:
        return self.bilibili_installed == 1

    @property
    def display_name(self) -> str:
        if self.market_name and self.market_name != 'Unknown':
            return self.market_name
        if self.device_name:
            return self.device_name
        return self.device_id
