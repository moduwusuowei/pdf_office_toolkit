"""程序入口。"""

import customtkinter as ctk

from .app import App
from .gui.i18n import set_lang
from .gui.settings import load_settings
from .gui.theme import apply_theme, ensure_theme_file


def main():
    settings = load_settings()
    set_lang(settings.get("lang", "zh"))
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    ensure_theme_file()   # 首启落一份默认配色文件，用户可直接编辑
    apply_theme()         # 须在创建任何控件之前
    App(settings).mainloop()


if __name__ == "__main__":
    main()
