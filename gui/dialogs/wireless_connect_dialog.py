import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QWidget, QTabWidget, QTabBar
)
from PyQt6.QtCore import pyqtSignal, Qt, QThread, QRegularExpression
from PyQt6.QtGui import QIntValidator, QRegularExpressionValidator

import logging

logger = logging.getLogger(__name__)


class PairWorker(QThread):
    pair_finished = pyqtSignal(bool, str)

    def __init__(self, adb_service, ip: str, port: int, code: str):
        super().__init__()
        self.adb_service = adb_service
        self.ip = ip
        self.port = port
        self.code = code

    def run(self):
        try:
            success = self.adb_service.pair_wireless(self.ip, self.port, self.code)
            if success:
                self.pair_finished.emit(True, f"配对成功: {self.ip}:{self.port}")
            else:
                self.pair_finished.emit(False, "配对失败，请检查配对码是否正确")
        except Exception as e:
            self.pair_finished.emit(False, f"配对错误: {str(e)}")


class ConnectionTestWorker(QThread):
    test_finished = pyqtSignal(bool, str)

    def __init__(self, adb_service, ip: str, port: int):
        super().__init__()
        self.adb_service = adb_service
        self.ip = ip
        self.port = port

    def run(self):
        try:
            success = self.adb_service.connect_wireless(self.ip, self.port)
            if success:
                device_id = f"{self.ip}:{self.port}"
                if self.adb_service.test_connection(device_id):
                    self.test_finished.emit(True, f"连接成功: {device_id}")
                else:
                    self.test_finished.emit(False, "连接建立但设备无响应")
            else:
                self.test_finished.emit(False, "无法连接到设备")
        except Exception as e:
            self.test_finished.emit(False, f"连接错误: {str(e)}")


