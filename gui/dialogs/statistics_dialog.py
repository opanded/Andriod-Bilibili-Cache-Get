from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QGridLayout, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Dict, Any, List


class StatisticsDialog(QDialog):
    """下载统计对话框"""
    
    def __init__(self, statistics_service, parent=None):
        super().__init__(parent)
        self.statistics_service = statistics_service
        self.setWindowTitle("下载统计")
        self.setMinimumSize(600, 500)
        self._init_ui()
        self._load_statistics()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        layout.addWidget(self._create_overall_group())
        
        layout.addWidget(self._create_history_group())
        
        layout.addWidget(self._create_device_group())
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._load_statistics)
        btn_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_overall_group(self) -> QGroupBox:
        group = QGroupBox("视频统计")
        layout = QGridLayout(group)
        
        self.overall_labels = {}
        
        stats = [
            ('total_videos', '总视频数'),
            ('completed', '已完成'),
            ('failed', '失败'),
            ('downloading', '下载中'),
            ('not_downloaded', '未下载'),
            ('total_size_formatted', '总大小'),
            ('total_duration_formatted', '总时长'),
            ('success_rate', '成功率')
        ]
        
        for i, (key, label) in enumerate(stats):
            row, col = i // 4, (i % 4) * 2
            label_widget = QLabel(f"{label}:")
            label_widget.setStyleSheet("color: #888;")
            layout.addWidget(label_widget, row, col)
            
            value_label = QLabel("-")
            value_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            layout.addWidget(value_label, row, col + 1)
            self.overall_labels[key] = value_label
        
        return group
    
    def _create_history_group(self) -> QGroupBox:
        group = QGroupBox("下载历史统计")
        layout = QGridLayout(group)
        
        self.history_labels = {}
        
        stats = [
            ('total_downloads', '总下载次数'),
            ('completed', '完成'),
            ('failed', '失败'),
            ('cancelled', '取消'),
            ('total_size_formatted', '总大小'),
            ('total_duration_formatted', '总时长')
        ]
        
        for i, (key, label) in enumerate(stats):
            row, col = i // 3, (i % 3) * 2
            label_widget = QLabel(f"{label}:")
            label_widget.setStyleSheet("color: #888;")
            layout.addWidget(label_widget, row, col)
            
            value_label = QLabel("-")
            value_label.setStyleSheet("font-weight: bold;")
            layout.addWidget(value_label, row, col + 1)
            self.history_labels[key] = value_label
        
        return group
    
    def _create_device_group(self) -> QGroupBox:
        group = QGroupBox("设备统计")
        layout = QVBoxLayout(group)
        
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(4)
        self.device_table.setHorizontalHeaderLabels(['设备ID', '视频数', '已完成', '总大小'])
        self.device_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.device_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.device_table)
        
        return group
    
    def _load_statistics(self):
        overall = self.statistics_service.get_overall_statistics()
        for key, label in self.overall_labels.items():
            value = overall.get(key, '-')
            if key == 'success_rate':
                label.setText(f"{value}%")
            else:
                label.setText(str(value))
        
        history = self.statistics_service.get_history_statistics()
        for key, label in self.history_labels.items():
            value = history.get(key, '-')
            label.setText(str(value))
        
        devices = self.statistics_service.get_statistics_by_device()
        self.device_table.setRowCount(len(devices))
        for i, device in enumerate(devices):
            self.device_table.setItem(i, 0, QTableWidgetItem(device.get('device_id', '-')))
            self.device_table.setItem(i, 1, QTableWidgetItem(str(device.get('total', 0))))
            self.device_table.setItem(i, 2, QTableWidgetItem(str(device.get('completed', 0))))
            size = device.get('size', 0)
            self.device_table.setItem(i, 3, QTableWidgetItem(self._format_size(size)))
    
    def _format_size(self, size: int) -> str:
        if not size:
            return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
