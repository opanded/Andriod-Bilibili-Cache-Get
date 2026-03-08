from typing import List, Optional, Dict
from sqlalchemy.orm import Session


class TagService:
    """标签管理服务"""
    
    def __init__(self, db):
        self.db = db
    
    def get_all_tags(self) -> List[Dict]:
        """获取所有标签"""
        with self.db.session() as session:
            from src.models.tag import VideoTag
            tags = session.query(VideoTag).order_by(VideoTag.name).all()
            return [
                {
                    'id': tag.id,
                    'name': tag.name,
                    'color': tag.color,
                    'video_count': len(tag.videos)
                }
                for tag in tags
            ]
    
    def create_tag(self, name: str, color: str = '#2196F3') -> Optional[int]:
        """创建标签"""
        with self.db.session() as session:
            from src.models.tag import VideoTag
            try:
                tag = VideoTag(name=name, color=color)
                session.add(tag)
                session.commit()
                return tag.id
            except Exception as e:
                session.rollback()
                return None
    
    def delete_tag(self, tag_id: int) -> bool:
        """删除标签"""
        with self.db.session() as session:
            from src.models.tag import VideoTag
            tag = session.query(VideoTag).filter(VideoTag.id == tag_id).first()
            if tag:
                session.delete(tag)
                session.commit()
                return True
            return False
    
    def add_tag_to_video(self, video_id: str, tag_id: int) -> bool:
        """为视频添加标签"""
        with self.db.session() as session:
            from src.models.tag import VideoTagRelation
            try:
                relation = VideoTagRelation(video_id=video_id, tag_id=tag_id)
                session.add(relation)
                session.commit()
                return True
            except Exception:
                session.rollback()
                return False
    
    def remove_tag_from_video(self, video_id: str, tag_id: int) -> bool:
        """移除视频标签"""
        with self.db.session() as session:
            from src.models.tag import VideoTagRelation
            relation = session.query(VideoTagRelation).filter(
                VideoTagRelation.video_id == video_id,
                VideoTagRelation.tag_id == tag_id
            ).first()
            if relation:
                session.delete(relation)
                session.commit()
                return True
            return False
    
    def get_video_tags(self, video_id: str) -> List[Dict]:
        """获取视频的所有标签"""
        with self.db.session() as session:
            from src.models.tag import VideoTagRelation, VideoTag
            relations = session.query(VideoTagRelation).filter(
                VideoTagRelation.video_id == video_id
            ).all()
            return [
                {
                    'id': rel.tag.id,
                    'name': rel.tag.name,
                    'color': rel.tag.color
                }
                for rel in relations
            ]
    
    def get_videos_by_tag(self, tag_id: int) -> List[str]:
        """获取标签下的所有视频ID"""
        with self.db.session() as session:
            from src.models.tag import VideoTagRelation
            relations = session.query(VideoTagRelation).filter(
                VideoTagRelation.tag_id == tag_id
            ).all()
            return [rel.video_id for rel in relations]
    
    def update_tag(self, tag_id: int, name: str = None, color: str = None) -> bool:
        """更新标签"""
        with self.db.session() as session:
            from src.models.tag import VideoTag
            tag = session.query(VideoTag).filter(VideoTag.id == tag_id).first()
            if tag:
                if name:
                    tag.name = name
                if color:
                    tag.color = color
                session.commit()
                return True
            return False
