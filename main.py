"""B站缓存视频下载工具 - 主入口"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.gui.main_window import main

if __name__ == '__main__':
    main()
