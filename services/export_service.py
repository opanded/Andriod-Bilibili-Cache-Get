import csv
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime


class ExportService:
    """数据导出服务"""
    
    def export_to_csv(self, videos: List[Any], file_path: str) -> bool:
        if not videos:
            return False
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                fieldnames = [
                    'video_id', 'title', 'owner_name', 'duration', 
                    'file_size', 'download_status', 'local_path',
                    'download_time', 'device_id', 'bvid'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for video in videos:
                    row = {
                        'video_id': getattr(video, 'video_id', ''),
                        'title': getattr(video, 'title', ''),
                        'owner_name': getattr(video, 'owner_name', ''),
                        'duration': self._format_duration(getattr(video, 'duration', 0)),
                        'file_size': self._format_size(getattr(video, 'file_size', 0)),
                        'download_status': getattr(video, 'download_status', 'not_downloaded'),
                        'local_path': getattr(video, 'local_path', ''),
                        'download_time': self._format_datetime(getattr(video, 'download_time', None)),
                        'device_id': getattr(video, 'device_id', ''),
                        'bvid': getattr(video, 'bvid', '')
                    }
                    writer.writerow(row)
            
            return True
        except Exception as e:
            print(f"CSV导出失败: {e}")
            return False
    
    def export_to_json(self, videos: List[Any], file_path: str) -> bool:
        if not videos:
            return False
        
        try:
            data = []
            for video in videos:
                video_dict = {
                    'video_id': getattr(video, 'video_id', ''),
                    'title': getattr(video, 'title', ''),
                    'owner_name': getattr(video, 'owner_name', ''),
                    'owner_id': getattr(video, 'owner_id', ''),
                    'duration': getattr(video, 'duration', 0),
                    'file_size': getattr(video, 'file_size', 0),
                    'download_status': getattr(video, 'download_status', 'not_downloaded'),
                    'local_path': getattr(video, 'local_path', ''),
                    'all_local_paths': getattr(video, 'all_local_paths', None),
                    'download_time': self._format_datetime(getattr(video, 'download_time', None)),
                    'device_id': getattr(video, 'device_id', ''),
                    'bvid': getattr(video, 'bvid', ''),
                    'total_episodes': getattr(video, 'total_episodes', 1),
                    'cover_path': getattr(video, 'cover_path', '')
                }
                data.append(video_dict)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'export_time': datetime.now().isoformat(),
                    'total_count': len(data),
                    'videos': data
                }, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"JSON导出失败: {e}")
            return False
    
    def _format_duration(self, seconds: int) -> str:
        if not seconds:
            return "0:00"
        minutes, secs = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"
    
    def _format_size(self, size: int) -> str:
        if not size:
            return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def _format_datetime(self, dt) -> str:
        if not dt:
            return ""
        if isinstance(dt, str):
            return dt
        return dt.strftime('%Y-%m-%d %H:%M:%S')
