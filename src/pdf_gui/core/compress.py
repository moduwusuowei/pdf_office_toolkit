"""压缩：lossless（内容流压缩）/ rasterize（重渲染光栅化）。"""

from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from .render import open_document, render_page
from .types import CancelCB, ProgressCB, TaskResult


def compress_pdf(src, dst, *, mode="lossless", dpi=100, jpeg_quality=70,
                 progress_cb: ProgressCB | None = None,
                 cancel_cb: CancelCB | None = None) -> TaskResult:
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
        return _compress_lossless(reader, dst, progress_cb, cancel_cb)
    return _compress_rasterize(src, dst, dpi, jpeg_quality, progress_cb, cancel_cb)


def _compress_lossless(reader, dst: Path, progress_cb, cancel_cb) -> TaskResult:
    # pypdf ≥7：compress_content_streams 要求页属于 PdfWriter，先 append 再压缩
    writer = PdfWriter()
    writer.append(reader)
    for i, page in enumerate(writer.pages):
        if cancel_cb and cancel_cb():
            return TaskResult(False, [], "已取消", cancelled=True)
        page.compress_content_streams()
        if progress_cb:
            progress_cb(i + 1, len(writer.pages), str(dst))
    with open(dst, "wb") as f:
        writer.write(f)
    return TaskResult(True, [dst])


def _compress_rasterize(src: Path, dst: Path, dpi: int, quality: int,
                        progress_cb, cancel_cb) -> TaskResult:
    """逐页渲染 → JPEG 编码 → 立即写入 PDF。

    不把整本渲染图留在内存里：300 页 A4@150dpi 若全缓存约 2GB，
    逐页写入后常驻内存只有一页（约 6MB）。"""
    doc = open_document(src)
    total = len(doc)
    if total == 0:
        return TaskResult(False, [], f"{src.name} 无页面或已加密")

    scale = dpi / 72
    cancelled = False
    failed = False
    pdf = canvas.Canvas(str(dst), pageCompression=1)
    try:
        for i in range(total):
            if cancel_cb and cancel_cb():
                cancelled = True
                break
            img = render_page(doc, i, scale=scale)
            if img.mode != "RGB":
                img = img.convert("RGB")
            page_w_pt = img.width * 72 / dpi
            page_h_pt = img.height * 72 / dpi
            pdf.setPageSize((page_w_pt, page_h_pt))
            buf = BytesIO()
            img.save(buf, "JPEG", quality=quality, optimize=True)
            buf.seek(0)
            pdf.drawImage(ImageReader(buf), 0, 0,
                          width=page_w_pt, height=page_h_pt)
            pdf.showPage()
            img.close()
            if progress_cb:
                progress_cb(i + 1, total, str(dst))
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
