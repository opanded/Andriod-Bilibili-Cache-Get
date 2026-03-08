"""吉祥物状态定义"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Union


class MascotType(Enum):
    """吉祥物类型"""
    RABBIT_FROG = "rabbit_frog"
    DONUT = "donut"
    BOTH = "both"


class MascotState(Enum):
    """吉祥物状态 - 对应16个表情"""
    NORMAL = "normal"
    HAPPY = "happy"
    THINKING = "thinking"
    SAD = "sad"
    WORKING = "working"
    CELEBRATE = "celebrate"
    SLEEP = "sleep"
    WORRIED = "worried"
    EXCITED = "excited"
    RELAX = "relax"
    SURPRISED = "surprised"
    CONFUSED = "confused"
    LOVE = "love"
    COOL = "cool"


EXPRESSION_INDEX_MAP: Dict[MascotState, Union[int, List[int]]] = {
    MascotState.NORMAL: 0,
    MascotState.HAPPY: [1, 2, 7],
    MascotState.THINKING: 3,
    MascotState.SAD: 4,
    MascotState.WORKING: 5,
    MascotState.CELEBRATE: 6,
    MascotState.SLEEP: 8,
    MascotState.WORRIED: 9,
    MascotState.EXCITED: 10,
    MascotState.RELAX: 11,
    MascotState.SURPRISED: 12,
    MascotState.CONFUSED: 13,
    MascotState.LOVE: 14,
    MascotState.COOL: 15,
}


@dataclass
class MascotMessage:
    """吉祥物消息"""
    text: str
    kaomoji: str = ""


RABBIT_FROG_MESSAGES: Dict[MascotState, List[MascotMessage]] = {
    MascotState.NORMAL: [
        MascotMessage("有什么可以帮你的吗？", "(｡･ω･｡)"),
        MascotMessage("准备就绪！", "ヾ(≧▽≦*)o"),
        MascotMessage("等待你的指令~", "(｡･ω･｡)ﾉ♡"),
    ],
    MascotState.HAPPY: [
        MascotMessage("太棒了！完美完成！", "ヾ(≧▽≦*)o"),
        MascotMessage("成功啦！", "٩(๑❛ᴗ❛๑)۶"),
        MascotMessage("干得漂亮！", "(๑•̀ㅂ•́)و✧"),
    ],
    MascotState.THINKING: [
        MascotMessage("正在努力工作中...", "(｀・ω・´)"),
        MascotMessage("让我想想...", "(・_・)"),
        MascotMessage("正在处理...", "(๑•̀ㅂ•́)و"),
    ],
    MascotState.SAD: [
        MascotMessage("呜呜...出了点问题...", "(´;ω;`)"),
        MascotMessage("抱歉，没能完成...", "(´•ω•̥`)"),
        MascotMessage("让我重新试试...", "(；′⌒`)"),
    ],
    MascotState.WORKING: [
        MascotMessage("专注传输中！", "(๑•̀ㅂ•́)و✧"),
        MascotMessage("正在努力下载中...", "(｀・ω・´)"),
        MascotMessage("马上就好~", "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧"),
    ],
    MascotState.CELEBRATE: [
        MascotMessage("大功告成！", "✧*｡٩(ˊᗜˋ*)و✧*｡"),
        MascotMessage("完美！", "ヾ(≧▽≦*)o"),
        MascotMessage("全部完成！", "٩(๑❛ᴗ❛๑)۶"),
    ],
    MascotState.SLEEP: [
        MascotMessage("等待你的指令...", "(－ω－) zzZ"),
        MascotMessage("休息一下...", "(´▽`ʃ♡ƪ)"),
        MascotMessage("困了...", "(－ω－)"),
    ],
    MascotState.WORRIED: [
        MascotMessage("有点担心...", "(´・ω・`)"),
        MascotMessage("这样没问题吗？", "(；′⌒`)"),
        MascotMessage("希望一切顺利...", "(´･ω･`)"),
    ],
    MascotState.EXCITED: [
        MascotMessage("哇！好兴奋！", "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧"),
        MascotMessage("太刺激了！", "٩(๑❛ᴗ❛๑)۶"),
        MascotMessage("期待期待~", "ヾ(≧▽≦*)o"),
    ],
    MascotState.RELAX: [
        MascotMessage("放松一下~", "(´▽`ʃ♡ƪ)"),
        MascotMessage("悠闲自在~", "(｡･ω･｡)"),
        MascotMessage("慢慢来~", "(◕‿◕✿)"),
    ],
    MascotState.SURPRISED: [
        MascotMessage("诶？！真的吗？", "(°o°)"),
        MascotMessage("哇！没想到！", "(ﾟДﾟ)"),
        MascotMessage("太意外了！", "(⊙o⊙)"),
    ],
    MascotState.CONFUSED: [
        MascotMessage("嗯？这是怎么回事...", "(・_・)"),
        MascotMessage("有点困惑...", "(´・ω・`)"),
        MascotMessage("不太明白...", "(；・∀・)"),
    ],
    MascotState.LOVE: [
        MascotMessage("好喜欢你呀~", "(´▽`ʃ♡ƪ)"),
        MascotMessage("谢谢你的陪伴！", "(◕‿◕✿)"),
        MascotMessage("你是最棒的！", "♡(◡‿◡)"),
    ],
    MascotState.COOL: [
        MascotMessage("小菜一碟！", "(￣▽￣)b"),
        MascotMessage("轻松搞定~", "(・ω・)b"),
        MascotMessage("没问题！", "(๑•̀ㅂ•́)و✧"),
    ],
}

DONUT_MESSAGES: Dict[MascotState, List[MascotMessage]] = {
    MascotState.NORMAL: [
        MascotMessage("甜甜的等待中~", "(◕‿◕✿)"),
        MascotMessage("有什么可以帮你的吗？", "(｡･ω･｡)ﾉ♡"),
        MascotMessage("准备就绪！", "ヾ(≧▽≦*)o"),
    ],
    MascotState.HAPPY: [
        MascotMessage("找到设备啦！", "٩(๑❛ᴗ❛๑)۶"),
        MascotMessage("成功啦！", "(◕‿◕✿)"),
        MascotMessage("太棒了！", "ヾ(≧▽≦*)o"),
    ],
    MascotState.WORRIED: [
        MascotMessage("设备好像断开了...", "(´・ω・`)"),
        MascotMessage("连接丢失了...", "(´･ω･`)"),
        MascotMessage("设备去哪了...", "(；′⌒`)"),
    ],
    MascotState.EXCITED: [
        MascotMessage("发现新视频！", "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧"),
        MascotMessage("好多内容！", "٩(๑❛ᴗ❛๑)۶"),
        MascotMessage("太棒了！", "ヾ(≧▽≦*)o"),
    ],
    MascotState.RELAX: [
        MascotMessage("休息一下吧~", "(´▽`ʃ♡ƪ)"),
        MascotMessage("慢慢来~", "(◕‿◕✿)"),
        MascotMessage("不着急~", "(｡･ω･｡)"),
    ],
    MascotState.SAD: [
        MascotMessage("呜呜...失败了...", "(´;ω;`)"),
        MascotMessage("抱歉...", "(´•ω•̥`)"),
        MascotMessage("让我试试...", "(；′⌒`)"),
    ],
    MascotState.WORKING: [
        MascotMessage("正在搬运中~", "(๑´ڡ`๑)"),
        MascotMessage("努力工作中...", "(◕‿◕✿)"),
    ],
    MascotState.CELEBRATE: [
        MascotMessage("完成啦！", "٩(๑❛ᴗ❛๑)۶"),
        MascotMessage("太棒了！", "(◕‿◕✿)"),
    ],
    MascotState.SLEEP: [
        MascotMessage("休息中...", "(－ω－)"),
        MascotMessage("困了...", "(´▽`ʃ♡ƪ)"),
    ],
    MascotState.THINKING: [
        MascotMessage("让我想想...", "(・_・)"),
        MascotMessage("正在处理...", "(◕‿◕✿)"),
    ],
    MascotState.SURPRISED: [
        MascotMessage("诶？！真的吗？", "(°o°)"),
        MascotMessage("哇！没想到！", "(ﾟДﾟ)"),
    ],
    MascotState.CONFUSED: [
        MascotMessage("嗯？这是怎么回事...", "(・_・)"),
        MascotMessage("有点困惑...", "(´・ω・`)"),
    ],
    MascotState.LOVE: [
        MascotMessage("好喜欢你呀~", "(´▽`ʃ♡ƪ)"),
        MascotMessage("谢谢你的陪伴！", "(◕‿◕✿)"),
    ],
    MascotState.COOL: [
        MascotMessage("小菜一碟！", "(￣▽￣)b"),
        MascotMessage("轻松搞定~", "(・ω・)b"),
    ],
}


def get_mascot_message(mascot_type: MascotType, state: MascotState) -> MascotMessage:
    """获取吉祥物消息"""
    import random
    
    if mascot_type == MascotType.RABBIT_FROG:
        messages = RABBIT_FROG_MESSAGES.get(state, RABBIT_FROG_MESSAGES[MascotState.NORMAL])
    else:
        messages = DONUT_MESSAGES.get(state, DONUT_MESSAGES[MascotState.NORMAL])
    
    return random.choice(messages)


def get_expression_index(state: MascotState) -> int:
    """获取状态对应的表情索引
    
    对于有多种表情变体的状态，随机返回一个索引
    """
    import random
    
    indices = EXPRESSION_INDEX_MAP.get(state, 0)
    
    if isinstance(indices, list):
        return random.choice(indices)
    
    return indices


class MascotMessageHelper:
    """吉祥物消息帮助类 - 用于生成各类场景的提示消息"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @staticmethod
    def download_start(video_title: str, up_name: str = None) -> tuple:
        """开始下载消息
        
        Returns:
            (message, state) 元组
        """
        import random
        title_short = video_title[:20] + "..." if len(video_title) > 20 else video_title
        
        if up_name:
            msgs = [
                (f"🐰🐸 开始下载《{title_short}》\nUP主是「{up_name[:10]}」哦！", MascotState.WORKING),
                (f"🍩 收到！搬运《{title_short}》\n来自「{up_name[:10]}」~", MascotState.HAPPY),
            ]
        else:
            msgs = [
                (f"🐰🐸 开始下载《{title_short}》啦~", MascotState.WORKING),
                (f"🍩 收到！正在搬运中~", MascotState.HAPPY),
                (f"🐰🐸 好的！马上开始~", MascotState.WORKING),
            ]
        return random.choice(msgs)
    
    @staticmethod
    def batch_download(count: int) -> tuple:
        """批量下载消息"""
        import random
        msgs = [
            (f"🐰🐸 哇！{count}个任务，我来啦！", MascotState.EXCITED),
            (f"🍩 收到！开始下载{count}个视频~", MascotState.HAPPY),
            (f"🐰🐸 好的好的，{count}个任务马上开始！", MascotState.WORKING),
        ]
        return random.choice(msgs)
    
    @staticmethod
    def download_complete(count: int = 1) -> tuple:
        """下载完成消息"""
        import random
        if count > 1:
            msgs = [
                (f"🐰🐸 太棒了！{count}个视频全部完成！", MascotState.CELEBRATE),
                (f"🍩 完美！{count}个任务搞定啦~", MascotState.HAPPY),
                (f"✧*｡٩(ˊᗜˋ*)و✧*｡ 全部完成！", MascotState.CELEBRATE),
                (f"🐰🐸 哇！{count}个视频都下载好了！", MascotState.HAPPY),
                (f"🍩 辛苦啦！{count}个任务完美收官~", MascotState.RELAX),
                (f"🎉 恭喜！{count}个视频安全抵达！", MascotState.CELEBRATE),
            ]
        else:
            msgs = [
                ("🐰🐸 下载完成啦！", MascotState.HAPPY),
                ("🍩 搞定！视频已经准备好了~", MascotState.CELEBRATE),
                ("✧*｡٩(ˊᗜˋ*)و✧*｡ 完美！", MascotState.HAPPY),
                ("🐰🐸 又搞定一个！", MascotState.COOL),
                ("🍩 轻松拿下~", MascotState.RELAX),
                ("✨ 视频到手！", MascotState.HAPPY),
                ("🐰🐸 任务完成！", MascotState.NORMAL),
                ("🍩 OK！下一个~", MascotState.WORKING),
            ]
        return random.choice(msgs)
    
    @staticmethod
    def farewell() -> tuple:
        """告别消息"""
        import random
        msgs = [
            ("🐰🐸 诶诶要走了吗？下次见哦！", MascotState.SAD),
            ("🍩 期待下次相遇~", MascotState.SAD),
            ("🐰🐸 再见啦！别忘了回来哦！", MascotState.SAD),
        ]
        return random.choice(msgs)
    
    @staticmethod
    def device_found(count: int = 1) -> tuple:
        """发现设备消息"""
        import random
        if count > 1:
            msgs = [
                (f"🐰🐸 找到{count}个设备啦！", MascotState.HAPPY),
                (f"🍩 发现{count}个设备~", MascotState.EXCITED),
            ]
        else:
            msgs = [
                ("🐰🐸 找到设备啦！", MascotState.HAPPY),
                ("🍩 发现一个设备~", MascotState.NORMAL),
            ]
        return random.choice(msgs)
    
    @staticmethod
    def device_disconnected() -> tuple:
        """设备断开消息"""
        import random
        msgs = [
            ("🐰🐸 设备好像断开了...", MascotState.SAD),
            ("🍩 设备去哪了？", MascotState.WORRIED),
        ]
        return random.choice(msgs)
    
    @staticmethod
    def loading(what: str = "视频") -> tuple:
        """加载中消息"""
        import random
        msgs = [
            (f"🐰🐸 正在扫描{what}...", MascotState.THINKING),
            (f"🍩 加载{what}中~", MascotState.WORKING),
            (f"🐰🐸 马上就好~", MascotState.WORKING),
        ]
        return random.choice(msgs)
    
    @staticmethod
    def video_loaded(count: int) -> tuple:
        """视频加载完成消息"""
        import random
        msgs = [
            (f"🐰🐸 找到{count}个视频！", MascotState.HAPPY),
            (f"🍩 扫描完成，共{count}个视频~", MascotState.NORMAL),
        ]
        return random.choice(msgs)
    
    @staticmethod
    def welcome() -> tuple:
        """欢迎消息"""
        import random
        msgs = [
            ("🐰🐸 欢迎回来！", MascotState.HAPPY),
            ("🍩 你来啦~", MascotState.NORMAL),
            ("🐰🐸 准备就绪！", MascotState.HAPPY),
        ]
        return random.choice(msgs)
    
    @staticmethod
    def error(what: str = "操作") -> tuple:
        """错误消息（信息性，非严重错误）"""
        import random
        msgs = [
            (f"🐰🐸 {what}失败了...让我再试试", MascotState.SAD),
            (f"🍩 哎呀，{what}出了点问题", MascotState.CONFUSED),
        ]
        return random.choice(msgs)
    
    @staticmethod
    def tips() -> tuple:
        """小贴士消息"""
        import random
        tips = [
            "💡 小提示：双击标题可以快速下载哦~",
            "💡 小提示：按Ctrl+F可以快速搜索~",
            "💡 小提示：支持无线ADB连接呢~",
            "💡 小提示：可以切换深色/浅色主题哦~",
            "💡 小提示：下载历史可以查看记录~",
            "💡 小提示：多P视频会自动合并~",
            "💡 小提示：封面可以点击放大预览~",
        ]
        return (random.choice(tips), MascotState.NORMAL)
    
    @staticmethod
    def love() -> tuple:
        """爱心互动消息"""
        import random
        msgs = [
            ("🐰🐸 好喜欢你呀~", MascotState.LOVE),
            ("🍩 谢谢你的陪伴！", MascotState.LOVE),
        ]
        return random.choice(msgs)
    
    @staticmethod
    def surprised() -> tuple:
        """惊讶消息"""
        import random
        msgs = [
            ("🐰🐸 诶？！真的吗？", MascotState.SURPRISED),
            ("🍩 哇！没想到！", MascotState.SURPRISED),
        ]
        return random.choice(msgs)
    
    @staticmethod
    def cool() -> tuple:
        """酷消息"""
        import random
        msgs = [
            ("🐰🐸 小菜一碟！", MascotState.COOL),
            ("🍩 轻松搞定~", MascotState.COOL),
        ]
        return random.choice(msgs)


