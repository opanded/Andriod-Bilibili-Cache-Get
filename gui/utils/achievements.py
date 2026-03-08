"""成就系统 - v2.1萌化版本"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field, asdict


@dataclass
class Achievement:
    """成就数据类"""
    id: str
    name: str
    description: str
    icon: str
    condition: str
    category: str = "general"
    hidden: bool = False
    unlocked: bool = False
    unlocked_at: Optional[str] = None


ACHIEVEMENTS_DATA: Dict[str, Achievement] = {
    "first_download": Achievement(
        id="first_download",
        name="初次下载",
        description="迈出收藏的第一步！",
        icon="�",
        condition="完成第一次下载",
        category="download"
    ),
    "download_10": Achievement(
        id="download_10",
        name="小试牛刀",
        description="开始积累你的收藏了！",
        icon="📚",
        condition="下载10个视频",
        category="download"
    ),
    "download_50": Achievement(
        id="download_50",
        name="收藏达人",
        description="兔蛙酱佩服你的收藏能力！",
        icon="📺",
        condition="下载50个视频",
        category="download"
    ),
    "download_100": Achievement(
        id="download_100",
        name="收藏家",
        description="你的收藏库越来越丰富了！",
        icon="🏆",
        condition="下载100个视频",
        category="download"
    ),
    "download_500": Achievement(
        id="download_500",
        name="视频库",
        description="你简直是个视频收藏大师！",
        icon="�",
        condition="下载500个视频",
        category="download"
    ),
    "batch_10": Achievement(
        id="batch_10",
        name="批量新手",
        description="开始尝试批量下载了！",
        icon="📦",
        condition="单次下载10个视频",
        category="download"
    ),
    "batch_50": Achievement(
        id="batch_50",
        name="批量达人",
        description="圈圈子都被你惊呆了！",
        icon="🎬",
        condition="单次下载50个视频",
        category="download"
    ),
    "batch_100": Achievement(
        id="batch_100",
        name="批量大师",
        description="批量下载的终极境界！",
        icon="🚀",
        condition="单次下载100个视频",
        category="download"
    ),
    "first_connect": Achievement(
        id="first_connect",
        name="初次连接",
        description="成功连接第一个设备！",
        icon="🔗",
        condition="连接第一个设备",
        category="connect"
    ),
    "connect_5": Achievement(
        id="connect_5",
        name="多设备用户",
        description="你开始管理多个设备了！",
        icon="📱",
        condition="连接5个不同设备",
        category="connect"
    ),
    "connect_10": Achievement(
        id="connect_10",
        name="连接大师",
        description="你已经是个连接专家了！",
        icon="🎯",
        condition="连接10个不同设备",
        category="connect"
    ),
    "wireless_connect": Achievement(
        id="wireless_connect",
        name="无线先锋",
        description="兔蛙酱觉得你很专业！",
        icon="📶",
        condition="使用无线ADB连接",
        category="connect"
    ),
    "night_owl": Achievement(
        id="night_owl",
        name="夜猫子",
        description="这么晚还在工作，辛苦了~",
        icon="🌙",
        condition="深夜(0-5点)使用",
        category="time"
    ),
    "early_bird": Achievement(
        id="early_bird",
        name="早起鸟",
        description="早起的鸟儿有虫吃！",
        icon="🐦",
        condition="早上(5-7点)使用",
        category="time"
    ),
    "weekend_warrior": Achievement(
        id="weekend_warrior",
        name="周末战士",
        description="周末也不休息，真勤奋！",
        icon="⚔️",
        condition="周末使用",
        category="time"
    ),
    "anniversary": Achievement(
        id="anniversary",
        name="周年纪念",
        description="感谢一年的陪伴！",
        icon="🎉",
        condition="使用满一年",
        category="time"
    ),
    "first_meet": Achievement(
        id="first_meet",
        name="初次见面",
        description="欢迎来到B站缓存下载工具！",
        icon="🐰🐸",
        condition="首次启动应用",
        category="interaction"
    ),
    "mascot_clicker": Achievement(
        id="mascot_clicker",
        name="吉祥物之友",
        description="和吉祥物互动真开心！",
        icon="🐰",
        condition="点击吉祥物10次",
        category="interaction"
    ),
    "mascot_lover": Achievement(
        id="mascot_lover",
        name="吉祥物狂热者",
        description="吉祥物超喜欢你的！",
        icon="🐸",
        condition="点击吉祥物50次",
        category="interaction"
    ),
    "theme_switcher": Achievement(
        id="theme_switcher",
        name="主题达人",
        description="换种心情，换种风格！",
        icon="🎨",
        condition="切换主题5次",
        category="interaction"
    ),
    "easter_egg": Achievement(
        id="easter_egg",
        name="彩蛋猎人",
        description="你发现了什么秘密？",
        icon="🥚",
        condition="???",
        category="hidden",
        hidden=True
    ),
    "secret_combo": Achievement(
        id="secret_combo",
        name="神秘组合",
        description="神秘的代码被你发现了！",
        icon="🔮",
        condition="???",
        category="hidden",
        hidden=True
    ),
    "expression_collector": Achievement(
        id="expression_collector",
        name="表情收藏家",
        description="你见过所有表情了！",
        icon="😊",
        condition="查看所有16种表情",
        category="interaction"
    ),
    "hidden_egg_finder": Achievement(
        id="hidden_egg_finder",
        name="隐藏彩蛋发现者",
        description="长按吉祥物发现了隐藏彩蛋！",
        icon="🥚",
        condition="长按吉祥物触发彩蛋",
        category="hidden",
        hidden=True
    ),
}


class AchievementManager:
    """成就管理器"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        self._data_dir = data_dir or Path.home() / ".bili_cache_get"
        self._data_file = self._data_dir / "achievements.json"
        self._achievements: Dict[str, Achievement] = {}
        self._stats: Dict[str, int] = {
            "devices_connected": 0,
            "videos_downloaded": 0,
            "max_batch_download": 0,
            "first_launch_date": None,
            "wireless_connections": 0,
            "mascot_clicks": 0,
            "theme_switches": 0,
        }
        self._connected_devices: Set[str] = set()
        self._new_unlocked: List[Achievement] = []
        
        self._load_data()
    
    def _load_data(self):
        """加载数据"""
        if self._data_file.exists():
            try:
                with open(self._data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    for ach_id, ach_data in data.get('achievements', {}).items():
                        if ach_id in ACHIEVEMENTS_DATA:
                            self._achievements[ach_id] = Achievement(
                                **{**asdict(ACHIEVEMENTS_DATA[ach_id]), **ach_data}
                            )
                    
                    self._stats = data.get('stats', self._stats)
                    self._connected_devices = set(data.get('connected_devices', []))
            except Exception:
                self._achievements = {k: Achievement(**asdict(v)) for k, v in ACHIEVEMENTS_DATA.items()}
        else:
            self._achievements = {k: Achievement(**asdict(v)) for k, v in ACHIEVEMENTS_DATA.items()}
    
    def _save_data(self):
        """保存数据"""
        self._data_dir.mkdir(parents=True, exist_ok=True)
        
        data = {
            'achievements': {k: asdict(v) for k, v in self._achievements.items()},
            'stats': self._stats,
            'connected_devices': list(self._connected_devices),
        }
        
        with open(self._data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def unlock(self, achievement_id: str) -> Optional[Achievement]:
        """解锁成就"""
        if achievement_id not in self._achievements:
            return None
        
        achievement = self._achievements[achievement_id]
        if achievement.unlocked:
            return None
        
        achievement.unlocked = True
        achievement.unlocked_at = datetime.now().isoformat()
        self._new_unlocked.append(achievement)
        self._save_data()
        
        return achievement
    
    def get_new_unlocked(self) -> List[Achievement]:
        """获取新解锁的成就"""
        unlocked = self._new_unlocked.copy()
        self._new_unlocked.clear()
        return unlocked
    
    def check_achievement(self, achievement_id: str) -> bool:
        """检查成就是否已解锁"""
        return self._achievements.get(achievement_id, Achievement("", "", "", "", "")).unlocked
    
    def get_all_achievements(self) -> List[Achievement]:
        """获取所有成就"""
        return list(self._achievements.values())
    
    def get_unlocked_achievements(self) -> List[Achievement]:
        """获取已解锁的成就"""
        return [a for a in self._achievements.values() if a.unlocked]
    
    def get_achievements_by_category(self, category: str) -> List[Achievement]:
        """获取指定分类的成就"""
        return [a for a in self._achievements.values() if a.category == category]
    
    def get_hidden_achievements(self) -> List[Achievement]:
        """获取所有隐藏成就"""
        return [a for a in self._achievements.values() if a.hidden]
    
    def get_visible_achievements(self) -> List[Achievement]:
        """获取可见成就（隐藏成就在未解锁时不显示条件）"""
        result = []
        for a in self._achievements.values():
            if a.hidden and not a.unlocked:
                visible_ach = Achievement(
                    id=a.id,
                    name="???",
                    description="???",
                    icon="🔒",
                    condition="???",
                    category=a.category,
                    hidden=True,
                    unlocked=False,
                    unlocked_at=None
                )
                result.append(visible_ach)
            else:
                result.append(a)
        return result
    
    def get_progress(self) -> tuple:
        """获取进度"""
        total = len(self._achievements)
        unlocked = sum(1 for a in self._achievements.values() if a.unlocked)
        return unlocked, total
    
    def get_unlocked_count(self) -> int:
        """获取已解锁成就数量"""
        return sum(1 for a in self._achievements.values() if a.unlocked)
    
    def get_total_count(self) -> int:
        """获取总成就数量"""
        return len(self._achievements)
    
    def on_first_launch(self):
        """首次启动"""
        if self._stats.get('first_launch_date') is None:
            self._stats['first_launch_date'] = datetime.now().isoformat()
            self.unlock('first_meet')
        self._save_data()
    
    def on_device_connected(self, device_id: str):
        """设备连接"""
        is_new_device = device_id not in self._connected_devices
        
        if is_new_device:
            self._connected_devices.add(device_id)
            self._stats['devices_connected'] = len(self._connected_devices)
            
            if self._stats['devices_connected'] == 1:
                self.unlock('first_connect')
            if self._stats['devices_connected'] >= 5:
                self.unlock('connect_5')
            if self._stats['devices_connected'] >= 10:
                self.unlock('connect_10')
        
        self._check_time_achievements()
        self._save_data()
    
    def on_video_downloaded(self, count: int = 1):
        """视频下载"""
        self._stats['videos_downloaded'] = self._stats.get('videos_downloaded', 0) + count
        
        total = self._stats['videos_downloaded']
        if total >= 1:
            self.unlock('first_download')
        if total >= 10:
            self.unlock('download_10')
        if total >= 50:
            self.unlock('download_50')
        if total >= 100:
            self.unlock('download_100')
        if total >= 500:
            self.unlock('download_500')
        
        self._save_data()
    
    def on_batch_download(self, count: int):
        """批量下载"""
        if count > self._stats.get('max_batch_download', 0):
            self._stats['max_batch_download'] = count
        
        if count >= 10:
            self.unlock('batch_10')
        if count >= 50:
            self.unlock('batch_50')
        if count >= 100:
            self.unlock('batch_100')
        
        self._save_data()
    
    def on_wireless_connect(self):
        """无线连接"""
        self._stats['wireless_connections'] = self._stats.get('wireless_connections', 0) + 1
        self.unlock('wireless_connect')
        self._save_data()
    
    def check_anniversary(self):
        """检查周年纪念"""
        first_launch = self._stats.get('first_launch_date')
        if first_launch:
            first_date = datetime.fromisoformat(first_launch)
            if (datetime.now() - first_date).days >= 365:
                self.unlock('anniversary')
    
    def get_stats(self) -> Dict[str, int]:
        """获取统计数据"""
        return self._stats.copy()
    
    def _check_time_achievements(self):
        """检查时间相关成就"""
        now = datetime.now()
        hour = now.hour
        
        if 0 <= hour < 5:
            self.unlock('night_owl')
        if 5 <= hour < 7:
            self.unlock('early_bird')
        if now.weekday() >= 5:
            self.unlock('weekend_warrior')
    
    def on_mascot_click(self):
        """吉祥物点击"""
        self._stats['mascot_clicks'] = self._stats.get('mascot_clicks', 0) + 1
        
        clicks = self._stats['mascot_clicks']
        if clicks >= 10:
            self.unlock('mascot_clicker')
        if clicks >= 50:
            self.unlock('mascot_lover')
        
        self._save_data()
    
    def on_theme_switch(self):
        """主题切换"""
        self._stats['theme_switches'] = self._stats.get('theme_switches', 0) + 1
        
        if self._stats['theme_switches'] >= 5:
            self.unlock('theme_switcher')
        
        self._save_data()
    
    def on_easter_egg_found(self):
        """发现彩蛋"""
        self.unlock('easter_egg')
        self._save_data()
    
    def on_secret_combo(self):
        """神秘组合"""
        self.unlock('secret_combo')
        self._save_data()
    
    def unlock_achievement(self, achievement_id: str) -> Optional[Achievement]:
        """解锁指定成就（公开方法）"""
        return self.unlock(achievement_id)
