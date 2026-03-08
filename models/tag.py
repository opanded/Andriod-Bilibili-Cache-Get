from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Optional


class VideoTag(Base):
    """视频标签表"""
    __tablename__ = 'video_tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    color = Column(String(7), default='#2196F3')
    created_at = Column(DateTime, default=datetime.now)
    
    videos = relationship('VideoTagRelation', back_populates='tag')


class VideoTagRelation(Base):
    """视频-标签关联表"""
    __tablename__ = 'video_tag_relations'
    
    id = Column(Integer, primary_key=True)
    video_id = Column(String, ForeignKey('videos.video_id'), nullable=False)
    tag_id = Column(Integer, ForeignKey('video_tags.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    video = relationship('VideoModel', back_populates='tags')
    tag = relationship('VideoTag', back_populates='videos')
    
    __table_args__ = (
        Table('unique_video_tag', {'video_id', 'tag_id'}),
    )
