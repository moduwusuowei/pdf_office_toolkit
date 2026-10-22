"""骑缝章：印章切条、多页分条规则、套用。"""

from math import ceil
from pathlib import Path

from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.lib.utils import ImageReader

from .overlay import append_with_overlay, make_overlay
from .types import CancelCB, ProgressCB, TaskResult


def strips_for_pages(pages: int, max_strips: int = 20) -> tuple[int, int]:
    """返回 (条数, 每条页数)。页数 ≤ max_strips 时一页一条。"""
    if pages <= 0:
        raise ValueError("页数必须 > 0")
    if pages <= max_strips:
        return pages, 1
    per = ceil(pages / max_strips)
    n = ceil(pages / per)
    return n, per


def trim_to_content(img: Image.Image) -> Image.Image:
    """裁掉四周全透明边（印章 PNG 常带大片留白，不裁会导致首末页分到空条）。"""
    box = img.getchannel("A").getbbox()
    if box is None:
        raise ValueError("印章图片为空（全透明）")
    return img.crop(box)


def split_stamp_image(img: Image.Image, n: int):
    """横向切 n 列竖条，返回 [(条图片, 条左在原图中的 x 偏移)]，总宽守恒。"""
    if n < 1:
        raise ValueError("条数必须 ≥ 1")
    w = img.width
    result = []
    for i in range(n):
        left = round(w * i / n)
        right = round(w * (i + 1) / n)
        result.append((img.crop((left, 0, right, img.height)), left))
    return result


def assemble_strips(strips) -> Image.Image:
    """把竖条按原顺序并排拼回完整印章（预览「叠放拼合」效果）。"""
    if not strips:
        raise ValueError("没有可拼合的条")
    images = [strip for strip, _left in strips]
    height = images[0].height
    width = sum(im.width for im in images)
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    x = 0
    for im in images:
        canvas.alpha_composite(im, (x, 0))
        x += im.width
    return canvas


def apply_paging_seal(src, dst, stamp_png, *, seal_height_ratio=0.4,
                      y_center_ratio=0.5, max_strips=20,
                      progress_cb: ProgressCB | None = None,
                      cancel_cb: CancelCB | None = None) -> TaskResult:
    """骑缝章：印章裁透明边后横切 N 条，每页右边缘同一位置画对应条。"""
    src, dst = Path(src), Path(dst)
    try:
        reader = PdfReader(src)
        if reader.is_encrypted:
            return TaskResult(False, [], f"{src.name} 已加密，请先解密")
        img = Image.open(stamp_png).convert("RGBA")
    except Exception as e:
        return TaskResult(False, [], f"印章图片无法读取: {e}")
    try:
        img = trim_to_content(img)
    except ValueError as e:
        return TaskResult(False, [], str(e))

    total = len(reader.pages)
    n_strips, pages_per_strip = strips_for_pages(total, max_strips)
    strips = split_stamp_image(img, n_strips)

    writer = PdfWriter()
    for i, page in enumerate(reader.pages):
        if cancel_cb and cancel_cb():
            return TaskResult(False, [], "已取消", cancelled=True)
        # 旋转页先把 /Rotate 烘焙进内容，否则"右边缘"会画到视觉上的底边
        try:
            rotation = int(page.get("/Rotate", 0) or 0) % 360
        except Exception:
            rotation = 0
        if rotation:
            page.transfer_rotation_to_content()
        w, h = float(page.mediabox.width), float(page.mediabox.height)
        strip_idx = min(i // pages_per_strip, n_strips - 1)
        strip, _left = strips[strip_idx]
        seal_h = seal_height_ratio * h
        seal_w = seal_h * img.width / img.height     # 完整印章宽
        strip_w = seal_w * strip.width / img.width   # 该条占完整印章宽的比例
        # 所有条贴右边缘、同一垂直位置：页序错开时窄条横向拼合还原完整印章
        x = w - strip_w
        y_top = h * y_center_ratio - seal_h / 2

        def draw(c, _img=strip, _x=x, _y=y_top, _w=strip_w, _h=seal_h):
            c.saveState()
            c.drawImage(ImageReader(_img), _x, _y, _w, _h, mask="auto")
            c.restoreState()

        append_with_overlay(page, make_overlay(w, h, draw), writer)
        if progress_cb:
            progress_cb(i + 1, total, str(dst))

    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "wb") as f:
        writer.write(f)
    return TaskResult(True, [dst])
