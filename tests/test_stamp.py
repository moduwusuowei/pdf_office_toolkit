from pypdf import PdfReader

from pdf_gui.core.stamp import stamp_pdf


def test_stamp_all_pages(tmp_path, sample_pdf, seal_png):
    out = tmp_path / "stamped.pdf"
    result = stamp_pdf(sample_pdf, out, seal_png)
    assert result.ok, result.error
    for page in PdfReader(out).pages:
        assert len(page.images) == 1


def test_stamp_last_page_only(tmp_path, sample_pdf, seal_png):
    out = tmp_path / "stamped.pdf"
    stamp_pdf(sample_pdf, out, seal_png, pages="last")
    pages = PdfReader(out).pages
    assert len(pages[0].images) == 0
    assert len(pages[2].images) == 1


def test_stamp_partial_opacity(tmp_path, sample_pdf, seal_png):
    out = tmp_path / "stamped.pdf"
    result = stamp_pdf(sample_pdf, out, seal_png, opacity=0.5)
    assert result.ok
    assert len(PdfReader(out).pages[0].images) == 1


def test_stamp_rejects_encrypted(tmp_path, encrypted_pdf, seal_png):
    result = stamp_pdf(encrypted_pdf, tmp_path / "x.pdf", seal_png)
    assert not result.ok and "加密" in result.error


def test_stamp_invalid_image(tmp_path, sample_pdf):
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"junk")
    result = stamp_pdf(sample_pdf, tmp_path / "x.pdf", bad)
    assert not result.ok