UI_ELEMENT_DESCRIPTIONS = {
    "device_panel": {
        "title": "设备列表",
        "desc": "这里显示已连接的设备，点击可以切换设备",
        "tip": "💡 支持有线和无线连接哦~"
    },
    "video_panel": {
        "title": "视频列表",
        "desc": "显示当前设备的缓存视频，双击可以下载",
        "tip": "💡 按住Ctrl可以多选~"
    },
    "download_panel": {
        "title": "下载队列",
        "desc": "显示正在进行的下载任务",
        "tip": "💡 可以暂停或取消任务~"
    },
    "refresh_btn": {
        "title": "刷新按钮",
        "desc": "重新扫描设备的缓存视频",
        "tip": "💡 快捷键: F5"
    },
    "download_btn": {
        "title": "下载按钮",
        "desc": "下载选中的视频到电脑",
        "tip": "💡 双击视频也可以下载~"
    },
    "settings_btn": {
        "title": "设置按钮",
        "desc": "打开设置对话框，配置下载选项",
        "tip": "💡 可以切换主题和设置下载路径~"
    },
    "backup_btn": {
        "title": "备份按钮",
        "desc": "导出或导入下载历史记录",
        "tip": "💡 换电脑也不用担心记录丢失~"
    },
    "history_btn": {
        "title": "历史记录",
        "desc": "查看所有下载历史",
        "tip": "💡 可以重新下载或打开文件~"
    },
    "wireless_btn": {
        "title": "无线连接",
        "desc": "通过无线ADB连接设备",
        "tip": "💡 需要先在设备上开启无线调试~"
    },
    "theme_btn": {
        "title": "切换主题",
        "desc": "在深色和浅色主题之间切换",
        "tip": "💡 快捷键: Ctrl+T"
    },
    "search_box": {
        "title": "搜索框",
        "desc": "输入关键词搜索视频",
        "tip": "💡 支持标题和UP主搜索~"
    },
    "filter_combo": {
        "title": "筛选器",
        "desc": "按下载状态筛选视频",
        "tip": "💡 可以只显示未下载的视频~"
    },
    "progress_bar": {
        "title": "进度条",
        "desc": "显示当前下载进度",
        "tip": "💡 鼠标悬停可以看到速度~"
    },
    "status_bar": {
        "title": "状态栏",
        "desc": "显示当前操作状态和提示",
        "tip": "💡 这里会有各种提示信息~"
    },
    "mascot": {
        "title": "吉祥物",
        "desc": "点击我会有惊喜哦！",
        "tip": "💡 长按或双击试试~"
    },
    "video_item": {
        "title": "视频条目",
        "desc": "这是一个缓存视频，双击可以下载",
        "tip": "💡 勾选可以批量下载~"
    },
    "checkbox": {
        "title": "复选框",
        "desc": "勾选这个视频进行批量操作",
        "tip": "💡 按住Shift可以范围选择~"
    },
    "cover": {
        "title": "视频封面",
        "desc": "点击可以放大预览",
        "tip": "💡 显示视频的第一帧~"
    },
    "title": {
        "title": "视频标题",
        "desc": "视频的标题，点击可以复制",
        "tip": "💡 双击可以快速下载~"
    },
    "owner": {
        "title": "UP主",
        "desc": "视频的创作者",
        "tip": "💡 点击可以复制名字~"
    },
    "duration": {
        "title": "时长",
        "desc": "视频的播放时长",
        "tip": "💡 格式为 分:秒~"
    },
    "size": {
        "title": "大小",
        "desc": "视频文件的大小",
        "tip": "💡 单位是MB~"
    },
    "status": {
        "title": "状态",
        "desc": "视频的下载状态",
        "tip": "💡 有未下载、下载中、已完成等状态~"
    },
}


def get_element_description(element_type: str) -> dict:
    """获取UI元素的描述
    
    Args:
        element_type: 元素类型
        
    Returns:
        包含title, desc, tip的字典
    """
    return UI_ELEMENT_DESCRIPTIONS.get(element_type, {
        "title": "未知元素",
        "desc": "这是一个UI元素",
        "tip": "💡 试试看有什么功能~"
    })
