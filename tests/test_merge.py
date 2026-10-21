
from pypdf import PdfReader
from tests.conftest import make_pdf

from pdf_gui.core.merge import merge_files


def test_merge_two_files(tmp_path):
    a = make_pdf(tmp_path / "a.pdf", pages=3)
    b = make_pdf(tmp_path / "b.pdf", pages=2)
    out = tmp_path / "merged.pdf"
    result = merge_files([a, b], out)
    assert result.ok, result.error
    assert len(PdfReader(out).pages) == 5


def test_merge_preserves_order(tmp_path):
    a = make_pdf(tmp_path / "a.pdf", pages=1)
    b = make_pdf(tmp_path / "b.pdf", pages=1)
    out = tmp_path / "merged.pdf"
    merge_files([b, a], out)
    reader = PdfReader(out)
    # b 在前：第 1 页文本来自 b.pdf 的 "page 1"
    assert "page 1" in reader.pages[0].extract_text()


def test_merge_rejects_encrypted(tmp_path, encrypted_pdf):
    plain = make_pdf(tmp_path / "plain2.pdf", pages=1)
    out = tmp_path / "merged.pdf"
    result = merge_files([plain, encrypted_pdf], out)
    assert not result.ok
    assert "加密" in result.error


def test_merge_reports_progress(tmp_path):
    a = make_pdf(tmp_path / "a.pdf", pages=1)
    b = make_pdf(tmp_path / "b.pdf", pages=1)
    calls = []
    merge_files([a, b], tmp_path / "m.pdf", progress_cb=lambda d, t, m: calls.append((d, t)))
    assert calls == [(1, 2), (2, 2)]
