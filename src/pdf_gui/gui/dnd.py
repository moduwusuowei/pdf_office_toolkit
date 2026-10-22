"""拖拽入队：用 tkdnd（tkinterdnd2）在 Tcl 层接收拖放。

不用 ctypes 子类化窗口过程（windnd 那种做法在 Python 3.12 上会在拖放时
抛出 `Fatal Python error: PyEval_RestoreThread ... GIL is released`）。
非 Windows 或缺少 tkinterdnd2 时静默降级，按钮添加照常可用。
"""

from __future__ import annotations

import locale
from collections.abc import Callable


def _decode(value) -> str:
    """Tcl 字符串按解释器编码解出；万一拿到字节串再按系统代码页兜底。"""
    if isinstance(value, str):
        return value
    for enc in ("utf-8", locale.getpreferredencoding(False), "gbk"):
        try:
            return value.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return value.decode("utf-8", "replace")


def split_paths(tkapp, data: str) -> list[str]:
    """把 tkdnd 给的数据串（Tcl 列表，路径可能带空格/花括号）拆成路径列表。"""
    try:
        raw = tkapp.splitlist(data)
    except Exception:
        raw = [data]
    return [p for p in (_decode(item) for item in raw) if p]


def enable_drop(window, handler: Callable[[list[str]], None]) -> bool:
    """给 window 开启文件拖拽；返回是否成功。handler 在 Tk 主线程、下一拍执行。"""
    try:
        from tkinterdnd2 import DND_FILES, TkinterDnD
    except Exception:       # 未安装（例如 Linux 开发机）
        return False

    class DropTarget(TkinterDnD.DnDWrapper):
        """借 DnDWrapper 的 Tcl 命令，但不改控件的类（CTk 窗口保持原样）。"""

        def __init__(self, widget):
            self._w = widget._w
            self.tk = widget.tk
            self.nametowidget = widget.nametowidget
            self._register = widget._register

        def on_drop(self, event) -> str:
            paths = split_paths(self.tk, getattr(event, "data", "") or "")
            if paths:
                # 落盘/建队列放在下一拍：拖放回调里不弹密码框、不做嵌套事件循环
                window.after_idle(handler, paths)
            # 必须回 copy：缺省动作可能把资源管理器里的源文件“移动”走
            return "copy"

    try:
        TkinterDnD._require(window)          # 把 tkdnd 载入当前 Tcl 解释器
        target = DropTarget(window)
        target.drop_target_register(DND_FILES)
        target.dnd_bind("<<Drop>>", target.on_drop)
    except Exception:       # 平台不支持 / tkdnd 加载失败
        return False
    window._drop_target = target           # 保住引用，便于调试与测试
    return True
