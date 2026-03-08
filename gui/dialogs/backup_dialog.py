"""数据备份对话框模块"""
import os
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QProgressBar, QGroupBox, QCheckBox,
    QMessageBox, QWidget, QTabWidget, QLineEdit, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class ExportWorker(QThread):
    """导出工作线程"""
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, backup_service, export_path, include_downloads):
        super().__init__()
        self.backup_service = backup_service
        self.export_path = export_path
        self.include_downloads = include_downloads
    
    def run(self):
        success, message = self.backup_service.export_data(
            self.export_path,
            self.include_downloads,
            progress_callback=self._on_progress
        )
        self.finished.emit(success, message)
    
    def _on_progress(self, current, total, msg):
        self.progress.emit(current, total, msg)


class ImportWorker(QThread):
    """导入工作线程"""
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, backup_service, import_path, restore_settings, restore_database):
        super().__init__()
        self.backup_service = backup_service
        self.import_path = import_path
        self.restore_settings = restore_settings
        self.restore_database = restore_database
    
    def run(self):
        success, message = self.backup_service.import_data(
            self.import_path,
            self.restore_settings,
            self.restore_database,
            progress_callback=self._on_progress
        )
        self.finished.emit(success, message)
    
    def _on_progress(self, current, total, msg):
        self.progress.emit(current, total, msg)


