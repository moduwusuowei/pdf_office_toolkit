"""页面预览：渲染 PDF 页为图像，叠加印章，点击回报 (x_ratio, y_ratio)。

y_ratio 用 PDF 语义（0=页底，1=页顶），点击时做屏幕→PDF 翻转。"""

import customtkinter as ctk

from ...core.render import open_document, render_page

PREVIEW_WIDTH = 460


class PagePreview(ctk.CTkFrame):
    def __init__(self, master, *, on_place=None, width: int = PREVIEW_WIDTH):
        super().__init__(master)
        self.on_place = on_place
        self.preview_width = width
        self._page_img = None    # PIL 渲染页（RGBA）
        self._stamp = None       # PIL 印章原图
        self._stamp_state = {}   # {size, opacity, x, y}
        self.label = ctk.CTkLabel(self, text="")
        self.label.pack()
        if on_place:
            self.label.bind("<Button-1>", self._on_click)

    def load_pdf(self, path, page: int = 0) -> None:
        """渲染第 page 页（0 起）并显示。"""
        doc = open_document(path)
        w, h = doc[page].get_size()
        self._page_img = render_page(doc, page, scale=self.preview_width / w)
        self._page_img = self._page_img.convert("RGBA")
        self._render()

    def set_stamp(self, png_path, size: float, opacity: float,
                  x: float, y: float) -> None:
        """设置/更新印章叠加（size=占页宽比例，x/y=PDF 语义比例坐标）。"""
        from PIL import Image
        self._stamp = Image.open(png_path).convert("RGBA")
        self._stamp_state = {"size": size, "opacity": opacity, "x": x, "y": y}
        self._render()

    def _render(self) -> None:
        if self._page_img is None:
            return
        out = self._page_img.copy()
        if self._stamp is not None and self._stamp_state:
            st = self._stamp_state
            iw = st["size"] * out.width
            ih = iw * self._stamp.height / self._stamp.width
            stamp = self._stamp.resize((max(1, int(iw)), max(1, int(ih))))
            if st["opacity"] < 1.0:
                alpha = stamp.getchannel("A").point(
                    lambda a: int(a * st["opacity"]))
                stamp.putalpha(alpha)
            cx = st["x"] * out.width
            cy = (1 - st["y"]) * out.height   # PDF 底部原点 → 屏幕顶部原点
            out.alpha_composite(
                stamp, (int(cx - iw / 2), int(cy - ih / 2)))
        img = out.convert("RGB")
        self._photo = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        self.label.configure(image=self._photo, text="")

    def _on_click(self, event) -> None:
        if self._page_img is None or not self.on_place:
            return
        w = self.label.winfo_width() or self._page_img.width
        h = self.label.winfo_height() or self._page_img.height
        x = min(max(event.x / w, 0.0), 1.0)
        y = min(max(1 - event.y / h, 0.0), 1.0)
        self.on_place(x, y)
