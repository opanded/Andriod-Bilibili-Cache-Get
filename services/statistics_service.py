from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func


class StatisticsService:
    """下载统计服务"""
    
    def __init__(self, db):
        self.db = db
    
    def get_overall_statistics(self) -> Dict[str, Any]:
        """获取总体统计"""
        try:
            with self.db.session() as session:
                from src.models.database import VideoModel, DownloadHistoryModel
                
                videos = session.query(VideoModel).all()
                
                total = len(videos)
                completed = sum(1 for v in videos if v.download_status == 'completed')
                failed = sum(1 for v in videos if v.download_status == 'failed')
                downloading = sum(1 for v in videos if v.download_status == 'downloading')
                not_downloaded = sum(1 for v in videos if v.download_status == 'not_downloaded')
                
                total_size = sum(v.file_size or 0 for v in videos if v.download_status == 'completed')
                total_duration = sum(v.duration or 0 for v in videos if v.download_status == 'completed')
                
                success_rate = (completed / total * 100) if total > 0 else 0
                
                return {
                    'total_videos': total,
                    'completed': completed,
                    'failed': failed,
                    'downloading': downloading,
                    'not_downloaded': not_downloaded,
                    'total_size': total_size,
                    'total_size_formatted': self._format_size(total_size),
                    'total_duration': total_duration,
                    'total_duration_formatted': self._format_duration(total_duration),
                    'success_rate': round(success_rate, 1)
                }
        except Exception as e:
            return self._empty_statistics()
    
    def get_history_statistics(self) -> Dict[str, Any]:
        """获取历史统计"""
        try:
            with self.db.session() as session:
                from src.models.database import DownloadHistoryModel
                
                history = session.query(DownloadHistoryModel).all()
                
                total = len(history)
                completed = sum(1 for h in history if h.status == 'completed')
                failed = sum(1 for h in history if h.status == 'failed')
                cancelled = sum(1 for h in history if h.status == 'cancelled')
                
                total_size = sum(h.file_size or 0 for h in history if h.status == 'completed')
                total_duration = sum(h.duration or 0 for h in history if h.status == 'completed')
                
                return {
                    'total_downloads': total,
                    'completed': completed,
                    'failed': failed,
                    'cancelled': cancelled,
                    'total_size': total_size,
                    'total_size_formatted': self._format_size(total_size),
                    'total_duration': total_duration,
                    'total_duration_formatted': self._format_duration(total_duration)
                }
        except Exception as e:
            return self._empty_statistics()
    
    def get_statistics_by_date(self, days: int = 30) -> List[Dict]:
        """按日期统计"""
        try:
            with self.db.session() as session:
                from src.models.database import DownloadHistoryModel
                
                start_date = datetime.now() - timedelta(days=days)
                
                history = session.query(DownloadHistoryModel).filter(
                    DownloadHistoryModel.completed_at >= start_date
                ).all()
                
                date_stats = {}
                for h in history:
                    if h.completed_at:
                        date_str = h.completed_at.strftime('%Y-%m-%d')
                        if date_str not in date_stats:
                            date_stats[date_str] = {'count': 0, 'size': 0}
                        date_stats[date_str]['count'] += 1
                        date_stats[date_str]['size'] += h.file_size or 0
                
                return [
                    {'date': k, 'count': v['count'], 'size': v['size']}
                    for k, v in sorted(date_stats.items())
                ]
        except Exception as e:
            return []
    
    def get_statistics_by_device(self) -> List[Dict]:
        """按设备统计"""
        try:
            with self.db.session() as session:
                from src.models.database import VideoModel
                
                videos = session.query(VideoModel).all()
                
                device_stats = {}
                for v in videos:
                    device_id = v.device_id or 'unknown'
                    if device_id not in device_stats:
                        device_stats[device_id] = {'total': 0, 'completed': 0, 'size': 0}
                    device_stats[device_id]['total'] += 1
                    if v.download_status == 'completed':
                        device_stats[device_id]['completed'] += 1
                        device_stats[device_id]['size'] += v.file_size or 0
                
                return [
                    {'device_id': k, **v}
                    for k, v in device_stats.items()
                ]
        except Exception as e:
            return []
    
    def _empty_statistics(self) -> Dict[str, Any]:
        return {
            'total_videos': 0,
            'completed': 0,
            'failed': 0,
            'downloading': 0,
            'not_downloaded': 0,
            'total_size': 0,
            'total_size_formatted': '0 B',
            'total_duration': 0,
            'total_duration_formatted': '0:00',
            'success_rate': 0.0
        }
    
    def _format_size(self, size: int) -> str:
        if not size:
            return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
    
    def _format_duration(self, seconds: int) -> str:
        if not seconds:
            return "0:00"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"
