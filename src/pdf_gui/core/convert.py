"""PDF 转图片：pypdfium2 逐页导出 PNG/JPG。"""

from pathlib import Path

from .render import open_document, render_page
from .types import ProgressCB, TaskResult

_SUPPORTED_FMT = {"png": "PNG", "jpg": "JPEG", "jpeg": "JPEG"}


def pdf_to_images(src, out_dir, dpi=150, fmt="png", quality=90,
                  progress_cb: ProgressCB | None = None) -> TaskResult:
    src, out_dir = Path(src), Path(out_dir)
    fmt = fmt.lower().lstrip(".")
    if fmt not in _SUPPORTED_FMT:
        return TaskResult(False, [], f"不支持的图片格式: {fmt}")
    try:
        doc = open_document(src)
        # pypdfium2 无法直接探测加密态，尝试渲染第一页失败即报加密/损坏
        if len(doc) == 0:
            return TaskResult(False, [], f"{src.name} 无页面或已加密")
        render_page(doc, 0, scale=0.1)
    except Exception as e:
        return TaskResult(False, [], f"{src.name} 已加密或无法读取: {e}")

    out_dir.mkdir(parents=True, exist_ok=True)
    scale = dpi / 72
    total = len(doc)
    outputs = []
    for i in range(total):
        img = render_page(doc, i, scale=scale)
        out = out_dir / f"{src.stem}_{i + 1:03d}.{fmt}"
        if _SUPPORTED_FMT[fmt] == "JPEG" and img.mode != "RGB":
            img = img.convert("RGB")
        img.save(out, _SUPPORTED_FMT[fmt], quality=quality)
        outputs.append(out)
        if progress_cb:
            progress_cb(i + 1, total, str(out))
    return TaskResult(True, outputs)
