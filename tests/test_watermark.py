from pypdf import PdfReader

from pdf_gui.core.watermark import add_image_watermark, add_text_watermark


def test_text_watermark_appears(tmp_path, sample_pdf):
    out = tmp_path / "wm.pdf"
    result = add_text_watermark(sample_pdf, out, "CONFIDENTIAL")
    assert result.ok, result.error
    text = PdfReader(out).pages[0].extract_text()
    assert "CONFIDENTIAL" in text


def test_chinese_text_watermark(tmp_path, sample_pdf):
    out = tmp_path / "wm.pdf"
    result = add_text_watermark(sample_pdf, out, "内部资料")
    assert result.ok, result.error
    assert "内部资料" in PdfReader(out).pages[0].extract_text()


def test_single_mode_one_watermark_per_page(tmp_path, sample_pdf):
    out = tmp_path / "wm.pdf"
    add_text_watermark(sample_pdf, out, "DRAFT", mode="single")
    text = PdfReader(out).pages[0].extract_text()
    assert text.count("DRAFT") == 1


def test_watermark_only_selected_pages(tmp_path, sample_pdf):
    out = tmp_path / "wm.pdf"
    add_text_watermark(sample_pdf, out, "X", pages="1")
    texts = [p.extract_text() for p in PdfReader(out).pages]
    assert "X" in texts[0]
    assert "X" not in texts[1]


def test_watermark_rejects_encrypted(tmp_path, encrypted_pdf):
    result = add_text_watermark(encrypted_pdf, tmp_path / "x.pdf", "X")
    assert not result.ok and "加密" in result.error


def test_image_watermark(tmp_path, sample_pdf, seal_png):
    out = tmp_path / "wm.pdf"
    result = add_image_watermark(sample_pdf, out, seal_png)
    assert result.ok, result.error
    for page in PdfReader(out).pages:
        assert len(page.images) == 1


def test_image_watermark_opacity_keeps_image(tmp_path, sample_pdf, seal_png):
    out = tmp_path / "wm.pdf"
    result = add_image_watermark(sample_pdf, out, seal_png, opacity=0.3)
    assert result.ok
    assert len(PdfReader(out).pages[0].images) == 1


def test_image_watermark_rejects_bad_pos(tmp_path, sample_pdf, seal_png):
    result = add_image_watermark(sample_pdf, tmp_path / "x.pdf", seal_png, pos="middle")
    assert not result.ok


def test_image_watermark_invalid_image(tmp_path, sample_pdf):
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image")
    result = add_image_watermark(sample_pdf, tmp_path / "x.pdf", bad)
    assert not result.ok
