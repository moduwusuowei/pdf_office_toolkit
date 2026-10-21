"""骑缝章面板：后台生成预览，显示「拼合示意 + 首末页」。"""

import queue
import threading
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image
from pypdf import PdfReader

from ...core import (
    apply_paging_seal,
    assemble_strips,
    split_stamp_image,
    strips_for_pages,
    trim_to_content,
)
from ...workers import Job, resolve_conflict
from ..i18n import t
from ..theme import color
from ..widgets.file_queue import TEMP_DIR
from ..widgets.preview import PagePreview
from .base import PanelBase

PREVIEW_WIDTH = 300          # 两页并排；缩放后整页可在一屏内看完
ASSEMBLY_MAX_SIZE = (320, 130)


class PagingSealPanel(PanelBase):
    name = "seal"
    title_key = "seal_title"
    multi_file = False

    def build_params(self, parent):
        self._file_picker(parent, "png", "seal_png", "choose_image",
                          [("PNG", "*.png")])
        self._labeled_slider(parent, "height", "seal_height", 0.1, 0.9, 0.4,
                             steps=16)
        self._labeled_slider(parent, "ycenter", "seal_ycenter", 0.1, 0.9, 0.5,
                             steps=16)
        self._labeled_slider(parent, "maxstrips", "seal_maxstrips", 5, 30, 20,
                             steps=25, fmt=int)
        self.preview_btn = ctk.CTkButton(parent, text=t("seal_preview_btn"),
                                         command=self._preview)
        self.preview_btn.pack(anchor="w", pady=4)
        ctk.CTkLabel(parent, text=t("seal_hint"), text_color=color("muted_text"),
                     wraplength=640, justify="left").pack(anchor="w", pady=2)

        caption = ctk.CTkFrame(parent, fg_color="transparent")
        caption.pack(fill="x", pady=(10, 0))
        ctk.CTkLabel(caption, text=t("seal_assembled_caption"),
                     text_color=color("muted_text")).pack(side="left")
        self.assembly_info = ctk.CTkLabel(caption, text="",
                                          text_color=color("muted_text"))
        self.assembly_info.pack(side="left", padx=(10, 0))
        self.assembly_label = ctk.CTkLabel(parent, text="")
        self.assembly_label.pack(anchor="w", pady=(2, 8))

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=6)
        first = ctk.CTkFrame(row, fg_color="transparent")
        first.pack(side="left", padx=4)
        ctk.CTkLabel(first, text=t("seal_page_first"),
                     text_color=color("muted_text")).pack(anchor="w")
        self.preview_first = PagePreview(first, width=PREVIEW_WIDTH)
        self.preview_first.pack()
        last = ctk.CTkFrame(row, fg_color="transparent")
        last.pack(side="left", padx=4)
        ctk.CTkLabel(last, text=t("seal_page_last"),
                     text_color=color("muted_text")).pack(anchor="w")
        self.preview_last = PagePreview(last, width=PREVIEW_WIDTH)
        self.preview_last.pack()

    def _current_file(self):
        files = self.file_queue.paths()
        return files[0] if files else None

    def _params(self) -> dict:
        return {
            "seal_height_ratio": float(self.state.get("height", 0.4)),
            "y_center_ratio": float(self.state.get("ycenter", 0.5)),
            "max_strips": int(float(self.state.get("maxstrips", 20))),
        }

    # ---- 预览 ----
    def _preview(self) -> None:
        if getattr(self, "_previewing", False):
            return
        f = self._current_file()
        png = (self.state.get("png") or "").strip()
        if not (f and png):
            messagebox.showwarning(t("seal_title"), t("no_files"))
            return
        params = self._params()
        try:
            img = trim_to_content(Image.open(png).convert("RGBA"))
            total = len(PdfReader(f).pages)
        except Exception as e:
            messagebox.showerror(t("seal_title"), str(e))
            return

        # 拼合示意很轻，直接算：所有竖条并排 = 完整印章
        n_strips, per = strips_for_pages(total, params["max_strips"])
        self._show_assembly(assemble_strips(split_stamp_image(img, n_strips)))
        self.assembly_info.configure(
            text=t("seal_assembly_info", strips=n_strips, per=per, total=total))

        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        tmp = TEMP_DIR / "paging_seal_preview.pdf"
        self._previewing = True
        self._preview_q: "queue.Queue[object]" = queue.Queue()
        self.preview_btn.configure(state="disabled", text=t("seal_preview_busy"))
        threading.Thread(target=self._run_preview, args=(f, tmp, png, params),
                         daemon=True).start()
        self.after(80, self._poll_preview)

    def _run_preview(self, src, tmp, png, params) -> None:
        try:
            result = apply_paging_seal(src, tmp, png, **params)
        except Exception as e:      # 线程里兜底，避免预览把程序带崩
            result = e
        self._preview_q.put(result)

    def _poll_preview(self) -> None:
        if not self.winfo_exists():
            return
        try:
            result = self._preview_q.get_nowait()
        except queue.Empty:
            self.after(80, self._poll_preview)
            return
        self._previewing = False
        self.preview_btn.configure(state="normal", text=t("seal_preview_btn"))
        if isinstance(result, Exception):
            messagebox.showerror(t("seal_title"), str(result))
            return
        if not result.ok:
            messagebox.showerror(t("seal_title"), result.error)
            return
        tmp = TEMP_DIR / "paging_seal_preview.pdf"
        total = len(PdfReader(tmp).pages)
        self.preview_first.load_pdf(tmp, page=0)
        self.preview_last.load_pdf(tmp, page=total - 1)

    def _show_assembly(self, img: Image.Image) -> None:
        target_w, target_h = ASSEMBLY_MAX_SIZE
        scale = min(target_w / img.width, target_h / img.height, 1.0)
        size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
        shown = img.resize(size, Image.Resampling.LANCZOS)
        bg = Image.new("RGB", size, "white")   # 白底便于在明暗主题下都看清
        bg.paste(shown, (0, 0), shown)
        self._assembly_photo = ctk.CTkImage(
            light_image=bg, dark_image=bg, size=bg.size)
        self.assembly_label.configure(image=self._assembly_photo, text="")

    # ---- 任务 ----
    def make_jobs(self, files, out_dir):
        png = (self.state.get("png") or "").strip()
        if not png:
            raise ValueError(t("seal_png"))
        rule = self.conflict_rule
        jobs, skipped = [], []
        for f in files:
            f = Path(f)
            out = resolve_conflict(out_dir / f.name, rule)
            if out is None:
                skipped.append(f.name)
                continue
            jobs.append(Job(apply_paging_seal, {
                "src": f, "dst": out, "stamp_png": png, **self._params(),
            }, label=f.name))
        return jobs, skipped
