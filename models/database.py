"""数据库模块 - 使用上下文管理器管理会话"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

Base = declarative_base()


class Database:
    """数据库管理类 - 使用上下文管理器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)
        self._migrate_schema()
        logger.info("数据库表创建完成")

    def _migrate_schema(self):
        """数据库迁移 - 添加缺失的列和索引"""
        from sqlalchemy import text
        
        migrations = [
            ("download_tasks", "video_title", "VARCHAR"),
            ("download_tasks", "error_category", "VARCHAR"),
            ("download_tasks", "temp_dir", "VARCHAR"),
            ("download_tasks", "all_local_paths", "TEXT"),
            ("download_tasks", "file_size", "INTEGER"),
            ("download_tasks", "duration", "INTEGER"),
            ("download_tasks", "priority", "INTEGER"),
            ("download_tasks", "retry_count", "INTEGER"),
            ("download_tasks", "started_at", "DATETIME"),
            ("download_tasks", "completed_at", "DATETIME"),
        ]
        
        with self.engine.connect() as conn:
            for table, column, col_type in migrations:
                try:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                    conn.commit()
                    logger.info(f"数据库迁移: 添加列 {table}.{column}")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        pass
                    else:
                        logger.debug(f"迁移跳过 {table}.{column}: {e}")
            
            self._migrate_indexes(conn)
    
    def _migrate_indexes(self, conn):
        """迁移索引 - 为已有数据库添加索引"""
        index_migrations = [
            ("ix_videos_device_id", "videos", "device_id"),
            ("ix_videos_download_status", "videos", "download_status"),
            ("ix_videos_device_status", "videos", "device_id, download_status"),
        ]
        
        for index_name, table, columns in index_migrations:
            try:
                conn.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({columns})"))
                conn.commit()
                logger.info(f"数据库迁移: 创建索引 {index_name}")
            except Exception as e:
                logger.debug(f"索引迁移跳过 {index_name}: {e}")

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """获取数据库会话（上下文管理器）

        用法:
            with db.session() as session:
                session.query(...)
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()

    def get_session(self) -> Session:
        """获取数据库会话（需要手动关闭）"""
        return self.SessionLocal()

    def close(self):
        """关闭数据库连接"""
        self.engine.dispose()
        logger.info("数据库连接已关闭")


class DeviceModel(Base):
    """设备数据模型"""
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, unique=True, nullable=False)
    device_name = Column(String)
    device_serial = Column(String)
    device_manufacturer = Column(String)
    market_name = Column(String)
    android_version = Column(String)
    bili_version = Column(String)
    connection_type = Column(String)
    connection_status = Column(String)
    bilibili_installed = Column(Integer, default=-1)
    bilibili_check_time = Column(DateTime)
    last_seen_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self) -> dict:
        return {
            'device_id': self.device_id,
            'device_name': self.device_name,
            'device_serial': self.device_serial,
            'device_manufacturer': self.device_manufacturer,
            'market_name': self.market_name,
            'android_version': self.android_version,
            'bili_version': self.bili_version,
            'connection_type': self.connection_type,
            'connection_status': self.connection_status,
            'bilibili_installed': self.bilibili_installed,
            'last_seen_time': self.last_seen_time
        }

    @classmethod
    def get_all(cls, session: Session) -> List['DeviceModel']:
        return session.query(cls).all()

    @classmethod
    def get_by_id(cls, session: Session, device_id: str) -> Optional['DeviceModel']:
        return session.query(cls).filter(cls.device_id == device_id).first()

    @classmethod
    def save_or_update(cls, session: Session, device) -> 'DeviceModel':
        model = cls.get_by_id(session, device.device_id)
        if model:
            model.device_name = device.device_name
            model.device_serial = device.device_serial
            model.device_manufacturer = device.device_manufacturer
            model.market_name = getattr(device, 'market_name', None)
            model.android_version = device.android_version
            model.bili_version = device.bili_version
            model.connection_type = device.connection_type
            model.connection_status = device.connection_status
            model.bilibili_installed = device.bilibili_installed
            model.bilibili_check_time = device.bilibili_check_time
            model.last_seen_time = device.last_seen_time or datetime.now()
        else:
            model = cls(
                device_id=device.device_id,
                device_name=device.device_name,
                device_serial=device.device_serial,
                device_manufacturer=device.device_manufacturer,
                market_name=getattr(device, 'market_name', None),
                android_version=device.android_version,
                bili_version=device.bili_version,
                connection_type=device.connection_type,
                connection_status=device.connection_status,
                bilibili_installed=device.bilibili_installed,
                bilibili_check_time=device.bilibili_check_time,
                last_seen_time=device.last_seen_time or datetime.now()
            )
            session.add(model)
        return model

    @classmethod
    def delete_expired(cls, session: Session, days: int) -> int:
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        count = session.query(cls).filter(
            cls.connection_status == 'offline',
            cls.last_seen_time < cutoff
        ).delete()
        return count


class VideoModel(Base):
    """视频数据模型"""
    __tablename__ = 'videos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String, nullable=False)
    bvid = Column(String)
    title = Column(Text)
    description = Column(Text)
    owner_id = Column(String)
    owner_name = Column(String)
    cover_path = Column(String)
    duration = Column(Integer)
    file_size = Column(Integer, default=0)
    video_quality = Column(Integer)
    video_quality_text = Column(String)
    episode_number = Column(Integer)
    total_episodes = Column(Integer, default=1)
    upload_time = Column(DateTime)
    cache_path = Column(String)
    cache_video_path = Column(String)
    cache_audio_path = Column(String)
    cache_info_path = Column(String)
    device_id = Column(String, ForeignKey('devices.device_id'), nullable=False)
    download_status = Column(String, default='not_downloaded')
    local_path = Column(String)
    all_local_paths = Column(Text)
    download_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint('video_id', 'device_id', name='uix_video_device'),
        Index('ix_videos_device_id', 'device_id'),
        Index('ix_videos_download_status', 'download_status'),
        Index('ix_videos_device_status', 'device_id', 'download_status'),
    )

    def to_dict(self) -> dict:
        return {
            'video_id': self.video_id,
            'bvid': self.bvid,
            'title': self.title,
            'description': self.description,
            'owner_id': self.owner_id,
            'owner_name': self.owner_name,
            'cover_path': self.cover_path,
            'duration': self.duration,
            'file_size': self.file_size,
            'video_quality': self.video_quality,
            'video_quality_text': self.video_quality_text,
            'episode_number': self.episode_number,
            'total_episodes': self.total_episodes,
            'cache_path': self.cache_path,
            'device_id': self.device_id,
            'download_status': self.download_status,
            'local_path': self.local_path,
            'all_local_paths': json.loads(self.all_local_paths) if self.all_local_paths else None,
            'download_time': self.download_time
        }

    @classmethod
    def get_by_video_and_device(cls, session: Session, video_id: str, device_id: str) -> Optional['VideoModel']:
        return session.query(cls).filter(
            cls.video_id == video_id,
            cls.device_id == device_id
        ).first()

    @classmethod
    def get_by_device(cls, session: Session, device_id: str) -> List['VideoModel']:
        return session.query(cls).filter(cls.device_id == device_id).all()

    @classmethod
    def save_or_update(cls, session: Session, video) -> 'VideoModel':
        model = cls.get_by_video_and_device(session, video.video_id, video.device_id)
        if model:
            model.bvid = video.bvid
            model.title = video.title
            model.description = getattr(video, 'description', None)
            model.owner_id = video.owner_id
            model.owner_name = video.owner_name
            model.cover_path = video.cover_path
            model.duration = video.duration
            model.file_size = video.file_size or 0
            model.video_quality = video.video_quality
            model.video_quality_text = video.video_quality_text
            model.episode_number = getattr(video, 'episode_number', 1)
            model.total_episodes = video.total_episodes
            model.cache_path = video.cache_path
            model.cache_video_path = getattr(video, 'cache_video_path', None)
            model.cache_audio_path = getattr(video, 'cache_audio_path', None)
            model.cache_info_path = getattr(video, 'cache_info_path', None)
            if hasattr(video, 'upload_time') and video.upload_time:
                model.upload_time = video.upload_time
            if hasattr(video, 'download_status'):
                model.download_status = video.download_status
            if hasattr(video, 'local_path') and video.local_path:
                model.local_path = video.local_path
            if hasattr(video, 'all_local_paths') and video.all_local_paths:
                model.all_local_paths = json.dumps(video.all_local_paths)
            if hasattr(video, 'download_time') and video.download_time:
                model.download_time = video.download_time
        else:
            model = cls(
                video_id=video.video_id,
                bvid=video.bvid,
                title=video.title,
                description=getattr(video, 'description', None),
                owner_id=video.owner_id,
                owner_name=video.owner_name,
                cover_path=video.cover_path,
                duration=video.duration,
                file_size=video.file_size or 0,
                video_quality=video.video_quality,
                video_quality_text=video.video_quality_text,
                episode_number=getattr(video, 'episode_number', 1),
                total_episodes=video.total_episodes,
                upload_time=getattr(video, 'upload_time', None),
                cache_path=video.cache_path,
                cache_video_path=getattr(video, 'cache_video_path', None),
                cache_audio_path=getattr(video, 'cache_audio_path', None),
                cache_info_path=getattr(video, 'cache_info_path', None),
                device_id=video.device_id,
                download_status=getattr(video, 'download_status', 'not_downloaded'),
                local_path=getattr(video, 'local_path', None),
                all_local_paths=json.dumps(video.all_local_paths) if hasattr(video, 'all_local_paths') and video.all_local_paths else None
            )
            session.add(model)
        return model

    @classmethod
    def update_download_status(cls, session: Session, video_id: str, device_id: str,
                               status: str, local_path: Optional[str] = None,
                               all_local_paths: Optional[List[str]] = None) -> bool:
        model = cls.get_by_video_and_device(session, video_id, device_id)
        if model:
            model.download_status = status
            if local_path:
                model.local_path = local_path
            if all_local_paths:
                model.all_local_paths = json.dumps(all_local_paths)
            if status == 'completed':
                model.download_time = datetime.now()
            return True
        return False

    @classmethod
    def update_device_id(cls, session: Session, old_id: str, new_id: str) -> int:
        count = session.query(cls).filter(cls.device_id == old_id).update(
            {cls.device_id: new_id}
        )
        return count


class DownloadHistoryModel(Base):
    """下载历史数据模型"""
    __tablename__ = 'download_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String, nullable=False)
    video_title = Column(String)
    device_id = Column(String)
    local_path = Column(String)
    all_local_paths = Column(Text)
    file_size = Column(Integer, default=0)
    duration = Column(Integer, default=0)
    status = Column(String, default='completed')
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'video_id': self.video_id,
            'video_title': self.video_title,
            'device_id': self.device_id,
            'local_path': self.local_path,
            'all_local_paths': json.loads(self.all_local_paths) if self.all_local_paths else None,
            'file_size': self.file_size,
            'duration': self.duration,
            'status': self.status,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def get_all(cls, session: Session, limit: int = 100, offset: int = 0) -> List['DownloadHistoryModel']:
        return session.query(cls).order_by(cls.completed_at.desc()).limit(limit).offset(offset).all()

    @classmethod
    def get_by_id(cls, session: Session, history_id: int) -> Optional['DownloadHistoryModel']:
        return session.query(cls).filter(cls.id == history_id).first()

    @classmethod
    def get_by_video_id(cls, session: Session, video_id: str) -> List['DownloadHistoryModel']:
        return session.query(cls).filter(cls.video_id == video_id).order_by(cls.completed_at.desc()).all()

    @classmethod
    def delete_by_id(cls, session: Session, history_id: int) -> bool:
        count = session.query(cls).filter(cls.id == history_id).delete()
        return count > 0

    @classmethod
    def clear_all(cls, session: Session) -> int:
        count = session.query(cls).delete()
        return count

    @classmethod
    def get_statistics(cls, session: Session) -> dict:
        from sqlalchemy import func
        total = session.query(func.count(cls.id)).scalar() or 0
        completed = session.query(func.count(cls.id)).filter(
            cls.status == 'completed'
        ).scalar() or 0
        failed = session.query(func.count(cls.id)).filter(
            cls.status == 'failed'
        ).scalar() or 0
        cancelled = session.query(func.count(cls.id)).filter(
            cls.status == 'cancelled'
        ).scalar() or 0
        total_size = session.query(func.sum(cls.file_size)).filter(
            cls.status == 'completed'
        ).scalar() or 0
        return {
            'total': total,
            'completed': completed,
            'failed': failed,
            'cancelled': cancelled,
            'total_size': total_size
        }


class DownloadTaskModel(Base):
    """下载任务数据模型"""
    __tablename__ = 'download_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, unique=True, nullable=False)
    video_id = Column(String, nullable=False)
    device_id = Column(String, nullable=False)
    video_title = Column(String)
    status = Column(String, default='pending')
    progress = Column(Float, default=0)
    error_message = Column(Text)
    error_category = Column(String)
    temp_dir = Column(String)
    local_path = Column(String)
    all_local_paths = Column(Text)
    file_size = Column(Integer, default=0)
    duration = Column(Integer, default=0)
    priority = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self) -> dict:
        return {
            'task_id': self.task_id,
            'video_id': self.video_id,
            'device_id': self.device_id,
            'video_title': self.video_title,
            'status': self.status,
            'progress': self.progress,
            'error_message': self.error_message,
            'error_category': self.error_category,
            'local_path': self.local_path,
            'all_local_paths': json.loads(self.all_local_paths) if self.all_local_paths else None,
            'file_size': self.file_size,
            'duration': self.duration,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def get_pending_tasks(cls, session: Session) -> List['DownloadTaskModel']:
        return session.query(cls).filter(
            cls.status.in_(['pending', 'paused', 'downloading', 'queued'])
        ).all()

    @classmethod
    def get_history(cls, session: Session, status: str = None, 
                    limit: int = 100, offset: int = 0) -> List['DownloadTaskModel']:
        query = session.query(cls).order_by(cls.completed_at.desc())
        if status:
            query = query.filter(cls.status == status)
        return query.limit(limit).offset(offset).all()

    @classmethod
    def get_statistics(cls, session: Session) -> dict:
        from sqlalchemy import func
        total = session.query(func.count(cls.id)).scalar() or 0
        completed = session.query(func.count(cls.id)).filter(
            cls.status == 'completed'
        ).scalar() or 0
        failed = session.query(func.count(cls.id)).filter(
            cls.status == 'failed'
        ).scalar() or 0
        cancelled = session.query(func.count(cls.id)).filter(
            cls.status == 'cancelled'
        ).scalar() or 0
        total_size = session.query(func.sum(cls.file_size)).filter(
            cls.status == 'completed'
        ).scalar() or 0
        return {
            'total': total,
            'completed': completed,
            'failed': failed,
            'cancelled': cancelled,
            'total_size': total_size
        }

    @classmethod
    def get_recent(cls, session: Session, days: int = 7) -> List['DownloadTaskModel']:
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        return session.query(cls).filter(
            cls.completed_at >= cutoff
        ).order_by(cls.completed_at.desc()).all()

    @classmethod
    def get_by_task_id(cls, session: Session, task_id: str) -> Optional['DownloadTaskModel']:
        return session.query(cls).filter(cls.task_id == task_id).first()

    @classmethod
    def delete_by_task_id(cls, session: Session, task_id: str) -> bool:
        count = session.query(cls).filter(cls.task_id == task_id).delete()
        return count > 0

    @classmethod
    def cleanup_completed(cls, session: Session, days: int = 7) -> int:
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        count = session.query(cls).filter(
            cls.status.in_(['completed', 'cancelled']),
            cls.completed_at < cutoff
        ).delete()
        return count
