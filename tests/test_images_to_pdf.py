from PIL import Image
from pypdf import PdfReader

from pdf_gui.core.images_to_pdf import images_to_pdf


def _img(path, size=(400, 300), color=(220, 30, 30), mode="RGB"):
    Image.new(mode, size, color).save(path)
    return path


def test_images_become_a4_pages(tmp_path):
    paths = [_img(tmp_path / "a.jpg", (400, 300)),
             _img(tmp_path / "b.png", (300, 500), (30, 30, 220))]
    out = tmp_path / "out.pdf"
    result = images_to_pdf(paths, out)
    assert result.ok, result.error
    reader = PdfReader(out)
    assert len(reader.pages) == 2
    # 竖版 A4 与横版 A4 各一页（auto 按图片长宽选方向）
    first = reader.pages[0].mediabox
    second = reader.pages[1].mediabox
    assert float(first.width) > float(first.height)      # 400×300 → 横向
    assert float(second.height) > float(second.width)    # 300×500 → 纵向
    assert abs(float(first.width) - 841.89) < 1


def test_original_size_uses_image_dimensions(tmp_path):
    src = _img(tmp_path / "wide.jpg", (200, 100))
    out = tmp_path / "out.pdf"
    result = images_to_pdf([src], out, page_size="original")
    assert result.ok, result.error
    box = PdfReader(out).pages[0].mediabox
    assert abs(float(box.width) - 150) < 1      # 200px @96dpi = 150pt
    assert abs(float(box.height) - 75) < 1


def test_transparent_png_gets_white_background(tmp_path):
    src = tmp_path / "alpha.png"
    Image.new("RGBA", (120, 120), (0, 0, 0, 0)).save(src)
    out = tmp_path / "out.pdf"
    result = images_to_pdf([src], out, page_size="original")
    assert result.ok, result.error
    assert len(PdfReader(out).pages) == 1


def test_cancel_leaves_no_output(tmp_path):
    paths = [_img(tmp_path / f"{i}.jpg") for i in range(3)]
    out = tmp_path / "out.pdf"
    result = images_to_pdf(paths, out, cancel_cb=lambda: True)
    assert not result.ok and result.cancelled
    assert not out.exists()


def test_empty_list_rejected(tmp_path):
    result = images_to_pdf([], tmp_path / "out.pdf")
    assert not result.ok


def test_unreadable_image_raises(tmp_path):
    bad = tmp_path / "bad.jpg"
    bad.write_text("not an image", encoding="utf-8")
    try:
        images_to_pdf([bad], tmp_path / "out.pdf")
    except ValueError as e:
        assert "无法读取" in str(e)
    else:
        raise AssertionError("损坏图片应抛 ValueError")
