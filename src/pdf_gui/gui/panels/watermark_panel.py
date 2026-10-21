"""水印面板：文字（平铺/居中）与图片两个标签页。"""

from pathlib import Path

import customtkinter as ctk

from ...core import add_image_watermark, add_text_watermark
from ...workers import Job, resolve_conflict
from ..i18n import t
from .base import PanelBase


class WatermarkPanel(PanelBase):
    name = "watermark"
    title_key = "wm_title"
    multi_file = True

    POS_VALUES = ["top-left", "top", "top-right", "left", "center", "right",
                  "bottom-left", "bottom", "bottom-right"]  # core 语义值，不做 i18n

    def build_params(self, parent):
        self.tabs = ctk.CTkTabview(parent)
        self.tabs.pack(fill="x", pady=4)
        self._tab_names = [t("wm_tab_text"), t("wm_tab_image")]
        tab_text = self.tabs.add(self._tab_names[0])
        tab_image = self.tabs.add(self._tab_names[1])
        # 文字水印
        self._labeled_entry(tab_text, "wm_text", "wm_text", default="机密")
        self._labeled_slider(tab_text, "wm_topacity", "wm_opacity", 0.0, 1.0, 0.15,
                             steps=20)
        self._labeled_slider(tab_text, "wm_angle", "wm_angle", -90, 90, 45,
                             steps=36, fmt=int)
        self._labeled_slider(tab_text, "wm_fontsize", "wm_fontsize", 8, 96, 36,
                             steps=88, fmt=int)
        self._radio(tab_text, "wm_mode", [(t("wm_tile"), "tile"),
                                          (t("wm_single"), "single")])
        self._labeled_entry(tab_text, "wm_pages", "wm_pages", default="")
        # 图片水印
        self._file_picker(tab_image, "wm_image", "wm_image", "choose_image",
                          [("Image", "*.png;*.jpg;*.jpeg;*.bmp")])
        self._labeled_slider(tab_image, "wm_iopacity", "wm_opacity", 0.0, 1.0, 0.3,
                             steps=20)
        self._labeled_slider(tab_image, "wm_isize", "wm_size", 0.05, 0.9, 0.3,
                             steps=17)
        self._option(tab_image, "wm_pos", "wm_pos", self.POS_VALUES, default_index=4)
        self._labeled_entry(tab_image, "wm_pages", "wm_pages", default="")
        # 恢复上次所在标签页（set 会触发 command，state 同步无害）
        self.tabs.configure(command=self._on_tab)
        self.tabs.set(self._tab_names[self.state.get("tab", 0)])

    def _on_tab(self) -> None:
        self.state["tab"] = self._tab_names.index(self.tabs.get())

    def make_jobs(self, files, out_dir):
        rule = self.conflict_rule
        pages = self.state.get("wm_pages", "") or "all"
        jobs, skipped = [], []
        if self.state.get("tab", 0) == 0:  # 文字
            text = (self.state.get("wm_text") or "").strip()
            if not text:
                raise ValueError(t("wm_text"))
            for f in files:
                f = Path(f)
                out = resolve_conflict(out_dir / f.name, rule)
                if out is None:
                    skipped.append(f.name)
                    continue
                jobs.append(Job(add_text_watermark, {
                    "src": f, "dst": out, "text": text,
                    "opacity": float(self.state.get("wm_topacity", 0.15)),
                    "angle": float(self.state.get("wm_angle", 45)),
                    "font_size": int(float(self.state.get("wm_fontsize", 36))),
                    "mode": "tile" if self.state.get("wm_mode", 0) == 0 else "single",
                    "pages": pages,
                }, label=f.name))
        else:  # 图片
            image_path = (self.state.get("wm_image") or "").strip()
            if not image_path:
                raise ValueError(t("wm_image"))
            for f in files:
                f = Path(f)
                out = resolve_conflict(out_dir / f.name, rule)
                if out is None:
                    skipped.append(f.name)
                    continue
                jobs.append(Job(add_image_watermark, {
                    "src": f, "dst": out, "image_path": image_path,
                    "opacity": float(self.state.get("wm_iopacity", 0.3)),
                    "size_ratio": float(self.state.get("wm_isize", 0.3)),
                    "pos": self.POS_VALUES[self.state.get("wm_pos", 4)],
                    "pages": pages,
                }, label=f.name))
        return jobs, skipped