class BackupDialog(QDialog):
    """数据备份对话框"""
    
    def __init__(self, backup_service, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self.backup_service = backup_service
        self.worker = None
        self._theme = theme
        
        self.setWindowTitle("数据备份管理")
        self.setMinimumSize(550, 450)
        self.resize(600, 500)
        
        self._init_ui()
        self._apply_theme()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        tab_widget = QTabWidget()
        
        export_tab = self._create_export_tab()
        tab_widget.addTab(export_tab, "📤 导出数据")
        
        import_tab = self._create_import_tab()
        tab_widget.addTab(import_tab, "📥 导入数据")
        
        layout.addWidget(tab_widget)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _create_export_tab(self) -> QWidget:
        """创建导出标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        info_group = QGroupBox("导出说明")
        info_layout = QVBoxLayout(info_group)
        info_label = QLabel(
            "导出功能将备份以下内容：\n"
            "• 数据库文件（设备信息、视频信息、下载记录）\n"
            "• 用户设置（下载目录、窗口状态等）\n"
            "• 可选：已下载的视频文件"
        )
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        layout.addWidget(info_group)
        
        path_group = QGroupBox("导出设置")
        path_layout = QVBoxLayout(path_group)
        
        path_row = QHBoxLayout()
        path_label = QLabel("导出路径:")
        path_label.setFixedWidth(80)
        self.export_path_edit = QLineEdit()
        self.export_path_edit.setPlaceholderText("选择导出文件保存位置...")
        self.export_path_edit.setReadOnly(True)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_export_path)
        
        path_row.addWidget(path_label)
        path_row.addWidget(self.export_path_edit)
        path_row.addWidget(browse_btn)
        path_layout.addLayout(path_row)
        
        self.include_downloads_cb = QCheckBox("包含已下载的视频文件（会增加备份大小）")
        self.include_downloads_cb.setChecked(False)
        path_layout.addWidget(self.include_downloads_cb)
        
        layout.addWidget(path_group)
        
        self.export_progress_group = QGroupBox("导出进度")
        progress_layout = QVBoxLayout(self.export_progress_group)
        
        self.export_progress_bar = QProgressBar()
        self.export_progress_bar.setRange(0, 100)
        self.export_progress_bar.setValue(0)
        progress_layout.addWidget(self.export_progress_bar)
        
        self.export_status_label = QLabel("准备就绪")
        self.export_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.export_status_label)
        
        self.export_progress_group.setVisible(False)
        layout.addWidget(self.export_progress_group)
        
        layout.addStretch()
        
        export_btn = QPushButton("开始导出")
        export_btn.setFixedHeight(40)
        export_btn.clicked.connect(self._start_export)
        layout.addWidget(export_btn)
        
        default_name = f"bili_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        default_path = Path.home() / "Desktop" / default_name
        if not default_path.parent.exists():
            default_path = Path.home() / default_name
        self.export_path_edit.setText(str(default_path))
        
        return widget
    
    def _create_import_tab(self) -> QWidget:
        """创建导入标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        info_group = QGroupBox("导入说明")
        info_layout = QVBoxLayout(info_group)
        info_label = QLabel(
            "导入功能将恢复以下内容：\n"
            "• 数据库文件（将覆盖现有数据）\n"
            "• 用户设置（将覆盖现有设置）\n"
            "⚠️ 导入前建议先备份当前数据"
        )
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        layout.addWidget(info_group)
        
        file_group = QGroupBox("选择备份文件")
        file_layout = QVBoxLayout(file_group)
        
        file_row = QHBoxLayout()
        file_label = QLabel("备份文件:")
        file_label.setFixedWidth(80)
        self.import_path_edit = QLineEdit()
        self.import_path_edit.setPlaceholderText("选择要导入的备份文件...")
        self.import_path_edit.setReadOnly(True)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_import_path)
        
        file_row.addWidget(file_label)
        file_row.addWidget(self.import_path_edit)
        file_row.addWidget(browse_btn)
        file_layout.addLayout(file_row)
        
        layout.addWidget(file_group)
        
        restore_group = QGroupBox("恢复选项")
        restore_layout = QVBoxLayout(restore_group)
        
        self.restore_settings_cb = QCheckBox("恢复用户设置")
        self.restore_settings_cb.setChecked(True)
        restore_layout.addWidget(self.restore_settings_cb)
        
        self.restore_database_cb = QCheckBox("恢复数据库")
        self.restore_database_cb.setChecked(True)
        restore_layout.addWidget(self.restore_database_cb)
        
        layout.addWidget(restore_group)
        
        self.backup_info_text = QTextEdit()
        self.backup_info_text.setReadOnly(True)
        self.backup_info_text.setMaximumHeight(100)
        self.backup_info_text.setPlaceholderText("选择备份文件后将显示详细信息...")
        layout.addWidget(self.backup_info_text)
        
        self.import_progress_group = QGroupBox("导入进度")
        progress_layout = QVBoxLayout(self.import_progress_group)
        
        self.import_progress_bar = QProgressBar()
        self.import_progress_bar.setRange(0, 100)
        self.import_progress_bar.setValue(0)
        progress_layout.addWidget(self.import_progress_bar)
        
        self.import_status_label = QLabel("准备就绪")
        self.import_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.import_status_label)
        
        self.import_progress_group.setVisible(False)
        layout.addWidget(self.import_progress_group)
        
        layout.addStretch()
        
        import_btn = QPushButton("开始导入")
        import_btn.setFixedHeight(40)
        import_btn.clicked.connect(self._start_import)
        layout.addWidget(import_btn)
        
        return widget
    
    def _apply_theme(self):
        """应用主题"""
        if self._theme == 'light':
            self._apply_light_theme()
        else:
            self._apply_dark_theme()
    
    def _apply_light_theme(self):
        """应用浅色主题"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
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
            QLabel {
                color: #1a1a1a;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                padding: 8px;
                color: #1a1a1a;
            }
            QLineEdit:read-only {
                background-color: #e8e8e8;
            }
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #a0a0a0;
                border-radius: 5px;
                padding: 10px 18px;
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
            QProgressBar {
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                text-align: center;
                background-color: #e0e0e0;
                color: #1a1a1a;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
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
            QTabWidget::pane {
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #e8e8e8;
                border: 2px solid #c0c0c0;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                padding: 10px 18px;
                color: #1a1a1a;
            }
            QTabBar::tab:selected {
                background-color: #2196F3;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #d0d0d0;
            }
            QTextEdit {
                background-color: #ffffff;
                border: 2px solid #c0c0c0;
                border-radius: 5px;
                color: #1a1a1a;
            }
        """)
    
    def _apply_dark_theme(self):
        """应用深色主题"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
            }
            QGroupBox {
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
            }
            QLineEdit:read-only {
                background-color: #353535;
            }
            QPushButton {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px 16px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            QPushButton:pressed {
                background-color: #5d5d5d;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 4px;
                text-align: center;
                background-color: #3d3d3d;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
            QCheckBox {
                color: #ffffff;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QTabWidget::pane {
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #2d2d2d;
            }
            QTabBar::tab {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 16px;
                color: #ffffff;
            }
            QTabBar::tab:selected {
                background-color: #2196F3;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #4d4d4d;
            }
            QTextEdit {
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 4px;
                color: #ffffff;
            }
        """)
    
    def _browse_export_path(self):
        """浏览导出路径"""
        default_name = f"bili_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "选择导出位置",
            self.export_path_edit.text() or str(Path.home() / default_name),
            "ZIP文件 (*.zip)"
        )
        if path:
            self.export_path_edit.setText(path)
    
    def _browse_import_path(self):
        """浏览导入路径"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择备份文件",
            str(Path.home()),
            "ZIP文件 (*.zip)"
        )
        if path:
            self.import_path_edit.setText(path)
            self._load_backup_info(path)
    
    def _load_backup_info(self, path: str):
        """加载备份文件信息"""
        info = self.backup_service.get_backup_info(path)
        if info:
            created_at = info.get('created_at', '未知')
            if created_at != '未知':
                try:
                    dt = datetime.fromisoformat(created_at)
                    created_at = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            info_text = (
                f"📋 备份信息\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"版本: {info.get('version', '未知')}\n"
                f"创建时间: {created_at}\n"
                f"应用版本: {info.get('app_version', '未知')}\n"
                f"文件大小: {info.get('file_size_mb', 0):.2f} MB\n"
                f"包含下载文件: {'是' if info.get('includes_downloads') else '否'}"
            )
            self.backup_info_text.setText(info_text)
        else:
            self.backup_info_text.setText("⚠️ 无法读取备份文件信息，文件可能已损坏")
    
    def _start_export(self):
        """开始导出"""
        export_path = self.export_path_edit.text().strip()
        if not export_path:
            QMessageBox.warning(self, "提示", "请选择导出路径")
            return
        
        include_downloads = self.include_downloads_cb.isChecked()
        
        if include_downloads:
            reply = QMessageBox.question(
                self,
                "确认",
                "包含已下载的视频文件可能会使备份文件非常大。\n\n确定要继续吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self.export_progress_group.setVisible(True)
        self.export_progress_bar.setValue(0)
        self.export_status_label.setText("正在导出...")
        
        self.worker = ExportWorker(
            self.backup_service,
            export_path,
            include_downloads
        )
        self.worker.progress.connect(self._on_export_progress)
        self.worker.finished.connect(self._on_export_finished)
        self.worker.start()
    
    def _on_export_progress(self, current: int, total: int, message: str):
        """导出进度更新"""
        self.export_progress_bar.setValue(current)
        self.export_status_label.setText(message)
    
    def _on_export_finished(self, success: bool, message: str):
        """导出完成"""
        if success:
            self.export_status_label.setText("✅ 导出成功！")
            QMessageBox.information(self, "导出成功", message)
        else:
            self.export_status_label.setText("❌ 导出失败")
            QMessageBox.warning(self, "导出失败", message)
        
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
    
    def _start_import(self):
        """开始导入"""
        import_path = self.import_path_edit.text().strip()
        if not import_path:
            QMessageBox.warning(self, "提示", "请选择要导入的备份文件")
            return
        
        if not Path(import_path).exists():
            QMessageBox.warning(self, "提示", "备份文件不存在")
            return
        
        restore_settings = self.restore_settings_cb.isChecked()
        restore_database = self.restore_database_cb.isChecked()
        
        if not restore_settings and not restore_database:
            QMessageBox.warning(self, "提示", "请至少选择一项要恢复的内容")
            return
        
        reply = QMessageBox.question(
            self,
            "确认导入",
            "导入将覆盖现有数据，此操作不可撤销！\n\n确定要继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.import_progress_group.setVisible(True)
        self.import_progress_bar.setValue(0)
        self.import_status_label.setText("正在导入...")
        
        self.worker = ImportWorker(
            self.backup_service,
            import_path,
            restore_settings,
            restore_database
        )
        self.worker.progress.connect(self._on_import_progress)
        self.worker.finished.connect(self._on_import_finished)
        self.worker.start()
    
    def _on_import_progress(self, current: int, total: int, message: str):
        """导入进度更新"""
        self.import_progress_bar.setValue(current)
        self.import_status_label.setText(message)
    
    def _on_import_finished(self, success: bool, message: str):
        """导入完成"""
        if success:
            self.import_status_label.setText("✅ 导入成功！")
            QMessageBox.information(self, "导入成功", message)
        else:
            self.import_status_label.setText("❌ 导入失败")
            QMessageBox.warning(self, "导入失败", message)
        
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "确认关闭",
                "正在执行操作，确定要取消吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            
            self.worker.terminate()
            self.worker.wait()
        
        event.accept()
