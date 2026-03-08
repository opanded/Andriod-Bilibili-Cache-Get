"""文件传输与处理模块"""
import os
import json
import shutil
import threading
import uuid
import logging
from typing import List, Dict, Optional, Callable
from pathlib import Path
from datetime import datetime

from ..interfaces import (
    IDownloadService, IEventPublisher, DownloadStatus,
    DownloadRequest, DownloadTaskInfo, DownloadError, ErrorCategory
)
from ..models.video import Video
from ..models.database import Database, DownloadTaskModel, DownloadHistoryModel
from ..services.adb_service import ADBService
from ..services.video_merger import VideoMerger
from ..utils.file_utils import sanitize_filename, get_unique_filename
from ..config import Config
from .device_manager import DeviceManager

logger = logging.getLogger(__name__)


class FileTransfer(IDownloadService):
    """文件传输与处理核心类 - 实现 IDownloadService 接口"""

    def __init__(self, config, device_manager: DeviceManager,
                 adb_service: ADBService, event_publisher: IEventPublisher, db: Database,
                 notification_service=None):
        self.config = config
        self.device_manager = device_manager
        self.adb_service = adb_service
        self.event_publisher = event_publisher
        self.db = db
        self.notification_service = notification_service

        self.video_merger = VideoMerger(str(Config.get_ffmpeg_path()))

        self._download_queue: List[dict] = []
        self._active_tasks: Dict[str, dict] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

        self._progress_callbacks: Dict[str, Callable] = {}

        self._cleanup_temp_files()

        self._processor_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._processor_thread.start()

    def _cleanup_temp_files(self):
        """清理临时文件"""
        temp_dir = self.config.TEMP_DIR
        if temp_dir.exists():
            for item in temp_dir.iterdir():
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {item}, {e}")
            logger.info("临时文件清理完成")

    def handle_device_disconnected(self, device_id: str):
        """处理设备断开事件"""
        with self._lock:
            for task_id, task in list(self._active_tasks.items()):
                if task['request'].device_id == device_id:
                    task['status'] = DownloadStatus.FAILED.value
                    task['error_message'] = "设备已断开连接"
                    task['error_category'] = ErrorCategory.USER_ACTION.value
                    self.event_publisher.publish('download.error', {
                        'task_id': task_id,
                        'video_id': task['request'].video_id,
                        'video_title': task['request'].video_title,
                        'error': "设备已断开连接",
                        'error_category': ErrorCategory.USER_ACTION.value
                    })
                    del self._active_tasks[task_id]
                    logger.info(f"设备 {device_id} 断开，任务 {task_id} 已标记为失败")

    def submit_download(self, request: DownloadRequest) -> str:
        """提交下载请求"""
        task_id = str(uuid.uuid4())

        task = {
            'task_id': task_id,
            'request': request,
            'status': DownloadStatus.QUEUED.value,
            'progress': 0.0,
            'temp_dir': None,
            'local_path': None,
            'error_message': None,
            'error_category': None,
            'retry_count': 0,
            'created_at': datetime.now()
        }

        with self._lock:
            self._download_queue.append(task)

        try:
            with self.db.session() as session:
                task_model = DownloadTaskModel(
                    task_id=task_id,
                    video_id=request.video_id,
                    device_id=request.device_id,
                    video_title=request.video_title,
                    status=DownloadStatus.QUEUED.value,
                    progress=0.0,
                    created_at=datetime.now()
                )
                session.add(task_model)
        except Exception as e:
            logger.warning(f"保存任务到数据库失败: {e}")

        logger.info(f"添加下载任务: {task_id}, 视频: {request.video_title}")
        self.event_publisher.publish('download.queued', {
            'task_id': task_id,
            'video_id': request.video_id,
            'video_title': request.video_title
        })

        return task_id

    def submit_batch(self, requests: List[DownloadRequest]) -> List[str]:
        """批量提交下载请求"""
        task_ids = []
        for request in requests:
            task_id = self.submit_download(request)
            task_ids.append(task_id)
        return task_ids

    def pause_task(self, task_id: str) -> bool:
        """暂停指定任务"""
        with self._lock:
            for task in self._download_queue:
                if task['task_id'] == task_id:
                    task['status'] = DownloadStatus.PAUSED.value
                    self.event_publisher.publish('download.paused', {'task_id': task_id})
                    return True
        return False

    def resume_task(self, task_id: str) -> bool:
        """恢复指定任务"""
        with self._lock:
            for task in self._download_queue:
                if task['task_id'] == task_id and task['status'] == DownloadStatus.PAUSED.value:
                    task['status'] = DownloadStatus.QUEUED.value
                    self.event_publisher.publish('download.resumed', {'task_id': task_id})
                    return True
        return False

    def cancel_task(self, task_id: str) -> bool:
        """取消指定任务"""
        with self._lock:
            for i, task in enumerate(self._download_queue):
                if task['task_id'] == task_id:
                    task['status'] = DownloadStatus.CANCELLED.value
                    self._download_queue.pop(i)
                    self.event_publisher.publish('download.cancelled', {
                        'task_id': task_id,
                        'video_id': task['request'].video_id
                    })
                    return True

            if task_id in self._active_tasks:
                task = self._active_tasks[task_id]
                task['status'] = DownloadStatus.CANCELLED.value
                return True

        return False

    def cancel_batch(self, task_ids: List[str]) -> bool:
        """批量取消任务"""
        success = True
        for task_id in task_ids:
            if not self.cancel_task(task_id):
                success = False
        return success

    def get_task_info(self, task_id: str) -> Optional[DownloadTaskInfo]:
        """获取任务详细信息"""
        with self._lock:
            for task in self._download_queue:
                if task['task_id'] == task_id:
                    return DownloadTaskInfo(
                        task_id=task_id,
                        status=DownloadStatus(task['status']),
                        progress=task['progress'],
                        local_path=task.get('local_path'),
                        error_message=task.get('error_message'),
                        error_category=ErrorCategory(task['error_category']) if task.get('error_category') else None
                    )

            if task_id in self._active_tasks:
                task = self._active_tasks[task_id]
                return DownloadTaskInfo(
                    task_id=task_id,
                    status=DownloadStatus(task['status']),
                    progress=task['progress'],
                    local_path=task.get('local_path'),
                    error_message=task.get('error_message'),
                    error_category=ErrorCategory(task['error_category']) if task.get('error_category') else None
                )

        return None

    def get_queue_summary(self) -> Dict:
        """获取队列概览"""
        with self._lock:
            summary = {
                'pending': 0,
                'downloading': 0,
                'paused': 0,
                'completed': 0,
                'failed': 0,
                'cancelled': 0
            }

            for task in self._download_queue:
                status = task['status']
                if status in summary:
                    summary[status] += 1

            for task in self._active_tasks.values():
                status = task['status']
                if status in summary:
                    summary[status] += 1

            return summary

    def get_active_tasks(self) -> List[str]:
        """获取进行中的任务ID列表"""
        with self._lock:
            return list(self._active_tasks.keys())

    def get_failed_tasks(self) -> List[str]:
        """获取所有失败的任务ID列表"""
        failed = []
        with self._lock:
            for task in self._download_queue:
                if task['status'] == DownloadStatus.FAILED.value:
                    failed.append(task['task_id'])
            for task in self._active_tasks.values():
                if task['status'] == DownloadStatus.FAILED.value:
                    failed.append(task['task_id'])
        return failed

    def get_tasks_by_status(self, status: str) -> List[str]:
        """获取指定状态的所有任务ID"""
        tasks = []
        with self._lock:
            for task in self._download_queue:
                if task['status'] == status:
                    tasks.append(task['task_id'])
            for task in self._active_tasks.values():
                if task['status'] == status:
                    tasks.append(task['task_id'])
        return tasks

    def restore_tasks(self) -> None:
        """从数据库恢复未完成的任务"""
        try:
            with self.db.session() as session:
                pending_tasks = DownloadTaskModel.get_pending_tasks(session)
                
                for task_model in pending_tasks:
                    if task_model.status == DownloadStatus.DOWNLOADING.value:
                        task_model.status = DownloadStatus.FAILED.value
                        task_model.error_message = "程序异常关闭，请重新下载"
                        logger.warning(f"任务 {task_model.task_id} 状态为下载中，已重置为失败: {task_model.video_title}")
                        continue
                    
                    if task_model.status in [DownloadStatus.QUEUED.value, 'pending']:
                        task = {
                            'task_id': task_model.task_id,
                            'request': None,
                            'status': DownloadStatus.QUEUED.value,
                            'progress': task_model.progress or 0.0,
                            'temp_dir': None,
                            'local_path': task_model.local_path,
                            'error_message': task_model.error_message,
                            'error_category': task_model.error_category,
                            'retry_count': task_model.retry_count or 0,
                            'created_at': task_model.created_at,
                            'restored': True,
                            'video_id': task_model.video_id,
                            'device_id': task_model.device_id,
                            'video_title': task_model.video_title
                        }
                        with self._lock:
                            self._download_queue.append(task)
                        logger.info(f"恢复任务: {task_model.task_id}, 视频: {task_model.video_title}")
                
                session.commit()
                logger.info(f"已恢复 {len([t for t in pending_tasks if t.status == DownloadStatus.QUEUED.value])} 个未完成任务")
        except Exception as e:
            logger.error(f"恢复任务失败: {e}")

    def _update_task_in_db(self, task_id: str, updates: dict) -> None:
        """更新数据库中的任务记录"""
        try:
            with self.db.session() as session:
                task_model = DownloadTaskModel.get_by_task_id(session, task_id)
                if task_model:
                    for key, value in updates.items():
                        if key == 'all_local_paths' and isinstance(value, list):
                            value = json.dumps(value)
                        if hasattr(task_model, key):
                            setattr(task_model, key, value)
        except Exception as e:
            logger.warning(f"更新任务数据库记录失败: {task_id}, {e}")

    def _record_download_history(self, task: dict, status: str, error_message: str = None) -> None:
        """记录下载历史"""
        try:
            request = task.get('request')
            if not request:
                return
            
            with self.db.session() as session:
                history = DownloadHistoryModel(
                    video_id=request.video_id,
                    video_title=request.video_title,
                    device_id=request.device_id,
                    local_path=task.get('local_path'),
                    all_local_paths=json.dumps(task.get('all_local_paths')) if task.get('all_local_paths') else None,
                    file_size=task.get('file_size', 0),
                    duration=task.get('duration', 0),
                    status=status,
                    error_message=error_message,
                    started_at=task.get('started_at'),
                    completed_at=task.get('completed_at')
                )
                session.add(history)
                logger.info(f"已记录下载历史: {request.video_title}, 状态: {status}")
        except Exception as e:
            logger.warning(f"记录下载历史失败: {e}")

    def _process_queue(self):
        """处理下载队列"""
        logger.info("下载队列处理线程已启动")
        while not self._stop_event.is_set():
            tasks_to_start = []

            with self._lock:
                active_count = len(self._active_tasks)
                max_concurrent = getattr(self.config, 'MAX_CONCURRENT_DOWNLOADS', 3)
                available_slots = max(0, max_concurrent - active_count)

                for _ in range(available_slots):
                    for i, t in enumerate(self._download_queue):
                        if t['status'] == DownloadStatus.QUEUED.value:
                            task = self._download_queue.pop(i)
                            tasks_to_start.append(task)
                            self._active_tasks[task['task_id']] = task
                            break
                    else:
                        break

            for task in tasks_to_start:
                try:
                    threading.Thread(target=self._execute_task_wrapper, args=(task,), daemon=True).start()
                except Exception as e:
                    logger.error(f"任务启动异常: {task['task_id']}, 错误: {e}")
                    task['status'] = DownloadStatus.FAILED.value
                    task['error_message'] = str(e)
                    self.event_publisher.publish('download.error', {
                        'task_id': task['task_id'],
                        'video_id': task['request'].video_id,
                        'video_title': task['request'].video_title,
                        'error': str(e)
                    })
                    with self._lock:
                        if task['task_id'] in self._active_tasks:
                            del self._active_tasks[task['task_id']]

            self._stop_event.wait(0.5)

        logger.info("下载队列处理线程已停止")

    def _execute_task_wrapper(self, task: dict):
        """执行下载任务的包装器"""
        try:
            self._execute_task(task)
        except Exception as e:
            logger.error(f"任务执行异常: {task['task_id']}, 错误: {e}")
            task['status'] = DownloadStatus.FAILED.value
            task['error_message'] = str(e)
            
            request = task.get('request')
            video_id = request.video_id if request else task.get('video_id')
            video_title = request.video_title if request else task.get('video_title')
            
            self.event_publisher.publish('download.error', {
                'task_id': task['task_id'],
                'video_id': video_id,
                'video_title': video_title,
                'error': str(e)
            })
        finally:
            with self._lock:
                if task['task_id'] in self._active_tasks:
                    del self._active_tasks[task['task_id']]

    def _execute_task(self, task: dict):
        """执行下载任务"""
        request = task.get('request')
        
        if request is None:
            logger.warning(f"任务 {task['task_id']} 缺少请求信息，跳过执行")
            task['status'] = DownloadStatus.FAILED.value
            task['error_message'] = "任务信息不完整，请重新添加下载"
            return
        
        task['status'] = DownloadStatus.DOWNLOADING.value
        task['started_at'] = datetime.now()

        self._update_task_in_db(task['task_id'], {
            'status': DownloadStatus.DOWNLOADING.value,
            'started_at': task['started_at']
        })

        logger.info(f"开始执行任务: {task['task_id']}, 视频: {request.video_title}")
        self.event_publisher.publish('download.started', {
            'task_id': task['task_id'],
            'video_id': request.video_id,
            'video_title': request.video_title
        })

        try:
            if not self.device_manager.verify_connection(request.device_id):
                raise DownloadError.retryable("设备连接已断开")

            is_sufficient, free_gb, message = self.config.check_disk_space()
            if not is_sufficient:
                raise DownloadError.user_action(message)

            episode_paths = self._get_all_episode_paths(request.device_id, request)

            if not episode_paths:
                raise DownloadError.fatal("未找到视频文件")

            logger.info(f"发现 {len(episode_paths)} 个分P视频")

            downloaded_files = []
            total_episodes = len(episode_paths)

            for idx, (video_path, audio_path, episode_num) in enumerate(episode_paths, 1):
                temp_dir = self.config.TEMP_DIR / task['task_id'] / f"ep_{episode_num}"
                temp_dir.mkdir(parents=True, exist_ok=True)

                progress_start = (idx - 1) / total_episodes * 80
                progress_end = idx / total_episodes * 80

                video_local_path = temp_dir / "video.m4s"
                if not self._download_file(
                    request.device_id,
                    video_path,
                    str(video_local_path),
                    lambda p, ps=progress_start, pe=progress_end: self._update_progress(task, ps + (pe - ps) * p * 0.5)
                ):
                    raise DownloadError.retryable(f"第{episode_num}P视频文件下载失败")

                audio_local_path = None
                if audio_path:
                    audio_local_path = temp_dir / "audio.m4s"
                    if not self._download_file(
                        request.device_id,
                        audio_path,
                        str(audio_local_path),
                        lambda p, ps=progress_start, pe=progress_end: self._update_progress(task, ps + (pe - ps) * (0.5 + p * 0.5))
                    ):
                        raise DownloadError.retryable(f"第{episode_num}P音频文件下载失败")

                if total_episodes == 1:
                    output_filename = self._generate_output_filename(request)
                else:
                    output_filename = self._generate_output_filename(request, episode_num)

                output_path = Path(request.local_dir) / output_filename
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path = get_unique_filename(output_path.parent, output_path.name)

                if not self.video_merger.merge(
                    str(video_local_path),
                    str(audio_local_path) if audio_local_path else None,
                    str(output_path)
                ):
                    raise DownloadError.fatal(f"第{episode_num}P音视频合并失败")

                downloaded_files.append(str(output_path))
                logger.info(f"第{episode_num}P下载完成: {output_path}")

            task['status'] = DownloadStatus.COMPLETED.value
            task['local_path'] = downloaded_files[0] if downloaded_files else None
            task['completed_at'] = datetime.now()
            task['progress'] = 100.0

            total_size = 0
            for f in downloaded_files:
                try:
                    total_size += os.path.getsize(f)
                except:
                    pass

            duration_seconds = 0
            if task.get('started_at') and task.get('completed_at'):
                duration_seconds = int((task['completed_at'] - task['started_at']).total_seconds())

            self._update_task_in_db(task['task_id'], {
                'status': DownloadStatus.COMPLETED.value,
                'progress': 100.0,
                'local_path': task['local_path'],
                'all_local_paths': downloaded_files,
                'file_size': total_size,
                'duration': duration_seconds,
                'completed_at': task['completed_at']
            })

            task['file_size'] = total_size
            task['duration'] = duration_seconds
            task['all_local_paths'] = downloaded_files
            self._record_download_history(task, 'completed')

            logger.info(f"任务完成: {task['task_id']}, 共下载 {len(downloaded_files)} 个文件")
            self.event_publisher.publish('download.completed', {
                'task_id': task['task_id'],
                'video_id': request.video_id,
                'video_title': request.video_title,
                'local_path': task['local_path'],
                'all_files': downloaded_files
            })

            if self.notification_service:
                self.notification_service.notify_download_completed(
                    request.video_title,
                    task['local_path']
                )

            self._cleanup_task_temp(task)

        except DownloadError as e:
            logger.error(f"任务执行失败: {task['task_id']}, {e.message}")
            task['status'] = DownloadStatus.FAILED.value
            task['error_message'] = e.message
            task['error_category'] = e.category.value
            task['completed_at'] = datetime.now()

            self._update_task_in_db(task['task_id'], {
                'status': DownloadStatus.FAILED.value,
                'error_message': e.message,
                'error_category': e.category.value,
                'completed_at': task['completed_at']
            })

            self._record_download_history(task, 'failed', e.message)

            self.event_publisher.publish('download.error', {
                'task_id': task['task_id'],
                'video_id': request.video_id,
                'video_title': request.video_title,
                'error': e.message,
                'error_category': e.category.value
            })

            if e.category == ErrorCategory.RETRYABLE and task['retry_count'] < self.config.MAX_RETRY_COUNT:
                task['retry_count'] += 1
                logger.info(f"任务重试: {task['task_id']}, 第{task['retry_count']}次")
                task['status'] = DownloadStatus.QUEUED.value
                self._update_task_in_db(task['task_id'], {
                    'status': DownloadStatus.QUEUED.value,
                    'retry_count': task['retry_count']
                })
                with self._lock:
                    self._download_queue.insert(0, task)
                    del self._active_tasks[task['task_id']]
                return

        except Exception as e:
            logger.error(f"任务执行异常: {task['task_id']}, {e}")
            task['status'] = DownloadStatus.FAILED.value
            task['error_message'] = str(e)
            task['completed_at'] = datetime.now()

            self._update_task_in_db(task['task_id'], {
                'status': DownloadStatus.FAILED.value,
                'error_message': str(e),
                'completed_at': task['completed_at']
            })

            self._record_download_history(task, 'failed', str(e))

            self.event_publisher.publish('download.error', {
                'task_id': task['task_id'],
                'video_id': request.video_id,
                'video_title': request.video_title,
                'error': str(e)
            })

        finally:
            with self._lock:
                if task['task_id'] in self._active_tasks:
                    del self._active_tasks[task['task_id']]

    def _get_all_episode_paths(self, device_id: str, request: DownloadRequest) -> list:
        """获取所有分P的视频和音频路径"""
        paths = []

        if not request.cache_video_path:
            logger.error(f"视频缓存路径为空: video_id={request.video_id}")
            return paths

        try:
            video_dir = request.cache_video_path.rsplit('/', 3)[0]
            
            entries = self.adb_service.list_directory(device_id, video_dir)
            
            c_dirs = []
            for entry in entries:
                name = entry.get('name', '')
                if name.startswith('c_'):
                    c_dirs.append(name)
            
            c_dirs.sort()

            if not c_dirs:
                if self.adb_service.file_exists(device_id, request.cache_video_path):
                    paths.append((request.cache_video_path, request.cache_audio_path, 1))
                return paths

            for idx, c_dir in enumerate(c_dirs, 1):
                episode_dir = f"{video_dir}/{c_dir}"

                quality_dirs = self._find_quality_dirs(device_id, episode_dir)

                if quality_dirs:
                    quality_dir = f"{episode_dir}/{quality_dirs[0]}"
                    video_path = f"{quality_dir}/video.m4s"
                    audio_path = f"{quality_dir}/audio.m4s"
                else:
                    video_path = f"{episode_dir}/video.m4s"
                    audio_path = f"{episode_dir}/audio.m4s"

                if self.adb_service.file_exists(device_id, video_path):
                    audio_exists = self.adb_service.file_exists(device_id, audio_path)
                    paths.append((video_path, audio_path if audio_exists else None, idx))

        except Exception as e:
            logger.error(f"获取分P路径失败: {e}")
            if request.cache_video_path and self.adb_service.file_exists(device_id, request.cache_video_path):
                paths.append((request.cache_video_path, request.cache_audio_path, 1))

        return paths

    def _find_quality_dirs(self, device_id: str, episode_dir: str) -> list:
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

    def _download_file(self, device_id: str, remote_path: str, local_path: str,
                       progress_callback: Optional[Callable[[float], None]]) -> bool:
        """下载单个文件"""
        logger.info(f"开始下载文件: {remote_path} -> {local_path}")
        try:
            result = self.adb_service.pull_file(
                device_id,
                remote_path,
                local_path,
                progress_callback=progress_callback
            )

            if result and progress_callback:
                progress_callback(100.0)

            return result
        except Exception as e:
            logger.error(f"下载文件失败: {remote_path}, 错误: {e}")
            return False

    def _update_progress(self, task: dict, progress: float):
        """更新任务进度"""
        task['progress'] = min(100.0, max(0.0, progress))

        self.event_publisher.publish('download.progress', {
            'task_id': task['task_id'],
            'video_id': task['request'].video_id,
            'progress': task['progress']
        })

    def _generate_output_filename(self, request: DownloadRequest, episode_num: int = None) -> str:
        """生成输出文件名"""
        safe_title = sanitize_filename(request.video_title or "unnamed", self.config.MAX_FILENAME_LENGTH)

        if episode_num:
            safe_title = f"{safe_title}_P{episode_num}"

        if request.video_id:
            filename = f"{safe_title}_{request.video_id}.mp4"
        else:
            filename = f"{safe_title}.mp4"

        return filename

    def _cleanup_task_temp(self, task: dict):
        """清理任务临时文件"""
        temp_dir = self.config.TEMP_DIR / task['task_id']
        if temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
                logger.debug(f"清理临时目录: {temp_dir}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")

    def stop(self):
        """停止文件传输服务"""
        self._stop_event.set()
        self._processor_thread.join(timeout=5)

    def stop_fast(self):
        """快速停止文件传输服务"""
        logger.info("正在快速停止文件传输服务...")
        self._stop_event.set()
        self._processor_thread.join(timeout=1)
        logger.info("文件传输服务已停止")
