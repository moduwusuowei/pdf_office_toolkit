"""core 层：PDF 处理引擎，纯函数、零 GUI 依赖。"""

from .compress import compress_pdf
from .convert import pdf_to_images
from .merge import merge_files
from .pages import parse_page_spec
from .paging_seal import (
    apply_paging_seal,
    assemble_strips,
    split_stamp_image,
    strips_for_pages,
    trim_to_content,
)
from .secure import decrypt_pdf, encrypt_pdf
from .split import parse_ranges, split_by_blank_pages, split_by_ranges, split_every_n
from .stamp import stamp_pdf
from .types import ProgressCB, TaskResult
from .watermark import add_image_watermark, add_text_watermark

__all__ = [
    "merge_files",
    "parse_ranges", "split_every_n", "split_by_ranges", "split_by_blank_pages",
    "parse_page_spec",
    "add_text_watermark", "add_image_watermark",
    "stamp_pdf",
    "apply_paging_seal", "split_stamp_image", "strips_for_pages",
    "trim_to_content", "assemble_strips",
    "encrypt_pdf", "decrypt_pdf",
    "compress_pdf",
    "pdf_to_images",
    "ProgressCB", "TaskResult",
]
