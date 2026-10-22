"""图片转 PDF：多张图片按给定顺序合成一份 PDF。"""

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from .types import CancelCB, ProgressCB, TaskResult

A4 = (595.2756, 841.8898)          # 210 × 297 mm，单位 pt
MM = 72 / 25.4
SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tif", ".tiff"}
DEFAULT_DPI = 96                    # 无 DPI 元数据时，“原始尺寸”按此换算


def _to_rgb(im: Image.Image) -> Image.Image:
    """透明图铺白底，其余统一转 RGB（PDF 里可直接编码）。"""
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.getchannel("A"))
        return bg
    return im.convert("RGB")


def _image_dpi(im: Image.Image) -> float:
    try:
        dpi = im.info.get("dpi")
        value = float(dpi[0]) if isinstance(dpi, (tuple, list)) else float(dpi)
        return value if value > 1 else DEFAULT_DPI
    except (TypeError, ValueError, IndexError):
        return DEFAULT_DPI


def _page_size(size_px, page_size: str, orientation: str, dpi: float):
    w_px, h_px = size_px
    if page_size == "a4":
        width, height = A4
        landscape = orientation == "landscape" or (
            orientation == "auto" and w_px > h_px)
        return (height, width) if landscape else (width, height)
    width, height = w_px * 72 / dpi, h_px * 72 / dpi
    if orientation == "landscape" and height > width:
        width, height = height, width
    elif orientation == "portrait" and width > height:
        width, height = height, width
    return width, height


def images_to_pdf(paths, dst, *, page_size="a4", orientation="auto",
                  margin_mm=10, quality=90,
                  progress_cb: ProgressCB | None = None,
                  cancel_cb: CancelCB | None = None) -> TaskResult:
    """把 paths 依次排版成一份 PDF；所有图片等比缩放、居中、留白边。

    page_size: a4 | original；orientation: auto | portrait | landscape。
    """
    paths = [Path(p) for p in paths]
    dst = Path(dst)
    if not paths:
        return TaskResult(False, [], "没有可转换的图片")
    if page_size not in ("a4", "original"):
        return TaskResult(False, [], f"未知页面尺寸: {page_size}")
    if orientation not in ("auto", "portrait", "landscape"):
        return TaskResult(False, [], f"未知页面方向: {orientation}")

    margin = max(0.0, float(margin_mm)) * MM
    total = len(paths)
    dst.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(dst), pageCompression=1)
    cancelled = failed = False
    try:
        for i, path in enumerate(paths):
            if cancel_cb and cancel_cb():
                cancelled = True
                break
            try:
                with Image.open(path) as im:
                    needs_reencode = (
                        im.format != "JPEG" or im.mode not in ("RGB", "L")
                        or im.getexif().get(0x0112, 1) != 1)
                    dpi = _image_dpi(im)
                    if needs_reencode:
                        im = ImageOps.exif_transpose(im)
                        im = _to_rgb(im)
                        size_px = im.size
                        buf = BytesIO()
                        im.save(buf, "JPEG", quality=quality, optimize=True)
                        buf.seek(0)
                        reader = ImageReader(buf)
                    else:
                        size_px = im.size
                        buf = None
                        reader = ImageReader(str(path))
            except Exception as e:
                failed = True
                raise ValueError(f"无法读取 {path.name}: {e}") from e

            page_w, page_h = _page_size(size_px, page_size, orientation, dpi)
            avail_w = max(1.0, page_w - 2 * margin)
            avail_h = max(1.0, page_h - 2 * margin)
            scale = min(avail_w / size_px[0], avail_h / size_px[1])
            draw_w, draw_h = size_px[0] * scale, size_px[1] * scale
            x = (page_w - draw_w) / 2
            y = (page_h - draw_h) / 2

            pdf.setPageSize((page_w, page_h))
            pdf.drawImage(reader, x, y, draw_w, draw_h)
            pdf.showPage()
            if progress_cb:
                progress_cb(i + 1, total, path.name)
    except Exception:
        failed = True
        raise
    finally:
        pdf.save()
        if failed or cancelled:
            dst.unlink(missing_ok=True)
    if cancelled:
        return TaskResult(False, [], "已取消", cancelled=True)
    return TaskResult(True, [dst])
