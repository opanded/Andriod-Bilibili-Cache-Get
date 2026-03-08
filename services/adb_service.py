"""ADB服务封装模块"""
import subprocess
import re
import logging
import sys
from typing import List, Dict, Optional
from pathlib import Path

from ..interfaces.services import IADBService

logger = logging.getLogger(__name__)


def _detect_encoding():
    """检测系统默认编码"""
    if sys.platform == 'win32':
        try:
            import locale
            encoding = locale.getpreferredencoding(False)
            if encoding:
                return encoding
        except:
            pass
        return 'gbk'
    return 'utf-8'


DEFAULT_ENCODING = _detect_encoding()


class ADBService(IADBService):
    """ADB服务封装类"""

    def __init__(self, adb_path: str = "adb"):
        self.adb_path = adb_path
        self._check_adb_available()

    def _check_adb_available(self) -> bool:
        try:
            result = self._run_command(["version"])
            logger.info(f"ADB可用: {result.stdout.strip()}")
            return True
        except Exception as e:
            logger.error(f"ADB不可用: {e}")
            return False

    def _decode_output(self, data: bytes) -> str:
        """智能解码输出，尝试多种编码"""
        if not data:
            return ""

        encodings = ['utf-8', DEFAULT_ENCODING, 'gbk', 'gb2312', 'latin-1']
        
        for encoding in encodings:
            try:
                return data.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        
        return data.decode('utf-8', errors='ignore')

    def _run_command(self, args: List[str], device_id: Optional[str] = None,
                     timeout: int = 30) -> subprocess.CompletedProcess:
        cmd = [self.adb_path]
        if device_id:
            cmd.extend(["-s", device_id])
        cmd.extend(args)

        logger.debug(f"执行ADB命令: {' '.join(cmd)}")

        creationflags = 0
        if sys.platform == 'win32':
            creationflags = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace',
            creationflags=creationflags
        )

        stdout_text = result.stdout if result.stdout else ""
        stderr_text = result.stderr if result.stderr else ""

        if result.returncode != 0:
            error_msg = stderr_text.strip() if stderr_text else "未知错误"
            raise RuntimeError(f"ADB命令执行失败: {error_msg}")

        class Result:
            pass
        r = Result()
        r.stdout = stdout_text
        r.stderr = stderr_text
        r.returncode = result.returncode
        return r

    def get_devices(self) -> List[Dict[str, str]]:
        try:
            result = self._run_command(["devices", "-l"])
            devices = []

            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                if len(parts) >= 2:
                    device_id = parts[0]
                    status = parts[1]

                    device_info = {"device_id": device_id, "status": status}
                    for part in parts[2:]:
                        if ':' in part:
                            key, value = part.split(':', 1)
                            device_info[key] = value

                    devices.append(device_info)

            logger.info(f"发现 {len(devices)} 个设备")
            return devices
        except Exception as e:
            logger.error(f"获取设备列表失败: {e}")
            return []

    def get_device_info(self, device_id: str) -> Dict[str, str]:
        info = {}

        try:
            result = self._run_command(["shell", "getprop", "ro.product.marketname"], device_id)
            market_name = result.stdout.strip()
            info["market_name"] = market_name if market_name else "Unknown"
        except:
            info["market_name"] = "Unknown"

        try:
            result = self._run_command(["shell", "getprop", "ro.product.model"], device_id)
            info["model"] = result.stdout.strip()
        except:
            info["model"] = "Unknown"

        try:
            result = self._run_command(["shell", "getprop", "ro.product.manufacturer"], device_id)
            info["manufacturer"] = result.stdout.strip()
        except:
            info["manufacturer"] = "Unknown"

        try:
            result = self._run_command(["shell", "getprop", "ro.build.version.release"], device_id)
            info["android_version"] = result.stdout.strip()
        except:
            info["android_version"] = "Unknown"

        try:
            result = self._run_command(["shell", "getprop", "ro.serialno"], device_id)
            info["serial"] = result.stdout.strip()
        except:
            info["serial"] = device_id

        return info

    def get_device_serial(self, device_id: str) -> Optional[str]:
        try:
            result = self._run_command(["shell", "getprop", "ro.serialno"], device_id)
            serial = result.stdout.strip()
            if serial and serial != "unknown":
                return serial
        except Exception as e:
            logger.warning(f"获取设备序列号失败: {e}")
        return None

    def check_package_installed(self, device_id: str, package_name: str) -> bool:
        try:
            result = self._run_command(
                ["shell", "pm", "list", "packages", package_name],
                device_id
            )
            return package_name in result.stdout
        except Exception as e:
            logger.error(f"检查应用安装状态失败: {e}")
            return False

    def get_package_version(self, device_id: str, package_name: str) -> Optional[str]:
        try:
            result = self._run_command(
                ["shell", "dumpsys", "package", package_name, "|", "grep", "versionName"],
                device_id
            )
            match = re.search(r'versionName=([^\s]+)', result.stdout)
            if match:
                return match.group(1)
        except Exception as e:
            logger.error(f"获取应用版本失败: {e}")
        return None

    def keep_screen_on(self, device_id: str) -> bool:
        try:
            result = self._run_command(
                ["shell", "settings", "get", "system", "screen_off_timeout"],
                device_id
            )
            original_timeout = result.stdout.strip()

            self._run_command(
                ["shell", "settings", "put", "system", "screen_off_timeout", "2147483647"],
                device_id
            )

            self._run_command(["shell", "input", "keyevent", "224"], device_id)

            logger.info(f"设备 {device_id} 屏幕常亮已设置，原超时时间: {original_timeout}ms")
            return True
        except Exception as e:
            logger.error(f"设置屏幕常亮失败: {e}")
            return False

    def restore_screen_timeout(self, device_id: str, timeout: str = "30000") -> bool:
        try:
            self._run_command(
                ["shell", "settings", "put", "system", "screen_off_timeout", timeout],
                device_id
            )
            logger.info(f"设备 {device_id} 屏幕超时已恢复为 {timeout}ms")
            return True
        except Exception as e:
            logger.error(f"恢复屏幕超时失败: {e}")
            return False

    def list_directory(self, device_id: str, remote_path: str) -> List[Dict[str, str]]:
        try:
            result = self._run_command(
                ["shell", "ls", "-la", remote_path],
                device_id
            )

            items = []
            for line in result.stdout.strip().split('\n'):
                parts = line.split(None, 8)
                if len(parts) >= 8 and not line.startswith('total'):
                    items.append({
                        'permissions': parts[0],
                        'owner': parts[2],
                        'group': parts[3],
                        'size': parts[4],
                        'date': f"{parts[5]} {parts[6]}",
                        'name': parts[7] if len(parts) == 8 else parts[8]
                    })

            return items
        except Exception as e:
            logger.error(f"列出目录失败: {e}")
            return []

    def file_exists(self, device_id: str, remote_path: str) -> bool:
        try:
            result = self._run_command(
                ["shell", "test", "-e", remote_path, "&&", "echo", "exists"],
                device_id
            )
            return "exists" in result.stdout
        except:
            return False

    def get_file_size(self, device_id: str, remote_path: str) -> int:
        try:
            result = self._run_command(
                ["shell", "stat", "-c%s", remote_path],
                device_id
            )
            return int(result.stdout.strip())
        except:
            return -1

    def pull_file(self, device_id: str, remote_path: str, local_path: str,
                  progress_callback=None) -> bool:
        try:
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)

            result = self._run_command(
                ["pull", remote_path, local_path],
                device_id,
                timeout=300
            )

            if not Path(local_path).exists():
                logger.error(f"文件下载后不存在: {local_path}")
                return False

            downloaded_size = Path(local_path).stat().st_size

            if progress_callback:
                progress_callback(downloaded_size, downloaded_size)

            logger.info(f"文件下载成功: {remote_path} -> {local_path}")
            return True
        except Exception as e:
            logger.error(f"文件拉取失败: {e}")
            return False

    def read_remote_file(self, device_id: str, remote_path: str) -> str:
        try:
            result = self._run_command(
                ["shell", "cat", remote_path],
                device_id
            )
            return result.stdout
        except Exception as e:
            logger.error(f"读取远程文件失败: {e}")
            return ""

    def connect_wireless(self, ip: str, port: int) -> bool:
        try:
            result = self._run_command(
                ["connect", f"{ip}:{port}"],
                timeout=30
            )
            if "connected" in result.stdout.lower():
                logger.info(f"无线连接成功: {ip}:{port}")
                return True
            logger.warning(f"无线连接失败: {result.stdout.strip()}")
            return False
        except Exception as e:
            logger.error(f"无线连接失败: {e}")
            return False

    def disconnect_wireless(self, ip: str, port: int) -> bool:
        try:
            result = self._run_command(
                ["disconnect", f"{ip}:{port}"],
                timeout=30
            )
            logger.info(f"已断开无线连接: {ip}:{port}")
            return True
        except Exception as e:
            logger.error(f"断开无线连接失败: {e}")
            return False

    def pair_wireless(self, ip: str, port: int, code: str) -> bool:
        """使用配对码配对新设备"""
        try:
            result = self._run_command(
                ["pair", f"{ip}:{port}", code],
                timeout=30
            )
            output = result.stdout.lower()
            if "successfully paired" in output or "paired" in output:
                logger.info(f"配对成功: {ip}:{port}")
                return True
            logger.warning(f"配对失败: {result.stdout.strip()}")
            return False
        except Exception as e:
            logger.error(f"配对失败: {e}")
            return False

    def test_connection(self, device_id: str) -> bool:
        """测试设备连接"""
        try:
            result = self._run_command(["-s", device_id, "echo", "test"], device_id=None)
            logger.info(f"设备连接测试成功: {device_id}")
            return True
        except Exception as e:
            logger.error(f"设备连接测试失败: {e}")
            return False
