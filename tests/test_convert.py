from PIL import Image

from pdf_gui.core.convert import pdf_to_images


def test_convert_png(tmp_path, sample_pdf):
    out_dir = tmp_path / "imgs"
    result = pdf_to_images(sample_pdf, out_dir, dpi=72)
    assert result.ok, result.error
    assert len(result.outputs) == 3
    for p in result.outputs:
        assert p.exists()
        assert p.suffix == ".png"
        with Image.open(p) as im:
            assert im.width > 0


def test_convert_jpg_quality(tmp_path, sample_pdf):
    out_dir = tmp_path / "imgs"
    result = pdf_to_images(sample_pdf, out_dir, dpi=72, fmt="jpg", quality=50)
    assert result.ok, result.error
    assert all(p.suffix == ".jpg" for p in result.outputs)


def test_convert_rejects_bad_format(tmp_path, sample_pdf):
    result = pdf_to_images(sample_pdf, tmp_path / "imgs", dpi=72, fmt="gif")
    assert not result.ok


def test_convert_rejects_encrypted(tmp_path, encrypted_pdf):
    result = pdf_to_images(encrypted_pdf, tmp_path / "imgs", dpi=72)
    assert not result.ok and "加密" in result.error
