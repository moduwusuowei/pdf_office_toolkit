"""合并多个 PDF。"""

from pathlib import Path

from pypdf import PdfReader, PdfWriter

from .types import ProgressCB, TaskResult


def merge_files(paths, output, progress_cb: ProgressCB | None = None) -> TaskResult:
    paths = [Path(p) for p in paths]
    output = Path(output)
    writer = PdfWriter()
    total = len(paths)
    for i, p in enumerate(paths):
        try:
            reader = PdfReader(p)
            if reader.is_encrypted:
                return TaskResult(False, [], f"{p.name} 已加密，请先解密")
            writer.append(reader)
        except Exception as exc:
            return TaskResult(False, [], f"无法读取 {p.name}: {exc}")
        if progress_cb:
            progress_cb(i + 1, total, str(p))
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "wb") as f:
        writer.write(f)
    return TaskResult(True, [output])
