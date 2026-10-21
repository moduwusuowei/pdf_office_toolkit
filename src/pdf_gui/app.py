"""主窗口：左侧导航 + 右部面板容器；面板按需创建并缓存，切换不重建。"""

import queue

import customtkinter as ctk

from .gui.i18n import get_lang, set_lang, t
from .gui.meta import load_meta
from .gui.panels.compress_panel import CompressPanel
from .gui.panels.convert_panel import ConvertPanel
from .gui.panels.merge_panel import MergePanel
from .gui.panels.paging_seal_panel import PagingSealPanel
from .gui.panels.secure_panel import SecurePanel
from .gui.panels.split_panel import SplitPanel
from .gui.panels.stamp_panel import StampPanel
from .gui.panels.watermark_panel import WatermarkPanel
from .gui.settings import save_settings
from .gui.theme import color
from .gui.widgets.about_dialog import AboutDialog
from .gui.widgets.theme_dialog import ThemeDialog
from .workers import BatchWorker

# 各面板任务逐个追加：import …；PANELS 依序加入
PANELS: list[type] = [MergePanel, SplitPanel, WatermarkPanel, StampPanel,
                      PagingSealPanel, SecurePanel, CompressPanel, ConvertPanel]


class App(ctk.CTk):
    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        self.panel_state: dict[str, dict] = {}   # 面板名 → 参数状态（跨重建保留）
        self.events: "queue.Queue[tuple]" = queue.Queue()
        self.worker: BatchWorker | None = None
        self.current_panel = None
        self.panels: dict[type, object] = {}    # 已创建面板缓存：切换只显示/隐藏
        self.title(f"{t('app_title')} v{load_meta()['version']}")
        self.geometry("1150x720")
        self.minsize(980, 640)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_nav()
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)
        if PANELS:
            self.show_panel(PANELS[0])
        else:
            ctk.CTkLabel(self.container, text=t("wip")).grid(row=0, column=0)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(100, self._poll)

    # ---- 导航 ----
    def _build_nav(self):
        if hasattr(self, "nav"):
            self.nav.destroy()
        self.nav = ctk.CTkFrame(self, width=150)
        self.nav.grid(row=0, column=0, rowspan=1, sticky="nsw", padx=(8, 0), pady=8)
        for i, cls in enumerate(PANELS):
            ctk.CTkButton(
                self.nav, text=t(cls.title_key), anchor="w",
                command=lambda c=cls: self.show_panel(c),
            ).grid(row=i, column=0, sticky="ew", padx=6, pady=3)
        # 空行吃掉剩余高度，把配色/语言/关于三个按钮压在左下角
        spacer = len(PANELS)
        self.nav.grid_rowconfigure(spacer, weight=1)
        ctk.CTkButton(self.nav, text=t("theme"), command=self.show_theme
                      ).grid(row=spacer + 1, column=0, sticky="ew",
                             padx=6, pady=(0, 4))
        ctk.CTkButton(self.nav, text=t("lang_toggle"), command=self.switch_lang
                      ).grid(row=spacer + 2, column=0, sticky="ew",
                             padx=6, pady=(0, 4))
        ctk.CTkButton(self.nav, text=t("about"), command=self.show_about
                      ).grid(row=spacer + 3, column=0, sticky="ew",
                             padx=6, pady=(0, 6))

    # ---- 面板 ----
    def show_panel(self, cls: type):
        if self.current_panel is not None and type(self.current_panel) is cls:
            return
        panel = self.panels.get(cls)
        if panel is None:
            panel = cls(self.container, self)
            self.panels[cls] = panel
            panel.grid(row=0, column=0, sticky="nsew")
        # 面板始终留在布局里，切换只是置顶：不重建、不重新布局，切换即点即到
        panel.tkraise()
        self.current_panel = panel

    def switch_lang(self):
        set_lang("en" if get_lang() == "zh" else "zh")
        self.settings["lang"] = get_lang()
        self.title(f"{t('app_title')} v{load_meta()['version']}")
        self._rebuild_panels()

    def _rebuild_panels(self):
        """语言切换：导航与已创建面板全部重建（未打开过的面板下次再建）。"""
        current = type(self.current_panel) if self.current_panel is not None else None
        for panel in self.panels.values():
            panel.destroy()
        self.panels.clear()
        self.current_panel = None
        self._build_nav()
        if current is not None:
            self.show_panel(current)

    def show_about(self):
        """关于框：居中于主窗口，版本/版权/仓库来自 gui/app_meta.json。"""
        dialog = getattr(self, "_about", None)
        if dialog is not None and dialog.winfo_exists():
            dialog.lift()
            return
        self._about = AboutDialog(self)

    def show_theme(self):
        """配色编辑框：保存后立即重刷导航与面板，不必重启。"""
        dialog = getattr(self, "_theme_dialog", None)
        if dialog is not None and dialog.winfo_exists():
            dialog.lift()
            return
        self._theme_dialog = ThemeDialog(self, on_applied=self.reload_theme)

    def reload_theme(self) -> None:
        """主题表已更新：重画窗口底色，并重建导航与已打开面板。"""
        self.configure(fg_color=color("window_bg"))
        self._rebuild_panels()

    # ---- 弹窗 ----
    def ask_password(self, name: str) -> str | None:
        dialog = ctk.CTkInputDialog(
            text=t("password_prompt", name=name), title=t("app_title"))
        return dialog.get_input()

    # ---- 批处理 ----
    def run_worker(self, jobs, panel=None):
        if self.worker is not None and self.worker.is_alive():
            return
        self.events = queue.Queue()
        self.worker_panel = panel if panel is not None else self.current_panel
        self.worker = BatchWorker(jobs, self.events)
        self.worker.start()

    def cancel_worker(self):
        if self.worker is not None:
            self.worker.cancel()

    def _poll(self):
        # 事件投递到发起任务的面板，而不是"当前"面板：切走再切回也不串台
        panel = getattr(self, "worker_panel", None)
        try:
            while True:
                ev = self.events.get_nowait()
                if panel is None or not panel.winfo_exists():
                    continue
                rb = panel.run_bar
                if ev[0] == "job_start":
                    rb.on_job_start(ev[1], ev[2])
                elif ev[0] == "job_progress":
                    rb.on_progress(ev[1], ev[2], ev[3])
                elif ev[0] == "job_done":
                    rb.on_job_done(ev[1], ev[2], ev[3], ev[4])
                elif ev[0] == "finish":
                    rb.on_finish(ev[1], ev[2], ev[3], ev[4])
                    self.worker_panel = None
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def on_close(self):
        save_settings(self.settings)
        self.destroy()
