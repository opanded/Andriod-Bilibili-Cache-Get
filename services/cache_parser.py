"""B站缓存结构解析模块"""
import json
import logging
import tempfile
import shutil
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from ..models.video import Video

logger = logging.getLogger(__name__)


class CacheParser:
    """B站缓存解析器"""

    def __init__(self, adb_service, cache_base_path: str = "/sdcard/Android/data/tv.danmaku.bili/download"):
        self.adb_service = adb_service
        self.cache_base_path = cache_base_path
        self._local_cache_dir: Optional[Path] = None

    def _get_local_cache_dir(self, device_id: str) -> Path:
        if self._local_cache_dir is None:
            safe_device_id = device_id.replace(':', '_').replace('/', '_').replace('\\', '_')
            temp_dir = Path(tempfile.gettempdir()) / "bili_cache_get_v02" / safe_device_id
            temp_dir.mkdir(parents=True, exist_ok=True)
            self._local_cache_dir = temp_dir
        return self._local_cache_dir

    def get_cached_videos(self, device_id: str, db_session=None) -> List[Video]:
        """获取设备上所有缓存的视频"""
        videos = []

        try:
            logger.info("正在扫描视频目录...")
            entries = self.adb_service.list_directory(device_id, self.cache_base_path)

            video_entries = []
            for entry in entries:
                name = entry.get('name', '')
                if name in ['.', '..'] or not name or not name.isdigit():
                    continue

                video_dir = f"{self.cache_base_path}/{name}"

                try:
                    result = self.adb_service._run_command(
                        ["shell", f"ls {video_dir} | grep '^c_'"],
                        device_id,
                        timeout=5
                    )
                    c_dirs = [d.strip() for d in result.stdout.strip().split('\n') if d.strip()]
                    if c_dirs:
                        video_entries.append((name, video_dir, c_dirs))
                except:
                    continue

            if not video_entries:
                logger.info("未发现缓存视频")
                return []

            logger.info(f"发现 {len(video_entries)} 个视频目录")

            db_cached_videos = {}
            if db_session:
                from ..models.database import VideoModel
                db_videos = VideoModel.get_by_device(db_session, device_id)
                for db_video in db_videos:
                    db_cached_videos[db_video.video_id] = db_video

            for video_id, video_dir, episode_dirs in video_entries:
                try:
                    if video_id in db_cached_videos:
                        db_video = db_cached_videos[video_id]
                        
                        cache_video_path = db_video.cache_video_path
                        cache_audio_path = db_video.cache_audio_path
                        
                        if not cache_video_path and episode_dirs:
                            first_episode_dir = f"{video_dir}/{episode_dirs[0]}"
                            quality_dirs = self._find_quality_dirs(device_id, first_episode_dir)
                            if quality_dirs:
                                quality_dir = f"{first_episode_dir}/{quality_dirs[0]}"
                                cache_video_path = f"{quality_dir}/video.m4s"
                                cache_audio_path = f"{quality_dir}/audio.m4s"
                            else:
                                cache_video_path = f"{first_episode_dir}/video.m4s"
                                cache_audio_path = f"{first_episode_dir}/audio.m4s"
                        
                        video = Video(
                            video_id=video_id,
                            device_id=device_id,
                            bvid=db_video.bvid,
                            title=db_video.title,
                            owner_name=db_video.owner_name,
                            owner_id=db_video.owner_id,
                            cover_path=db_video.cover_path,
                            duration=db_video.duration,
                            file_size=db_video.file_size,
                            video_quality=db_video.video_quality,
                            video_quality_text=db_video.video_quality_text,
                            total_episodes=len(episode_dirs),
                            cache_path=video_dir,
                            cache_video_path=cache_video_path,
                            cache_audio_path=cache_audio_path,
                            download_status=db_video.download_status,
                            local_path=db_video.local_path,
                            all_local_paths=json.loads(db_video.all_local_paths) if db_video.all_local_paths else None
                        )
                        videos.append(video)
                    else:
                        video = self._parse_video_from_device(device_id, video_id, video_dir, episode_dirs)
                        if video:
                            videos.append(video)
                            if db_session:
                                from ..models.database import VideoModel
                                VideoModel.save_or_update(db_session, video)

                except Exception as e:
                    logger.debug(f"解析视频失败 {video_id}: {e}")
                    continue

            logger.info(f"成功解析 {len(videos)} 个视频")
            return videos

        except Exception as e:
            logger.error(f"获取缓存视频失败: {e}")
            return []

    def _parse_video_from_device(self, device_id: str, video_id: str,
                                  video_dir: str, episode_dirs: List[str]) -> Optional[Video]:
        """从设备解析视频信息"""
        try:
            video = Video(
                video_id=video_id,
                device_id=device_id,
                total_episodes=len(episode_dirs)
            )

            first_episode_dir = f"{video_dir}/{episode_dirs[0]}"
            entry_path = f"{first_episode_dir}/entry.json"

            entry_content = self.adb_service.read_remote_file(device_id, entry_path)
            if entry_content:
                try:
                    entry = json.loads(entry_content)
                    video.title = entry.get('title', f'视频_{video_id}')
                    video.bvid = entry.get('bvid', '') or entry.get('bv', '')
                    video.owner_id = str(entry.get('owner_id', ''))
                    video.owner_name = entry.get('owner_name', '未知UP主')

                    total_time_milli = entry.get('total_time_milli', 0)
                    video.duration = int(total_time_milli / 1000)

                    video.video_quality = entry.get('video_quality', 0)
                    quality_desc = entry.get('quality_pithy_description', '')
                    video.video_quality_text = quality_desc if quality_desc else self._get_quality_text(video.video_quality)

                    cover_url = entry.get('cover', '')
                    video.cover_path = cover_url if cover_url else None

                    video.file_size = entry.get('total_bytes', 0)
                except json.JSONDecodeError:
                    video.title = f'视频_{video_id}'
                    video.owner_name = '未知UP主'
            else:
                video.title = f'视频_{video_id}'
                video.owner_name = '未知UP主'

            video.cache_path = video_dir

            quality_dirs = self._find_quality_dirs(device_id, first_episode_dir)
            if quality_dirs:
                quality_dir = f"{first_episode_dir}/{quality_dirs[0]}"
                video.cache_video_path = f"{quality_dir}/video.m4s"
                video.cache_audio_path = f"{quality_dir}/audio.m4s"
            else:
                video.cache_video_path = f"{first_episode_dir}/video.m4s"
                video.cache_audio_path = f"{first_episode_dir}/audio.m4s"

            return video

        except Exception as e:
            logger.error(f"解析视频信息失败: {e}")
            return None

    def _find_quality_dirs(self, device_id: str, episode_dir: str) -> List[str]:
        """查找清晰度子目录"""
        quality_dirs = []
        try:
            entries = self.adb_service.list_directory(device_id, episode_dir)
            for entry in entries:
                name = entry.get('name', '')
                if name.isdigit():
                    quality_dirs.append(name)
            quality_dirs.sort(key=lambda x: int(x), reverse=True)
        except Exception as e:
            logger.debug(f"查找清晰度目录失败: {e}")
        return quality_dirs

    def _get_quality_text(self, quality_code: int) -> str:
        """根据清晰度代码获取描述文本"""
        quality_map = {
            16: "360P",
            32: "480P",
            64: "720P",
            80: "1080P",
            112: "1080P+",
            116: "1080P60",
            120: "4K",
            125: "HDR",
            126: "杜比视界",
            127: "8K"
        }
        return quality_map.get(quality_code, f"未知({quality_code})")