class WirelessConnectDialog(QDialog):
    pair_requested = pyqtSignal(str, int, str)
    connection_requested = pyqtSignal(str, int)

    test_connection_requested = pyqtSignal(str, int)

    
    def __init__(self, adb_service=None, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self.adb_service = adb_service
        self._pair_worker = None
        self._test_worker = None
        self._theme = theme
        self._init_ui()
        self._apply_theme()

    def _init_ui(self):
        self.setWindowTitle("无线设备连接")
        self.setMinimumWidth(400)
        self.setModal(True)

        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self._create_pair_tab(), "配对新设备")
        self.tab_widget.addTab(self._create_connect_tab(), "连接已配对设备")
        layout.addWidget(self.tab_widget)
        
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #aaaaaa; padding: 5px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)

    def _create_pair_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        info_label = QLabel("在设备上开启无线调试后，会显示配对码和输入以下信息：")
        info_label.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(info_label)
        
        ip_label = QLabel("IP地址:")
        self.pair_ip_input = QLineEdit()
        self.pair_ip_input.setPlaceholderText("例如: 192.168.1.100")
        ip_regex = QRegularExpressionValidator(
            QRegularExpression(r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
        )
        self.pair_ip_input.setValidator(ip_regex)
        layout.addWidget(ip_label)
        layout.addWidget(self.pair_ip_input)
        
        port_label = QLabel("配对端口:")
        self.pair_port_input = QLineEdit()
        self.pair_port_input.setPlaceholderText("例如: 37123")
        port_validator = QIntValidator(1, 65535)
        self.pair_port_input.setValidator(port_validator)
        layout.addWidget(port_label)
        layout.addWidget(self.pair_port_input)
        
        code_label = QLabel("配对码 (6位数字):")
        self.pair_code_input = QLineEdit()
        self.pair_code_input.setPlaceholderText("例如: 123456")
        self.pair_code_input.setMaxLength(6)
        code_regex = QRegularExpressionValidator(QRegularExpression(r"^\d{6}$"))
        self.pair_code_input.setValidator(code_regex)
        layout.addWidget(code_label)
        layout.addWidget(self.pair_code_input)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.pair_btn = QPushButton("配对")
        self.pair_btn.clicked.connect(self._on_pair_clicked)
        self.pair_btn.setEnabled(False)
        btn_layout.addWidget(self.pair_btn)
        
        layout.addLayout(btn_layout)
        
        self.pair_ip_input.textChanged.connect(self._validate_pair_inputs)
        self.pair_port_input.textChanged.connect(self._validate_pair_inputs)
        self.pair_code_input.textChanged.connect(self._validate_pair_inputs)
        
        widget.setLayout(layout)
        return widget

    def _create_connect_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        ip_label = QLabel("IP地址:")
        self.connect_ip_input = QLineEdit()
        self.connect_ip_input.setPlaceholderText("例如: 192.168.1.100")
        ip_regex = QRegularExpressionValidator(
            QRegularExpression(r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
        )
        self.connect_ip_input.setValidator(ip_regex)
        layout.addWidget(ip_label)
        layout.addWidget(self.connect_ip_input)
        
        port_label = QLabel("端口:")
        self.connect_port_input = QLineEdit()
        self.connect_port_input.setText("5555")
        self.connect_port_input.setPlaceholderText("默认: 5555")
        port_validator = QIntValidator(1, 65535)
        self.connect_port_input.setValidator(port_validator)
        layout.addWidget(port_label)
        layout.addWidget(self.connect_port_input)
        
        test_btn_layout = QHBoxLayout()
        self.test_btn = QPushButton("🔍 测试连接")
        self.test_btn.clicked.connect(self._on_test_clicked)
        test_btn_layout.addWidget(self.test_btn)
        layout.addLayout(test_btn_layout)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.connect_btn = QPushButton("连接")
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        self.connect_btn.setEnabled(False)
        btn_layout.addWidget(self.connect_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.connect_ip_input.textChanged.connect(self._validate_connect_inputs)
        self.connect_port_input.textChanged.connect(self._validate_connect_inputs)
        
        widget.setLayout(layout)
        return widget

    def _apply_theme(self):
        if self._theme == 'light':
            self._apply_light_theme()
        else:
            self._apply_dark_theme()
    
    def _apply_light_theme(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QLabel {
                color: #1a1a1a;
                font-size: 12px;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                padding: 10px;
                color: #1a1a1a;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #a0a0a0;
                border-radius: 5px;
                padding: 10px 18px;
                color: #1a1a1a;
                font-size: 12px;
                min-width: 80px;
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
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: #f0f0f0;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                color: #1a1a1a;
                padding: 8px 16px;
            }
            QTabBar::tab:selected {
                background-color: #f0f0f0;
                color: #2196F3;
            }
        """)
    
    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            QLineEdit {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px 16px;
                color: #ffffff;
                font-size: 12px;
                min-width: 80px;
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
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #2d2d2d;
            }
            QTabBar::tab {
                background-color: #3d3d3d;
                color: #ffffff;
                padding: 8px 16px;
            }
            QTabBar::tab:selected {
                background-color: #2d2d2d;
                color: #2196F3;
            }
        """)

    def _validate_pair_inputs(self):
        ip = self.pair_ip_input.text().strip()
        port_text = self.pair_port_input.text().strip()
        code = self.pair_code_input.text().strip()
        
        ip_valid = bool(re.match(
            r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
            ip
        ))
        
        port_valid = False
        if port_text:
            try:
                port = int(port_text)
                port_valid = 1 <= port <= 65535
            except ValueError:
                pass
        
        code_valid = len(code) == 6 and code.isdigit()
        
        self.pair_btn.setEnabled(ip_valid and port_valid and code_valid)

    
    def _validate_connect_inputs(self):
        ip = self.connect_ip_input.text().strip()
        port_text = self.connect_port_input.text().strip()
        
        ip_valid = bool(re.match(
            r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
            ip
        ))
        
        port_valid = False
        if port_text:
            try:
                port = int(port_text)
                port_valid = 1 <= port <= 65535
            except ValueError:
                pass
        
        self.connect_btn.setEnabled(ip_valid and port_valid)
        self.test_btn.setEnabled(ip_valid and port_valid and self.adb_service is not None)

    
    def _get_port(self, port_input: QLineEdit) -> int:
        port_text = port_input.text().strip()
        if port_text:
            try:
                return int(port_text)
            except ValueError:
                pass
        return 5555
    
    def _set_status(self, message: str, error: bool = False):
        color = "#f44336" if error else "#4CAF50"
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; padding: 5px;")
    
    def _on_pair_clicked(self):
        ip = self.pair_ip_input.text().strip()
        port = self._get_port(self.pair_port_input)
        code = self.pair_code_input.text().strip()
        
        if not ip:
            self._set_status("请输入IP地址", error=True)
            return
        
        if not code:
            self._set_status("请输入配对码", error=True)
            return
        
        
        self._set_status("正在配对...", error=False)
        self.pair_btn.setEnabled(False)
        
        self._pair_worker = PairWorker(self.adb_service, ip, port, code)
        self._pair_worker.pair_finished.connect(self._on_pair_finished)
        self._pair_worker.start()
    
    def _on_pair_finished(self, success: bool, message: str):
        self._set_status(message, error=not success)
        self.pair_btn.setEnabled(True)
        
        if success:
            self.connect_ip_input.setText(self.pair_ip_input.text())
            self.connect_port_input.setText("5555")
            self.tab_widget.setCurrentIndex(1)
    
    def _on_test_clicked(self):
        ip = self.connect_ip_input.text().strip()
        port = self._get_port(self.connect_port_input)
        
        if not ip:
            self._set_status("请输入IP地址", error=True)
            return
        
        
        self._set_status("正在测试连接...", error=False)
        self.test_btn.setEnabled(False)
        self.connect_btn.setEnabled(False)
        
        self._test_worker = ConnectionTestWorker(self.adb_service, ip, port)
        self._test_worker.test_finished.connect(self._on_test_finished)
        self._test_worker.start()
    
    def _on_test_finished(self, success: bool, message: str):
        self._set_status(message, error=not success)
        self.test_btn.setEnabled(True)
        self._validate_connect_inputs()
        
        if success:
            self.connect_btn.setEnabled(True)
    
    def _on_connect_clicked(self):
        ip = self.connect_ip_input.text().strip()
        port = self._get_port(self.connect_port_input)
        
        if not ip:
            self._set_status("请输入IP地址", error=True)
            return
        
        self.connection_requested.emit(ip, port)
        self.accept()
