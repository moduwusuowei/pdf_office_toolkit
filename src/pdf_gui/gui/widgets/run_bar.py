"""运行条控件：进度、状态、开始/取消，结束后弹结果报告。"""

from pathlib import Path

import customtkinter as ctk

from ..i18n import t
from ..shell import open_folder
from ..theme import color


class RunBar(ctk.CTkFrame):
    def __init__(self, master, *, on_start, on_cancel, settings=None,
                 out_dir_getter=None):
        super().__init__(master, fg_color="transparent")
        self._report: list[tuple[str, str, str | None]] = []  # (label, status, error)
        self._skipped: list[str] = []          # 冲突跳过的文件名
        self._current_label = ""
        self.on_start_cb = on_start
        self.settings = settings if settings is not None else {}
        self._out_dir_getter = out_dir_getter
        self.last_out_dir: Path | None = None  # 本次运行的输出目录（报告/自动打开用）
        self.grid_columnconfigure(0, weight=1)
        self.bar = ctk.CTkProgressBar(self)
        self.bar.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.status = ctk.CTkLabel(self, text="")
        self.status.grid(row=0, column=1, sticky="w", padx=(0, 10))
        self.start_btn = ctk.CTkButton(self, text=t("start"), width=90,
                                       command=self._clicked_start)
        self.start_btn.grid(row=1, column=0, pady=(6, 0))
        self.cancel_btn = ctk.CTkButton(self, text=t("cancel_run"), width=90,
                                        state="disabled", command=on_cancel)
        self.cancel_btn.grid(row=1, column=1, pady=(6, 0), sticky="w")
        self.auto_open = ctk.CTkCheckBox(self, text=t("auto_open_out"),
                                         command=self._toggle_auto_open)
        self.auto_open.grid(row=1, column=2, pady=(6, 0), sticky="e")
        if self.settings.get("auto_open_out"):
            self.auto_open.select()

    # ---- 对外接口 ----
    def set_skipped(self, skipped: list[str]) -> None:
        """面板在启动前告知因冲突跳过的文件，报告时计入「跳过」。"""
        self._skipped = list(skipped)

    def set_running(self, running: bool) -> None:
        self.start_btn.configure(state="disabled" if running else "normal")
        self.cancel_btn.configure(state="normal" if running else "disabled")
        if running:
            self.bar.set(0)
            self.status.configure(text=t("running_label"))
        else:
            self.bar.set(0)

    def _clicked_start(self) -> None:
        self._report = []
        self._skipped = []
        self.last_out_dir = (self._out_dir_getter()
                             if self._out_dir_getter is not None else None)
        self.on_start_cb()

    def _toggle_auto_open(self) -> None:
        self.settings["auto_open_out"] = bool(self.auto_open.get())

    def sync_settings(self) -> None:
        """设置是全局共享的：面板切换时把勾选状态拉回一致。"""
        if self.settings.get("auto_open_out"):
            self.auto_open.select()
        else:
            self.auto_open.deselect()

    # ---- 事件协议回调 ----
    def on_job_start(self, idx: int, label: str) -> None:
        self._current_label = label
        self.status.configure(text=label)

    def on_progress(self, idx: int, done: int, total: int) -> None:
        if total:
            self.bar.set(done / total)
        self.status.configure(text=t("job_progress", label=self._current_label,
                                      done=done, total=total))

    def on_job_done(self, idx: int, label: str, status: str,
                    error: str | None) -> None:
        self._report.append((label, status, error))

    def on_finish(self, ok: int, fail: int, cancelled: int,
                  errors: list[tuple[str, str | None]]) -> None:
        self.set_running(False)
        self.status.configure(text="")
        self.show_report(ok, fail, cancelled)

    # ---- 结果报告弹窗 ----
    def show_report(self, ok: int, fail: int, cancelled: int) -> None:
        win = ctk.CTkToplevel(self)
        win.title(t("report_title"))
        win.geometry("460x380")
        win.transient(self.winfo_toplevel())
        box = ctk.CTkTextbox(win)
        box.pack(padx=10, pady=(10, 4), fill="both", expand=True)
        for label in self._skipped:
            box.insert("end", f"⊘ {label}（{t('skip_note')}）\n")
        for label, status, error in self._report:
            if status == "ok":
                box.insert("end", f"✓ {label}\n")
            elif status == "fail":
                box.insert("end", f"✗ {label}：{error}\n")
            else:
                box.insert("end", f"⊘ {label}（{t('report_cancelled')}）\n")
        box.configure(state="disabled")
        footer = ctk.CTkLabel(
            win, text=f"{t('report_ok', n=ok)} / {t('report_fail', n=fail)}"
                      f" / {t('report_skip', n=len(self._skipped) + cancelled)}")
        footer.pack(pady=4)
        btns = ctk.CTkFrame(win, fg_color="transparent")
        btns.pack(pady=(0, 10))
        if self.last_out_dir is not None:
            ctk.CTkButton(btns, text=t("open_out_dir"), width=110,
                          command=lambda: open_folder(self.last_out_dir),
                          fg_color=("gray70", "gray30"),
                          text_color=color("text")).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btns, text=t("close_btn"), width=90,
                      command=win.destroy).pack(side="left")
