"""加密与解密：AES-256。"""

from pathlib import Path

from pypdf import PdfReader, PdfWriter

from .types import ProgressCB, TaskResult


def _read_plain(src: Path):
    reader = PdfReader(src)
    if reader.is_encrypted:
        raise ValueError(f"{src.name} 已加密")
    return reader


def encrypt_pdf(src, dst, user_password, owner_password=None,
                progress_cb: ProgressCB | None = None) -> TaskResult:
    src, dst = Path(src), Path(dst)
    if not user_password:
        return TaskResult(False, [], "密码为空")
    try:
        reader = _read_plain(src)
    except ValueError as e:
        return TaskResult(False, [], str(e))
    except Exception as e:
        return TaskResult(False, [], f"无法读取 {src.name}: {e}")
    writer = PdfWriter()
    for i, page in enumerate(reader.pages):
        writer.add_page(page)
        if progress_cb:
            progress_cb(i + 1, len(reader.pages), str(dst))
    writer.encrypt(user_password=user_password,
                  owner_password=owner_password or user_password,
                  algorithm="AES-256")
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "wb") as f:
        writer.write(f)
    return TaskResult(True, [dst])


def decrypt_pdf(src, dst, password,
                progress_cb: ProgressCB | None = None) -> TaskResult:
    src, dst = Path(src), Path(dst)
    try:
        reader = PdfReader(src)
        if reader.is_encrypted:
            # decrypt() 成功后 is_encrypted 仍为 True，需按返回值判断
            if not reader.decrypt(password):
                return TaskResult(False, [], f"{src.name} 密码错误或解密失败")
    except Exception as e:
        return TaskResult(False, [], f"{src.name} 密码错误或无法读取: {e}")
    writer = PdfWriter()
    for i, page in enumerate(reader.pages):
        writer.add_page(page)
        if progress_cb:
            progress_cb(i + 1, len(reader.pages), str(dst))
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "wb") as f:
        writer.write(f)
    return TaskResult(True, [dst])
