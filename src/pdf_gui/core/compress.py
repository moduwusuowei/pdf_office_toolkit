"""压缩：lossless（内容流压缩）/ rasterize（重渲染光栅化）。"""

from pathlib import Path

from pypdf import PdfReader, PdfWriter

from .render import open_document, render_page
from .types import ProgressCB, TaskResult


def compress_pdf(src, dst, *, mode="lossless", dpi=100, jpeg_quality=70,
                 progress_cb: ProgressCB | None = None) -> TaskResult:
    """mode=lossless 保结构、压缩内容流；mode=rasterize 重渲染、可能丢文本。"""
    src, dst = Path(src), Path(dst)
    if mode not in ("lossless", "rasterize"):
        return TaskResult(False, [], f"未知压缩模式: {mode}")
    try:
        reader = PdfReader(src)
        if reader.is_encrypted:
            return TaskResult(False, [], f"{src.name} 已加密，请先解密")
    except Exception as e:
        return TaskResult(False, [], f"无法读取 {src.name}: {e}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    if mode == "lossless":
        return _compress_lossless(reader, dst, progress_cb)
    return _compress_rasterize(src, dst, dpi, jpeg_quality, progress_cb)


def _compress_lossless(reader, dst: Path, progress_cb) -> TaskResult:
    # pypdf ≥7：compress_content_streams 要求页属于 PdfWriter，先 append 再压缩
    writer = PdfWriter()
    writer.append(reader)
    for i, page in enumerate(writer.pages):
        page.compress_content_streams()
        if progress_cb:
            progress_cb(i + 1, len(writer.pages), str(dst))
    with open(dst, "wb") as f:
        writer.write(f)
    return TaskResult(True, [dst])


def _compress_rasterize(src: Path, dst: Path, dpi: int, quality: int, progress_cb) -> TaskResult:
    doc = open_document(src)
    scale = dpi / 72
    total = len(doc)
    images = []
    for i in range(total):
        img = render_page(doc, i, scale=scale)
        if img.mode != "RGB":
            img = img.convert("RGB")
        images.append(img)
        if progress_cb:
            progress_cb(i + 1, total, str(dst))
    images[0].save(dst, "PDF", save_all=True, append_images=images[1:], resolution=dpi)
    return TaskResult(True, [dst])
