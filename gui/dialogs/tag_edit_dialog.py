from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QColorDialog, QMenu, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from typing import List, Dict, Optional


class TagEditDialog(QDialog):
    """标签编辑对话框"""
    
    tags_updated = pyqtSignal()
    
    def __init__(self, tag_service, video_id: str = None, parent=None):
        super().__init__(parent)
        self.tag_service = tag_service
        self.video_id = video_id
        self.setWindowTitle("标签管理")
        self.setMinimumSize(400, 500)
        self._init_ui()
        self._load_tags()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("所有标签:"))
        
        self.tag_list = QListWidget()
        self.tag_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tag_list.customContextMenuRequested.connect(self._show_tag_context_menu)
        self.tag_list.itemClicked.connect(self._on_tag_clicked)
        layout.addWidget(self.tag_list)
        
        add_layout = QHBoxLayout()
        self.new_tag_input = QLineEdit()
        self.new_tag_input.setPlaceholderText("新标签名称")
        add_layout.addWidget(self.new_tag_input)
        
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(30, 30)
        self.color_btn.setStyleSheet("background-color: #2196F3; border: none;")
        self._selected_color = "#2196F3"
        self.color_btn.clicked.connect(self._select_color)
        add_layout.addWidget(self.color_btn)
        
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self._add_tag)
        add_layout.addWidget(add_btn)
        
        layout.addLayout(add_layout)
        
        if self.video_id:
            layout.addWidget(QLabel(f"视频标签:"))
            
            self.video_tag_list = QListWidget()
            layout.addWidget(self.video_tag_list)
            
            manage_layout = QHBoxLayout()
            add_to_video_btn = QPushButton("添加到视频")
            add_to_video_btn.clicked.connect(self._add_tag_to_video)
            manage_layout.addWidget(add_to_video_btn)
            
            remove_from_video_btn = QPushButton("从视频移除")
            remove_from_video_btn.clicked.connect(self._remove_tag_from_video)
            manage_layout.addWidget(remove_from_video_btn)
            
            layout.addLayout(manage_layout)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_tags(self):
        """加载标签列表"""
        tags = self.tag_service.get_all_tags()
        self.tag_list.clear()
        
        for tag in tags:
            item = QListWidgetItem(tag['name'])
            item.setData(Qt.ItemDataRole.UserRole, tag['id'])
            item.setForeground(QColor(tag['color']))
            self.tag_list.addItem(item)
        
        if self.video_id:
            video_tags = self.tag_service.get_video_tags(self.video_id)
            self.video_tag_list.clear()
            for tag in video_tags:
                item = QListWidgetItem(tag['name'])
                item.setData(Qt.ItemDataRole.UserRole, tag['id'])
                item.setForeground(QColor(tag['color']))
                self.video_tag_list.addItem(item)
    
    def _select_color(self):
        """选择颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            self._selected_color = color.name()
            self.color_btn.setStyleSheet(f"background-color: {self._selected_color}; border: none;")
    
    def _add_tag(self):
        """添加新标签"""
        name = self.new_tag_input.text.strip()
        if not name:
            return
        
        tag_id = self.tag_service.create_tag(name, self._selected_color)
        if tag_id:
            self.new_tag_input.clear()
            self._load_tags()
            self.tags_updated.emit()
    
    def _on_tag_clicked(self, item):
        """标签点击事件"""
        tag_id = item.data(Qt.ItemDataRole.UserRole)
        tag = next((t for t in self.tag_service.get_all_tags() if t['id'] == tag_id), None)
        if tag:
            self._selected_color = tag['color']
            self.color_btn.setStyleSheet(f"background-color: {self._selected_color}; border: none;")
    
    def _show_tag_context_menu(self, pos):
        """显示标签右键菜单"""
        item = self.tag_list.itemAt(pos)
        if not item:
            return
        
        tag_id = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        edit_action = menu.addAction("编辑")
        delete_action = menu.addAction("删除")
        
        edit_action.triggered.connect(lambda: self._edit_tag(tag_id))
        delete_action.triggered.connect(lambda: self._delete_tag(tag_id))
        
        menu.exec(self.tag_list.mapToGlobal(pos))
    
    def _edit_tag(self, tag_id: int):
        """编辑标签"""
        pass
    
    def _delete_tag(self, tag_id: int):
        """删除标签"""
        self.tag_service.delete_tag(tag_id)
        self._load_tags()
        self.tags_updated.emit()
    
    def _add_tag_to_video(self):
        """添加标签到视频"""
        if not self.video_id:
            return
        
        current_item = self.tag_list.currentItem()
        if not current_item:
            return
        
        tag_id = current_item.data(Qt.ItemDataRole.UserRole)
        self.tag_service.add_tag_to_video(self.video_id, tag_id)
        self._load_tags()
        self.tags_updated.emit()
    
    def _remove_tag_from_video(self):
        """从视频移除标签"""
        if not self.video_id:
            return
        
        current_item = self.video_tag_list.currentItem()
        if not current_item:
            return
        
        tag_id = current_item.data(Qt.ItemDataRole.UserRole)
        self.tag_service.remove_tag_from_video(self.video_id, tag_id)
        self._load_tags()
        self.tags_updated.emit()
