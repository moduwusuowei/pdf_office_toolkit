from pypdf import PdfReader
from tests.conftest import make_pdf

from pdf_gui.core.compress import compress_pdf


def test_lossless_keeps_pages(tmp_path, sample_pdf):
    out = tmp_path / "small.pdf"
    result = compress_pdf(sample_pdf, out)
    assert result.ok, result.error
    assert len(PdfReader(out).pages) == 3


def test_rasterize_reduces_noisy_pdf(tmp_path):
    src = make_pdf(tmp_path / "big.pdf", pages=3, noisy_image=True)
    out = tmp_path / "small.pdf"
    result = compress_pdf(src, out, mode="rasterize", dpi=72, jpeg_quality=50)
    assert result.ok, result.error
    assert len(PdfReader(out).pages) == 3
    assert out.stat().st_size < src.stat().st_size


def test_invalid_mode_rejected(tmp_path, sample_pdf):
    result = compress_pdf(sample_pdf, tmp_path / "x.pdf", mode="magic")
    assert not result.ok


def test_compress_rejects_encrypted(tmp_path, encrypted_pdf):
    result = compress_pdf(encrypted_pdf, tmp_path / "x.pdf")
    assert not result.ok and "加密" in result.error


def test_rasterize_honours_cancel(tmp_path):
    src = make_pdf(tmp_path / "big.pdf", pages=5, noisy_image=True)
    out = tmp_path / "small.pdf"
    result = compress_pdf(src, out, mode="rasterize", dpi=72,
                          cancel_cb=lambda: True)
    assert not result.ok and result.cancelled
    assert not out.exists()          # 半成品不留在输出目录


def test_lossless_honours_cancel(tmp_path, sample_pdf):
    out = tmp_path / "small.pdf"
    result = compress_pdf(sample_pdf, out, cancel_cb=lambda: True)
    assert not result.ok and result.cancelled
    assert not out.exists()
