"""盖章：印章 PNG 叠加到指定页的指定比例坐标。"""


from PIL import Image
from reportlab.lib.utils import ImageReader

from .overlay import make_overlay
from .types import ProgressCB, TaskResult
from .watermark import _apply, _scaled_alpha


def stamp_pdf(src, dst, stamp_png, *, pages="all", x_ratio=0.8, y_ratio=0.15,
              size_ratio=0.25, opacity=1.0,
              progress_cb: ProgressCB | None = None) -> TaskResult:
    """stamp 以 (x_ratio, y_ratio) 为中心、宽 size_ratio*页宽 叠加。"""
    try:
        img = _scaled_alpha(Image.open(stamp_png).convert("RGBA"), opacity)
    except Exception as e:
        return TaskResult(False, [], f"印章图片无法读取: {e}")

    def overlay_for_page(w, h):
        def draw(c):
            c.saveState()
            iw = size_ratio * w
            ih = iw * img.height / img.width
            x = x_ratio * w - iw / 2
            y = y_ratio * h - ih / 2
            c.drawImage(ImageReader(img), x, y, iw, ih, mask="auto")
            c.restoreState()

        return make_overlay(w, h, draw)

    return _apply(src, dst, overlay_for_page, pages, progress_cb)
