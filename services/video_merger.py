"""视频合并服务模块"""
import subprocess
import sys
import logging
from pathlib import Path
from typing import Optional, Callable

from ..interfaces.services import IVideoMerger

logger = logging.getLogger(__name__)


class VideoMerger(IVideoMerger):
    """视频合并服务"""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path
        self._available = self._check_ffmpeg_available()

    def _check_ffmpeg_available(self) -> bool:
        try:
            creationflags = 0
            if sys.platform == 'win32':
                creationflags = subprocess.CREATE_NO_WINDOW

            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                timeout=10,
                encoding='utf-8',
                errors='replace',
                creationflags=creationflags
            )
            if result.returncode == 0:
                logger.info("FFmpeg可用")
                return True
        except Exception as e:
            logger.warning(f"FFmpeg不可用: {e}")
        return False

    def is_available(self) -> bool:
        return self._available

    def merge(self, video_path: str, audio_path: Optional[str],
              output_path: str, progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """合并视频和音频

        Args:
            video_path: 视频文件路径
            audio_path: 音频文件路径（可选）
            output_path: 输出文件路径
            progress_callback: 进度回调函数

        Returns:
            是否成功
        """
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            if not Path(video_path).exists():
                logger.error(f"视频文件不存在: {video_path}")
                return False

            if audio_path and not Path(audio_path).exists():
                logger.warning(f"音频文件不存在: {audio_path}，将只复制视频")
                audio_path = None

            cmd = [self.ffmpeg_path, "-y"]

            if audio_path:
                cmd.extend(["-i", video_path, "-i", audio_path])
                cmd.extend(["-c:v", "copy", "-c:a", "copy"])
            else:
                cmd.extend(["-i", video_path, "-c", "copy"])

            cmd.append(output_path)

            logger.info(f"执行合并命令: {' '.join(cmd)}")

            creationflags = 0
            if sys.platform == 'win32':
                creationflags = subprocess.CREATE_NO_WINDOW

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=300,
                encoding='utf-8',
                errors='replace',
                creationflags=creationflags
            )

            if result.returncode != 0:
                logger.error(f"合并失败: {result.stderr}")
                return False

            if not Path(output_path).exists():
                logger.error(f"合并后文件不存在: {output_path}")
                return False

            if progress_callback:
                progress_callback(100.0)

            logger.info(f"合并成功: {output_path}")
            return True

        except subprocess.TimeoutExpired:
            logger.error("合并超时")
            return False
        except Exception as e:
            logger.error(f"合并失败: {e}")
            return False
