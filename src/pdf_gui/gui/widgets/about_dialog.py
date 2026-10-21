"""关于对话框：版本 / 版权 / 仓库 / 配色配置，居中于主窗口。"""

import os
import webbrowser
from pathlib import Path

import customtkinter as ctk

from ..i18n import t
from ..meta import load_meta
from ..theme import THEME_PATH, color
from .dialog_util import center_over

_PAD = 24


class AboutDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(t("about"))
        self.resizable(False, False)
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.bind("<Escape>", lambda _e: self._close())

        meta = load_meta()
        wrap = 400
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=_PAD, pady=(_PAD, 8))

        ctk.CTkLabel(body, text=t("app_title"),
                     font=ctk.CTkFont(size=20, weight="bold")
                     ).pack(anchor="w")
        ctk.CTkLabel(body, text=f"{t('about_version')} {meta['version']}",
                     text_color=color("muted_text")).pack(anchor="w", pady=(2, 12))
        ctk.CTkLabel(body, text=meta["copyright"]).pack(anchor="w", pady=2)

        repo = meta.get("repository", "")
        if repo:
            ctk.CTkLabel(body, text=f"{t('about_repository')}：{repo}",
                         wraplength=wrap, justify="left").pack(anchor="w", pady=2)
            ctk.CTkButton(body, text=t("about_open_repo"), width=120,
                          command=lambda: webbrowser.open(repo)
                          ).pack(anchor="w", pady=(6, 0))

        ctk.CTkLabel(body, text=t("about_theme"), font=ctk.CTkFont(weight="bold")
                     ).pack(anchor="w", pady=(16, 2))
        ctk.CTkLabel(body, text=str(THEME_PATH), text_color=color("muted_text"),
                     wraplength=wrap, justify="left").pack(anchor="w")
        ctk.CTkButton(body, text=t("about_open_theme"), width=140,
                      command=self._open_theme
                      ).pack(anchor="w", pady=(6, 0))
        ctk.CTkLabel(body, text=t("about_restart_hint"), text_color=color("muted_text")
                     ).pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(body, text=t("close_btn"), width=96,
                      command=self._close).pack(anchor="e", pady=(18, 0))

        center_over(self, master, min_width=460)
        self.lift()
        self.grab_set()
        self.focus_force()

    @staticmethod
    def _open_theme() -> None:
        path = Path(THEME_PATH)
        opener = getattr(os, "startfile", None)
        if opener is not None and path.exists():
            opener(path)

    def _close(self) -> None:
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
