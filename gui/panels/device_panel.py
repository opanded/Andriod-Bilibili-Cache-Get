from typing import List

from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor

from src.models.device import Device


class DevicePanel(QGroupBox):
    device_selected = pyqtSignal(object)
    refresh_requested = pyqtSignal()
    wireless_connect_requested = pyqtSignal()

    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self._devices: List[Device] = []
        self._theme = theme
        self._init_ui()
        self._apply_theme()

    def _init_ui(self):
        self.setTitle("📱 设备列表")
        layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 刷新设备")
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        btn_layout.addWidget(self.refresh_btn)

        self.wireless_btn = QPushButton("📶 添加无线设备")
        self.wireless_btn.clicked.connect(self._on_wireless_clicked)
        btn_layout.addWidget(self.wireless_btn)

        layout.addLayout(btn_layout)

        self.device_list = QListWidget()
        self.device_list.itemClicked.connect(self._on_device_item_clicked)
        layout.addWidget(self.device_list)

        self.info_label = QLabel("未选择设备")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #aaaaaa; padding: 10px;")
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def apply_theme(self, theme: str):
        """应用主题"""
        self._theme = theme
        self._apply_theme()

    def _apply_theme(self):
        """应用主题"""
        if self._theme == 'light':
            self._apply_light_theme()
        else:
            self._apply_dark_theme()
    
    def _apply_light_theme(self):
        """应用浅色主题"""
        self.setStyleSheet("""
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
                padding: 8px 14px;
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
                color: #999999;
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
            }
        """)
        self.info_label.setStyleSheet("color: #666666; padding: 10px;")
    
    def _apply_dark_theme(self):
        """应用深色主题"""
        self.setStyleSheet("""
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
        """)
        self.info_label.setStyleSheet("color: #aaaaaa; padding: 10px;")

    def _on_refresh_clicked(self):
        self.refresh_requested.emit()

    def _on_wireless_clicked(self):
        self.wireless_connect_requested.emit()

    def _on_device_item_clicked(self, item: QListWidgetItem):
        device = item.data(Qt.ItemDataRole.UserRole)
        if device:
            self._update_info_label(device)
            self.device_selected.emit(device)

    def _update_info_label(self, device: Device):
        info_text = f"📱 {device.display_name}\n"
        info_text += f"厂商: {device.device_manufacturer or '未知'}\n"
        info_text += f"Android: {device.android_version or '未知'}\n"
        info_text += f"B站版本: {device.bili_version or '未安装'}"
        self.info_label.setText(info_text)

    def set_devices(self, devices: List[Device]):
        self._devices = devices
        self.device_list.clear()

        for device in devices:
            item = QListWidgetItem()
            display_text = f"📱 {device.display_name}"
            if device.has_bilibili:
                display_text += " ✓B站"
            else:
                display_text += " ✗无B站"
            item.setText(display_text)
            item.setData(Qt.ItemDataRole.UserRole, device)
            if not device.has_bilibili:
                item.setForeground(QColor("#ff9800"))
            self.device_list.addItem(item)

    def set_info(self, info: str):
        self.info_label.setText(info)

    def get_selected_device(self) -> Device:
        current_item = self.device_list.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None

    def clear_selection(self):
        self.device_list.clearSelection()
        self.info_label.setText("未选择设备")
