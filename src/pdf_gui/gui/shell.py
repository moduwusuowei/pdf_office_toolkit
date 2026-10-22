"""调系统文件管理器打开目录（Windows 为主，其他平台尽力而为）。"""

import subprocess
import sys
from pathlib import Path


def open_folder(path: Path | str) -> bool:
    """在资源管理器里打开目录；目录不存在时先创建。失败返回 False，不抛异常。"""
    target = Path(path)
    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError:
        return False
    try:
        if sys.platform == "win32":
            import os
            os.startfile(str(target))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])
        return True
    except OSError:
        return False
