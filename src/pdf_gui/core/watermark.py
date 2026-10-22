"""水印：文字（平铺/单页定位）与图片。"""

from pathlib import Path

from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

from .overlay import append_with_overlay, make_overlay
from .pages import parse_page_spec
from .types import CancelCB, ProgressCB, TaskResult

_font_registered = False


def _pick_font(text: str) -> str:
    """ASCII 用 Helvetica；含中文时注册 CID 字体 STSong-Light。"""
    global _font_registered
    if any(ord(ch) > 127 for ch in text):
        if not _font_registered:
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            _font_registered = True
        return "STSong-Light"
    return "Helvetica"


def _draw_text_overlay(page_w, page_h, text, *, opacity, angle, font_size, mode):
    def draw(c):
        c.saveState()
        c.setFont(_pick_font(text), font_size)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.setFillAlpha(opacity)
        if mode == "tile":
            for r_i in range(4):
                for c_i in range(2):
                    x = page_w * (c_i + 0.5) / 2
                    y = page_h * (r_i + 0.25) / 4
                    c.saveState()
                    c.translate(x, y)
                    c.rotate(angle)
                    c.drawCentredString(0, 0, text)
                    c.restoreState()
        else:  # single
            c.saveState()
            c.translate(page_w / 2, page_h / 2)
            c.rotate(angle)
            c.drawCentredString(0, 0, text)
            c.restoreState()
        c.restoreState()

    return make_overlay(page_w, page_h, draw)


def _apply(src, dst, overlay_for_page, pages,
           progress_cb: ProgressCB | None = None,
           cancel_cb: CancelCB | None = None) -> TaskResult:
    """通用套用流程：只对 pages 列表内的页叠 overlay。"""
    src, dst = Path(src), Path(dst)
    try:
        reader = PdfReader(src)
        if reader.is_encrypted:
            return TaskResult(False, [], f"{src.name} 已加密，请先解密")
        targets = parse_page_spec(pages, len(reader.pages))
    except ValueError as e:
        return TaskResult(False, [], str(e))
    target_set = set(targets)
    writer = PdfWriter()
    for i, page in enumerate(reader.pages):
        if cancel_cb and cancel_cb():
            return TaskResult(False, [], "已取消", cancelled=True)
        if i in target_set:
            w, h = float(page.mediabox.width), float(page.mediabox.height)
            append_with_overlay(page, overlay_for_page(w, h), writer)
        else:
            writer.add_page(page)
        if progress_cb:
            progress_cb(i + 1, len(reader.pages), str(dst))
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "wb") as f:
        writer.write(f)
    return TaskResult(True, [dst])


def add_text_watermark(src, dst, text, *, opacity=0.15, angle=45, font_size=36,
                       mode="tile", pages="all",
                       progress_cb: ProgressCB | None = None,
                       cancel_cb: CancelCB | None = None) -> TaskResult:
    if not text:
        return TaskResult(False, [], "水印文字为空")

    def overlay_for_page(w, h):
        return _draw_text_overlay(w, h, text, opacity=opacity, angle=angle,
                                  font_size=font_size, mode=mode)

    return _apply(src, dst, overlay_for_page, pages, progress_cb, cancel_cb)


_X = {"left": 0.15, "center": 0.5, "right": 0.85}
_Y = {"top": 0.85, "middle": 0.5, "bottom": 0.15}


def _parse_pos(pos: str) -> tuple[float, float]:
    """九宫格位置 "top-left"/"center"/"bottom-right" → (x_ratio, y_ratio)。"""
    parts = pos.strip().lower().split("-")
    x_key = next((k for k in _X if k in parts), "center")
    y_key = next((k for k in _Y if k in parts), "middle")
    if len(parts) > 2 or pos.strip().lower() not in (
        "top-left", "top", "top-right", "left", "center", "right",
        "bottom-left", "bottom", "bottom-right",
    ):
        raise ValueError(f"无效位置: {pos}")
    return _X[x_key], _Y[y_key]


def _scaled_alpha(img: Image.Image, opacity: float) -> Image.Image:
    if opacity >= 1.0:
        return img
    out = img.copy().convert("RGBA")
    alpha = out.getchannel("A").point(lambda a: int(a * opacity))
    out.putalpha(alpha)
    return out


def add_image_watermark(src, dst, image_path, *, opacity=0.3, size_ratio=0.3,
                        pos="center", pages="all",
                        progress_cb: ProgressCB | None = None,
                        cancel_cb: CancelCB | None = None) -> TaskResult:
    try:
        x_ratio, y_ratio = _parse_pos(pos)
        img = _scaled_alpha(Image.open(image_path), opacity)
    except ValueError as e:
        return TaskResult(False, [], str(e))
    except Exception as e:
        return TaskResult(False, [], f"水印图片无法读取: {e}")

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

    return _apply(src, dst, overlay_for_page, pages, progress_cb, cancel_cb)
