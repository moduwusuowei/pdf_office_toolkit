"""烟囱测试：core 包出口完整可用。"""

from pdf_gui.core import (  # noqa: F401
    compress_pdf,
    decrypt_pdf,
    encrypt_pdf,
    merge_files,
    parse_page_spec,
    parse_ranges,
    pdf_to_images,
    split_by_blank_pages,
    split_by_ranges,
    split_every_n,
)


def test_imports_resolve():
    import pdf_gui.core as core

    assert callable(core.merge_files)
