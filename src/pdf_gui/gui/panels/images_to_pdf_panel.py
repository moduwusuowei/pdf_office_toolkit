"""图片转 PDF 面板：按队列顺序把多张图片合成一份 PDF。"""

from pathlib import Path

import customtkinter as ctk

from ...core import images_to_pdf
from ...workers import Job, resolve_conflict
from ..i18n import t
from ..theme import color
from .base import PanelBase

PAGE_SIZES = ["a4", "original"]
ORIENTATIONS = ["auto", "portrait", "landscape"]


class ImageToPdfPanel(PanelBase):
    name = "imgpdf"
    title_key = "imgpdf_title"
    multi_file = True
    file_kind = "image"

    def build_params(self, parent):
        self._labeled_entry(parent, "outname", "imgpdf_outname",
                            default=t("imgpdf_default_name"))
        self._option(parent, "page_size", "imgpdf_page_size",
                     [t("imgpdf_a4"), t("imgpdf_original")], default_index=0)
        self._option(parent, "orientation", "imgpdf_orientation",
                     [t("imgpdf_auto"), t("imgpdf_portrait"), t("imgpdf_landscape")],
                     default_index=0)
        self._labeled_slider(parent, "margin", "imgpdf_margin", 0, 30, 10,
                             steps=30, fmt=int)
        self._labeled_slider(parent, "quality", "imgpdf_quality", 60, 100, 90,
                             steps=40, fmt=int)
        ctk.CTkLabel(parent, text=t("imgpdf_hint"), text_color=color("muted_text"),
                     wraplength=640, justify="left").pack(anchor="w", pady=4)

    def make_jobs(self, files, out_dir):
        name = (self.state.get("outname") or "").strip() or t("imgpdf_default_name")
        if not name.lower().endswith(".pdf"):
            name += ".pdf"
        out = resolve_conflict(out_dir / name, self.conflict_rule)
        if out is None:
            return [], [name]
        paths = [Path(f) for f in files]
        job = Job(images_to_pdf, {
            "paths": paths, "dst": out,
            "page_size": PAGE_SIZES[self.state.get("page_size", 0)],
            "orientation": ORIENTATIONS[self.state.get("orientation", 0)],
            "margin_mm": int(float(self.state.get("margin", 10))),
            "quality": int(float(self.state.get("quality", 90))),
        }, label=out.name)
        return [job], []
