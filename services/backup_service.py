"""数据备份服务模块"""
import os
import json
import shutil
import zipfile
import logging
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)


class BackupService:
    """数据备份服务类"""
    
    BACKUP_VERSION = "1.0"
    BACKUP_MANIFEST_FILE = "manifest.json"
    
    def __init__(self, db, settings_service):
        self.db = db
        self.settings_service = settings_service
    
    def export_data(self, export_path: str, include_downloads: bool = False,
                    progress_callback=None) -> Tuple[bool, str]:
        """导出数据库和设置到指定目录
        
        Args:
            export_path: 导出文件路径（.zip）
            include_downloads: 是否包含已下载的视频文件
            progress_callback: 进度回调函数 (current, total, message)
        
        Returns:
            (success, message)
        """
        try:
            export_path = Path(export_path)
            if not export_path.suffix == '.zip':
                export_path = export_path.with_suffix('.zip')
            
            temp_dir = Path(tempfile.mkdtemp(prefix="bili_backup_"))
            
            try:
                if progress_callback:
                    progress_callback(0, 100, "准备导出...")
                
                db_path = Path(self.db.db_path)
                if not db_path.exists():
                    return False, "数据库文件不存在"
                
                backup_db_path = temp_dir / "bili_cache.db"
                shutil.copy2(db_path, backup_db_path)
                logger.info(f"已复制数据库: {db_path} -> {backup_db_path}")
                
                if progress_callback:
                    progress_callback(20, 100, "导出设置...")
                
                settings_data = self.settings_service.settings.to_dict()
                settings_path = temp_dir / "user_settings.json"
                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(settings_data, f, indent=2, ensure_ascii=False)
                logger.info(f"已导出设置: {settings_path}")
                
                if progress_callback:
                    progress_callback(40, 100, "创建备份清单...")
                
                manifest = {
                    "version": self.BACKUP_VERSION,
                    "created_at": datetime.now().isoformat(),
                    "app_version": "0.2-GLM5",
                    "includes_downloads": include_downloads,
                    "files": ["bili_cache.db", "user_settings.json"]
                }
                
                if include_downloads:
                    download_dir_str = self.settings_service.settings.download_dir
                    if download_dir_str:
                        download_dir = Path(download_dir_str)
                    else:
                        from src.config import Config
                        download_dir = Config.DOWNLOAD_DIR
                    
                    if download_dir.exists():
                        downloads_backup_dir = temp_dir / "downloads"
                        manifest["files"].append("downloads")
                        
                        if progress_callback:
                            progress_callback(50, 100, "计算下载文件...")
                        
                        total_size, file_count = self._calculate_dir_size(download_dir)
                        
                        if progress_callback:
                            progress_callback(55, 100, f"复制下载文件 ({file_count} 个文件)...")
                        
                        self._copy_dir_with_progress(
                            download_dir, downloads_backup_dir,
                            progress_callback, 55, 40
                        )
                
                manifest_path = temp_dir / self.BACKUP_MANIFEST_FILE
                with open(manifest_path, 'w', encoding='utf-8') as f:
                    json.dump(manifest, f, indent=2, ensure_ascii=False)
                
                if progress_callback:
                    progress_callback(95, 100, "压缩备份文件...")
                
                with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in temp_dir.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(temp_dir)
                            zipf.write(file_path, arcname)
                
                if progress_callback:
                    progress_callback(100, 100, "导出完成")
                
                backup_size = export_path.stat().st_size / (1024 * 1024)
                logger.info(f"备份已创建: {export_path} ({backup_size:.2f} MB)")
                
                return True, f"备份成功！\n文件大小: {backup_size:.2f} MB"
                
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            return False, f"导出失败: {str(e)}"
    
    def import_data(self, import_path: str, restore_settings: bool = True,
                    restore_database: bool = True, progress_callback=None) -> Tuple[bool, str]:
        """从ZIP文件导入数据
        
        Args:
            import_path: 导入文件路径（.zip）
            restore_settings: 是否恢复设置
            restore_database: 是否恢复数据库
            progress_callback: 进度回调函数 (current, total, message)
        
        Returns:
            (success, message)
        """
        try:
            import_path = Path(import_path)
            if not import_path.exists():
                return False, "备份文件不存在"
            
            if not import_path.suffix == '.zip':
                return False, "无效的备份文件格式，需要 .zip 文件"
            
            temp_dir = Path(tempfile.mkdtemp(prefix="bili_restore_"))
            
            try:
                if progress_callback:
                    progress_callback(0, 100, "解压备份文件...")
                
                with zipfile.ZipFile(import_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                if progress_callback:
                    progress_callback(20, 100, "验证备份文件...")
                
                manifest_path = temp_dir / self.BACKUP_MANIFEST_FILE
                if not manifest_path.exists():
                    return False, "无效的备份文件：缺少清单文件"
                
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                
                validation_result = self._validate_backup(manifest, temp_dir)
                if not validation_result[0]:
                    return False, validation_result[1]
                
                if progress_callback:
                    progress_callback(30, 100, "验证通过，准备恢复...")
                
                if restore_database:
                    if progress_callback:
                        progress_callback(40, 100, "备份当前数据库...")
                    
                    current_db_path = Path(self.db.db_path)
                    if current_db_path.exists():
                        backup_db_path = current_db_path.with_suffix('.db.bak')
                        shutil.copy2(current_db_path, backup_db_path)
                        logger.info(f"已备份当前数据库: {backup_db_path}")
                    
                    if progress_callback:
                        progress_callback(50, 100, "恢复数据库...")
                    
                    self.db.close()
                    
                    source_db = temp_dir / "bili_cache.db"
                    if source_db.exists():
                        shutil.copy2(source_db, current_db_path)
                        logger.info(f"已恢复数据库: {source_db} -> {current_db_path}")
                    else:
                        return False, "备份文件中缺少数据库"
                
                if restore_settings:
                    if progress_callback:
                        progress_callback(70, 100, "恢复设置...")
                    
                    source_settings = temp_dir / "user_settings.json"
                    if source_settings.exists():
                        with open(source_settings, 'r', encoding='utf-8') as f:
                            settings_data = json.load(f)
                        
                        from src.models.settings import UserSettings
                        new_settings = UserSettings.from_dict(settings_data)
                        new_settings.validate()
                        
                        self.settings_service.settings = new_settings
                        self.settings_service.save()
                        logger.info("已恢复用户设置")
                
                if progress_callback:
                    progress_callback(100, 100, "导入完成")
                
                return True, "数据恢复成功！\n请重启应用程序以使更改生效。"
                
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            logger.error(f"导入数据失败: {e}")
            return False, f"导入失败: {str(e)}"
    
    def _validate_backup(self, manifest: dict, temp_dir: Path) -> Tuple[bool, str]:
        """验证备份文件完整性
        
        Args:
            manifest: 备份清单
            temp_dir: 临时解压目录
        
        Returns:
            (is_valid, error_message)
        """
        if "version" not in manifest:
            return False, "备份文件缺少版本信息"
        
        if manifest["version"] != self.BACKUP_VERSION:
            return False, f"不支持的备份版本: {manifest['version']}"
        
        if "files" not in manifest:
            return False, "备份清单缺少文件列表"
        
        for file_name in manifest["files"]:
            file_path = temp_dir / file_name
            if file_name == "downloads":
                continue
            
            if not file_path.exists():
                return False, f"备份文件缺少: {file_name}"
        
        return True, ""
    
    def _calculate_dir_size(self, directory: Path) -> Tuple[int, int]:
        """计算目录大小和文件数量
        
        Args:
            directory: 目录路径
        
        Returns:
            (total_size, file_count)
        """
        total_size = 0
        file_count = 0
        
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                    file_count += 1
                except Exception:
                    pass
        
        return total_size, file_count
    
    def _copy_dir_with_progress(self, src: Path, dst: Path,
                                 progress_callback, start_progress: int,
                                 progress_range: int):
        """带进度复制的目录复制
        
        Args:
            src: 源目录
            dst: 目标目录
            progress_callback: 进度回调
            start_progress: 起始进度
            progress_range: 进度范围
        """
        files = list(src.rglob('*'))
        total_files = len([f for f in files if f.is_file()])
        
        if total_files == 0:
            return
        
        dst.mkdir(parents=True, exist_ok=True)
        
        copied = 0
        for file_path in files:
            if file_path.is_file():
                rel_path = file_path.relative_to(src)
                dst_path = dst / rel_path
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dst_path)
                
                copied += 1
                if progress_callback and copied % 10 == 0:
                    progress = start_progress + int((copied / total_files) * progress_range)
                    progress_callback(progress, 100, f"复制文件 {copied}/{total_files}...")
    
    def get_backup_info(self, backup_path: str) -> Optional[dict]:
        """获取备份文件信息
        
        Args:
            backup_path: 备份文件路径
        
        Returns:
            备份信息字典，失败返回None
        """
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists() or not backup_path.suffix == '.zip':
                return None
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                if self.BACKUP_MANIFEST_FILE not in zipf.namelist():
                    return None
                
                with zipf.open(self.BACKUP_MANIFEST_FILE) as f:
                    manifest = json.load(f)
            
            file_size = backup_path.stat().st_size
            
            return {
                "version": manifest.get("version"),
                "created_at": manifest.get("created_at"),
                "app_version": manifest.get("app_version"),
                "includes_downloads": manifest.get("includes_downloads", False),
                "file_size": file_size,
                "file_size_mb": file_size / (1024 * 1024),
                "file_path": str(backup_path)
            }
            
        except Exception as e:
            logger.error(f"获取备份信息失败: {e}")
            return None
    
    def list_available_backups(self, directory: str) -> List[dict]:
        """列出目录中的可用备份文件
        
        Args:
            directory: 目录路径
        
        Returns:
            备份信息列表
        """
        backups = []
        directory = Path(directory)
        
        if not directory.exists():
            return backups
        
        for backup_file in directory.glob("*.zip"):
            info = self.get_backup_info(str(backup_file))
            if info:
                backups.append(info)
        
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return backups
