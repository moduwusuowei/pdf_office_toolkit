"""拆分：范围解析、每 N 页、自定义范围、按空白页。"""

from pathlib import Path

from pypdf import PdfReader, PdfWriter

from .types import ProgressCB, TaskResult


def parse_ranges(spec: str, total: int) -> list[range]:
    """解析 "1-3,5,8-10" 为 1 起页码 range 列表；非法输入抛 ValueError。"""
    spec = spec.replace(" ", "").replace("，", ",")
    if not spec:
        raise ValueError("范围为空")
    result: list[range] = []
    for part in spec.split(","):
        try:
            if "-" in part:
                a, b = part.split("-", 1)
                start, end = int(a), int(b)
            else:
                start = end = int(part)
        except ValueError:
            raise ValueError(f"无效页码: {part}") from None
        if start < 1 or end > total:
            raise ValueError(f"页码超出范围: {part}（共 {total} 页）")
        if start > end:
            raise ValueError(f"起页大于止页: {part}")
        result.append(range(start, end + 1))
    return result


def _write_pages(src, out: Path, indices) -> Path:
    reader = PdfReader(src)
    writer = PdfWriter()
    for i in indices:
        writer.add_page(reader.pages[i])
    with open(out, "wb") as f:
        writer.write(f)
    return out


def _check_readable(src: Path) -> None:
    reader = PdfReader(src)
    if reader.is_encrypted:
        raise _EncryptedError(src.name)


def split_every_n(src, n: int, out_dir, progress_cb: ProgressCB | None = None) -> TaskResult:
    src, out_dir = Path(src), Path(out_dir)
    if n < 1:
        raise ValueError("每份页数必须 ≥ 1")
    try:
        _check_readable(src)
    except _EncryptedError as e:
        return TaskResult(False, [], f"{e} 已加密，请先解密")
    total = len(PdfReader(src).pages)
    out_dir.mkdir(parents=True, exist_ok=True)
    chunks = list(range(0, total, n))
    outputs = []
    for chunk_i, start in enumerate(chunks):
        out = out_dir / f"{src.stem}_{chunk_i + 1:02d}.pdf"
        outputs.append(_write_pages(src, out, range(start, min(start + n, total))))
        if progress_cb:
            progress_cb(chunk_i + 1, len(chunks), str(out))
    return TaskResult(True, outputs)


def split_by_ranges(src, spec: str, out_dir, progress_cb: ProgressCB | None = None) -> TaskResult:
    src, out_dir = Path(src), Path(out_dir)
    try:
        _check_readable(src)
    except _EncryptedError as e:
        return TaskResult(False, [], f"{e} 已加密，请先解密")
    total = len(PdfReader(src).pages)
    try:
        ranges = parse_ranges(spec, total)
    except ValueError as e:
        return TaskResult(False, [], str(e))
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for i, r in enumerate(ranges):
        out = out_dir / f"{src.stem}_{i + 1:02d}.pdf"
        outputs.append(_write_pages(src, out, [p - 1 for p in r]))
        if progress_cb:
            progress_cb(i + 1, len(ranges), str(out))
    return TaskResult(True, outputs)


def split_by_blank_pages(src, out_dir, progress_cb: ProgressCB | None = None) -> TaskResult:
    from .render import open_document, page_is_blank, render_page

    src, out_dir = Path(src), Path(out_dir)
    try:
        _check_readable(src)
    except _EncryptedError as e:
        return TaskResult(False, [], f"{e} 已加密，请先解密")
    doc = open_document(src)
    total = len(doc)
    blank = {i for i in range(total) if page_is_blank(render_page(doc, i, scale=0.5))}
    segments: list[list[int]] = []
    current: list[int] = []
    for i in range(total):
        if i in blank:
            if current:
                segments.append(current)
            current = []
        else:
            current.append(i)
    if current:
        segments.append(current)
    if not segments:  # 全空白：整份输出
        segments = [list(range(total))]
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for seg_i, seg in enumerate(segments):
        out = out_dir / f"{src.stem}_{seg_i + 1:02d}.pdf"
        outputs.append(_write_pages(src, out, seg))
        if progress_cb:
            progress_cb(seg_i + 1, len(segments), str(out))
    return TaskResult(True, outputs)


class _EncryptedError(Exception):
    pass
