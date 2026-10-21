"""盖章面板：单文件、预览点击定位、参数实时反映到预览。"""

from pathlib import Path

import customtkinter as ctk

from ...core import stamp_pdf
from ...workers import Job, resolve_conflict
from ..i18n import t
from ..theme import color
from ..widgets.preview import PagePreview
from .base import PanelBase


class StampPanel(PanelBase):
    name = "stamp"
    title_key = "stamp_title"
    multi_file = False

    def build_params(self, parent):
        self._file_picker(parent, "png", "stamp_png", "choose_image",
                          [("PNG", "*.png")], command=lambda _p: self._refresh_preview())
        self._labeled_slider(parent, "size", "stamp_size", 0.05, 0.9, 0.25,
                             steps=17, command=self._refresh_preview)
        self._labeled_slider(parent, "opacity", "stamp_opacity", 0.05, 1.0, 1.0,
                             steps=19, command=self._refresh_preview)
        self._labeled_entry(parent, "pages", "wm_pages", default="all")
        ctk.CTkLabel(parent, text=t("stamp_hint"),
                     text_color=color("muted_text")).pack(anchor="w", pady=2)
        self.preview = PagePreview(parent, on_place=self._on_place)
        self.preview.pack(pady=8)

    def on_files_changed(self) -> None:
        self._refresh_preview()

    def _current_file(self):
        files = self.file_queue.paths()
        return files[0] if files else None

    def _refresh_preview(self, *_args) -> None:
        if not hasattr(self, "preview"):
            return   # 滑杆初始化先于预览创建
        f = self._current_file()
        png = (self.state.get("png") or "").strip()
        if not (f and png):
            return
        try:
            self.preview.load_pdf(f, page=0)
            self.preview.set_stamp(
                png,
                float(self.state.get("size", 0.25)),
                float(self.state.get("opacity", 1.0)),
                float(self.state.get("x", 0.8)),
                float(self.state.get("y", 0.15)))
        except Exception:
            pass  # 预览失败（文件渲染问题等）不打断主流程

    def _on_place(self, x: float, y: float) -> None:
        self.state["x"], self.state["y"] = x, y
        self._refresh_preview()

    def make_jobs(self, files, out_dir):
        png = (self.state.get("png") or "").strip()
        if not png:
            raise ValueError(t("stamp_png"))
        rule = self.conflict_rule
        jobs, skipped = [], []
        for f in files:
            f = Path(f)
            out = resolve_conflict(out_dir / f.name, rule)
            if out is None:
                skipped.append(f.name)
                continue
            jobs.append(Job(stamp_pdf, {
                "src": f, "dst": out, "stamp_png": png,
                "pages": self.state.get("pages", "") or "all",
                "x_ratio": float(self.state.get("x", 0.8)),
                "y_ratio": float(self.state.get("y", 0.15)),
                "size_ratio": float(self.state.get("size", 0.25)),
                "opacity": float(self.state.get("opacity", 1.0)),
            }, label=f.name))
        return jobs, skipped
