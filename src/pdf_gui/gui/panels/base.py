"""面板基类：三段式布局（文件队列 / 参数区 / 输出+运行条）与参数控件助手。

子类只需设 name/title_key/multi_file 三个类属性，
实现 build_params(parent) 与 make_jobs(files, out_dir)。"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from ..i18n import t
from ..theme import color
from ..widgets.file_queue import FileQueue
from ..widgets.run_bar import RunBar

CONFLICT_RULES = ["rename", "overwrite", "skip"]


class PanelBase(ctk.CTkFrame):
    name = "base"
    title_key = "app_title"
    multi_file = True  # False = 单文件面板（FileQueue 添加新文件时替换）

    def __init__(self, master, app):
        # 不透明底色：多个面板叠放在同一格，靠 tkraise 切换，避免每次重新布局
        super().__init__(master, fg_color=color("window_bg"))
        self.app = app
        self.state: dict = app.panel_state.setdefault(self.name, {})
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        # 行 0：标题
        ctk.CTkLabel(self, text=t(self.title_key),
                     font=ctk.CTkFont(size=18, weight="bold")
                     ).grid(row=0, column=0, sticky="w", pady=(0, 8))
        # 行 1：文件队列
        self.file_queue = FileQueue(
            self, max_files=0 if self.multi_file else 1,
            ask_password=app.ask_password, on_change=self.on_files_changed,
            state=self.state)
        self.file_queue.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        # 行 2：参数区（滚动）
        self.params = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.params.grid(row=2, column=0, sticky="nsew")
        self.build_params(self.params)
        # 行 3：输出目录 + 冲突规则 + 运行条
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        bottom.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(bottom, text=t("out_dir_label")).grid(row=0, column=0, sticky="w")
        self.out_entry = ctk.CTkEntry(bottom, placeholder_text=t("out_dir_label"))
        self.out_entry.insert(0, self.state.get("out_dir", app.settings["out_dir"]))
        self.out_entry.grid(row=0, column=1, sticky="ew", padx=6)
        ctk.CTkButton(bottom, text=t("choose_dir"), width=80,
                       command=self._browse_out).grid(row=0, column=2)
        self._conflict_labels = [t("conflict_rename"), t("conflict_overwrite"),
                                 t("conflict_skip")]
        ctk.CTkLabel(bottom, text=t("conflict_label")).grid(row=0, column=3, padx=(16, 4))
        try:
            default_rule = CONFLICT_RULES.index(app.settings.get("conflict", "rename"))
        except ValueError:
            default_rule = 0
        self.state.setdefault("conflict", default_rule)
        self.conflict_menu = ctk.CTkOptionMenu(
            bottom, values=self._conflict_labels, command=self._on_conflict)
        self.conflict_menu.set(self._conflict_labels[self.state["conflict"]])
        self.conflict_menu.grid(row=0, column=4, padx=(0, 8))
        self.run_bar = RunBar(bottom, on_start=self._start,
                              on_cancel=app.cancel_worker)
        self.run_bar.grid(row=1, column=0, columnspan=5, sticky="ew", pady=(8, 0))

    # ---- 子类钩子 ----
    def build_params(self, parent) -> None:
        raise NotImplementedError

    def make_jobs(self, files: list[Path], out_dir: Path):
        """返回 (jobs, skipped)；非法参数 raise ValueError（基类弹窗提示）。"""
        raise NotImplementedError

    def on_files_changed(self) -> None:
        """FileQueue 增删后的回调，默认空操作（盖章面板用来刷新预览）。"""

    # ---- 派生属性 ----
    @property
    def conflict_rule(self) -> str:
        return CONFLICT_RULES[self.state.get("conflict", 0)]

    # ---- 启动 ----
    def _start(self) -> None:
        files = self.file_queue.paths()
        if not files:
            messagebox.showwarning(t("app_title"), t("no_files"))
            return
        out_dir = Path(self.out_entry.get())
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            probe = out_dir / ".write_test"
            probe.write_text("", encoding="utf-8")
            probe.unlink()
        except OSError:
            messagebox.showerror(t("app_title"), t("write_test_fail"))
            return
        try:
            jobs, skipped = self.make_jobs(files, out_dir)
        except ValueError as e:
            messagebox.showerror(t("app_title"), str(e))
            return
        if not jobs and not skipped:
            return
        self.state["out_dir"] = str(out_dir)
        self.run_bar.set_skipped(skipped)
        self.run_bar.set_running(True)
        self.app.run_worker(jobs, self)

    def _browse_out(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.out_entry.delete(0, "end")
            self.out_entry.insert(0, folder)

    def _on_conflict(self, choice: str) -> None:
        self.state["conflict"] = self._conflict_labels.index(choice)
        self.app.settings["conflict"] = self.conflict_rule

    # ---- 参数控件助手（全部自动持久化到 self.state，键即存储名） ----
    def _labeled_entry(self, parent, key: str, label_key: str, default: str = "",
                       show: str = "") -> ctk.CTkEntry:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text=t(label_key), width=130, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(row, width=220, show=show) if show else ctk.CTkEntry(row, width=220)
        entry.insert(0, str(self.state.get(key, default)))
        entry.bind("<KeyRelease>", lambda _e: self.state.__setitem__(key, entry.get()))
        entry.bind("<FocusOut>", lambda _e: self.state.__setitem__(key, entry.get()))
        entry.pack(side="left")
        self.state[key] = entry.get()
        return entry

    def _labeled_slider(self, parent, key: str, label_key: str, from_: float,
                        to: float, default: float, *, steps: int = 100,
                        fmt=None, command=None) -> ctk.CTkSlider:
        """fmt=int 时按整数显示（dpi/质量/字号等）。"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text=t(label_key), width=130, anchor="w").pack(side="left")
        val = ctk.CTkLabel(row, width=44, anchor="w")

        def show(v):
            val.configure(text=str(int(v)) if fmt is int else f"{float(v):.2f}")
            self.state[key] = float(v)
            if command:
                command(float(v))

        slider = ctk.CTkSlider(row, from_=from_, to=to, number_of_steps=steps,
                               command=show)
        initial = float(self.state.get(key, default))
        slider.set(initial)
        slider.pack(side="left", padx=(4, 8))
        val.pack(side="left")
        show(initial)
        return slider

    def _radio(self, parent, key: str, options: list[tuple[str, str]]) -> tk.StringVar:
        """options: [(显示文本, 语义值)]；state 存索引。"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        var = tk.StringVar(value=str(self.state.get(key, 0)))
        for i, (text, _) in enumerate(options):
            ctk.CTkRadioButton(
                row, text=text, variable=var, value=str(i),
                command=lambda v=var, k=key: self.state.__setitem__(k, int(v.get())),
            ).pack(side="left", padx=(0, 12))
        self.state[key] = int(var.get())
        return var

    def _option(self, parent, key: str, label_key: str, values: list[str],
                default_index: int = 0) -> ctk.CTkOptionMenu:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text=t(label_key), width=130, anchor="w").pack(side="left")
        menu = ctk.CTkOptionMenu(
            row, values=values, width=200,
            command=lambda choice: self.state.__setitem__(key, values.index(choice)))
        current = self.state.get(key, default_index)
        menu.set(values[current])
        menu.pack(side="left")
        self.state[key] = current
        return menu

    def _file_picker(self, parent, key: str, label_key: str, pick_btn_key: str,
                     filetypes: list[tuple[str, str]], command=None) -> ctk.CTkEntry:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text=t(label_key), width=130, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(row, width=260)
        entry.insert(0, str(self.state.get(key, "")))
        entry.bind("<KeyRelease>", lambda _e: self.state.__setitem__(key, entry.get()))
        entry.bind("<FocusOut>", lambda _e: self.state.__setitem__(key, entry.get()))
        entry.pack(side="left", padx=(0, 8))
        self.state[key] = entry.get()

        def pick():
            path = filedialog.askopenfilename(filetypes=filetypes)
            if path:
                entry.delete(0, "end")
                entry.insert(0, path)
                self.state[key] = path
                if command:
                    command(path)

        ctk.CTkButton(row, text=t(pick_btn_key), width=90, command=pick).pack(side="left")
        return entry
