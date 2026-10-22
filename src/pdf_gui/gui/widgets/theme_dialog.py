"""配色编辑框：逐项点选浅色/深色，保存到配置文件并立即应用。"""

import tkinter as tk
from tkinter import colorchooser, messagebox

import customtkinter as ctk

from ..i18n import t
from ..theme import (
    DEFAULT_THEME,
    THEME_TOKENS,
    apply_theme,
    color,
    derive_hover,
    load_theme,
    save_theme,
)
from .dialog_util import center_over

_PAD = 20
_SWATCH_W = 104
_LABEL_W = 140


def _contrast_text(win, value: str) -> str:
    """按亮度给色块挑黑/白文字，避免浅色上看不清。"""
    try:
        r, g, b = win.winfo_rgb(value)      # 0..65535
    except tk.TclError:
        return "#000000"
    lum = (r * 299 + g * 587 + b * 114) / 1000 / 65535
    return "#000000" if lum > 0.55 else "#FFFFFF"


class ThemeDialog(ctk.CTkToplevel):
    def __init__(self, master, on_applied=None):
        super().__init__(master)
        self._on_applied = on_applied
        self.values = self._current_values()
        self._dirty: set[str] = set()   # 用户实际改过的项，保存时只覆盖这些
        self.title(t("theme_title"))
        self.resizable(False, False)
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.bind("<Escape>", lambda _e: self._close())

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=_PAD, pady=(_PAD, 8))

        ctk.CTkLabel(body, text=t("theme_title"),
                     font=ctk.CTkFont(size=18, weight="bold")
                     ).pack(anchor="w")
        ctk.CTkLabel(body, text=t("theme_hint"), justify="left", wraplength=520,
                     text_color=color("muted_text")
                     ).pack(anchor="w", pady=(4, 12))

        table = ctk.CTkFrame(body, fg_color="transparent")
        table.pack(fill="x")
        table.grid_columnconfigure(0, weight=1)
        for col, text in ((1, t("theme_light")), (2, t("theme_dark"))):
            ctk.CTkLabel(table, text=text, width=_SWATCH_W,
                         text_color=color("muted_text")
                         ).grid(row=0, column=col, padx=4, pady=(0, 4))

        self.swatches: dict[tuple[str, int], ctk.CTkButton] = {}
        for row, (token, label_key) in enumerate(THEME_TOKENS, start=1):
            ctk.CTkLabel(table, text=t(label_key), width=_LABEL_W, anchor="w"
                         ).grid(row=row, column=0, sticky="w", pady=3)
            for mode in (0, 1):     # 0 = 浅色，1 = 深色
                btn = ctk.CTkButton(
                    table, text="", width=_SWATCH_W, height=26,
                    command=lambda tk_=token, m=mode: self._pick(tk_, m))
                btn.grid(row=row, column=mode + 1, padx=4, pady=3)
                self.swatches[(token, mode)] = btn
        self._paint_all()

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=_PAD, pady=(4, _PAD))
        secondary = dict(fg_color=("gray70", "gray30"),
                         hover_color=("gray60", "gray40"),
                         text_color=color("text"))
        ctk.CTkButton(footer, text=t("theme_reset"), width=100,
                      command=self._reset, **secondary).pack(side="left")
        ctk.CTkButton(footer, text=t("theme_save"), width=130,
                      command=self._save).pack(side="right")
        ctk.CTkButton(footer, text=t("theme_cancel"), width=84,
                      command=self._close, **secondary
                      ).pack(side="right", padx=(0, 8))

        center_over(self, master, min_width=560)
        self.lift()
        self.grab_set()
        self.focus_force()

    # ---- 数据 ----
    @staticmethod
    def _current_values() -> dict[str, list[str]]:
        theme = load_theme()
        values = {}
        for token, _ in THEME_TOKENS:
            value = theme.get(token, DEFAULT_THEME[token])
            if isinstance(value, str):
                values[token] = [value, value]
            else:
                values[token] = [str(value[0]), str(value[1])]
        return values

    # ---- 交互 ----
    def _pick(self, token: str, mode: int) -> None:
        current = self.values[token][mode]
        _rgb, hex_color = colorchooser.askcolor(
            color=current, parent=self, title=t("theme_pick"))
        if not hex_color:
            return
        # 悬停色原本跟着主色走的话，改主色后继续跟；单独调过的悬停色保持不动
        follows = (token == "accent"
                   and self.values["accent_hover"] == derive_hover(self.values["accent"]))
        self.values[token][mode] = hex_color
        self._dirty.add(token)
        if follows:
            self.values["accent_hover"] = derive_hover(self.values["accent"])
            self._paint("accent_hover")
        self._paint(token)

    def _paint(self, token: str) -> None:
        for mode in (0, 1):
            value = self.values[token][mode]
            self.swatches[(token, mode)].configure(
                text=value, fg_color=value, hover_color=value,
                text_color=_contrast_text(self, value))

    def _paint_all(self) -> None:
        for token, _ in THEME_TOKENS:
            self._paint(token)

    def _reset(self) -> None:
        for token, _ in THEME_TOKENS:
            value = DEFAULT_THEME[token]
            self.values[token] = [value, value] if isinstance(value, str) else list(value)
            self._dirty.add(token)
        self._paint_all()

    def _save(self) -> None:
        # 以磁盘上的配置为底，只覆盖用户动过的项：没动的悬停色才能继续跟着主色推导
        theme = load_theme(derive=False)
        for token in self._dirty:
            theme[token] = list(self.values[token])
        if theme.get("accent_hover") == derive_hover(theme["accent"]):
            theme.pop("accent_hover", None)     # 推导值不落盘，换主色时自动重新推导
        if not save_theme(theme):
            messagebox.showerror(t("theme_title"), t("theme_save_fail"), parent=self)
            return
        apply_theme()   # 从文件重读（带推导），保证控件和配置文件一致
        self._close()
        if self._on_applied is not None:
            self._on_applied()

    def _close(self) -> None:
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
