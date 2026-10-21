"""对话框通用：把 Toplevel 居中到父窗口（而非屏幕）。"""


def center_over(window, master, min_width: int = 0) -> None:
    window.update_idletasks()
    width = max(min_width, window.winfo_reqwidth())
    height = window.winfo_reqheight()
    parent_w = master.winfo_width() or master.winfo_reqwidth()
    parent_h = master.winfo_height() or master.winfo_reqheight()
    x = master.winfo_rootx() + max(0, (parent_w - width) // 2)
    y = master.winfo_rooty() + max(0, (parent_h - height) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.update_idletasks()
    # 窗口管理器会加标题栏/边框，导致内容区偏移；再校正一次
    off_x = window.winfo_rootx() - x
    off_y = window.winfo_rooty() - y
    if off_x or off_y:
        window.geometry(f"+{x - off_x}+{y - off_y}")
