import pytest
from PIL import Image, ImageDraw
from pypdf import PdfReader, PdfWriter
from pypdfium2 import PdfDocument
from tests.conftest import make_pdf

from pdf_gui.core.paging_seal import (
    apply_paging_seal,
    assemble_strips,
    split_stamp_image,
    strips_for_pages,
    trim_to_content,
)


@pytest.fixture
def padded_seal_png(tmp_path):
    """四周留大片透明的印章（模拟扫描/截图出来的印章 PNG）。"""
    img = Image.new("RGBA", (400, 300), (0, 0, 0, 0))
    ImageDraw.Draw(img).rectangle((100, 75, 300, 225), fill=(200, 0, 0, 255))
    path = tmp_path / "padded_seal.png"
    img.save(path)
    return path


def _red_bbox(image):
    pixels = image.convert("RGB").load()
    xs, ys = [], []
    for y in range(image.height):
        for x in range(image.width):
            r, g, b = pixels[x, y]
            if r > 150 and g < 90 and b < 90:
                xs.append(x)
                ys.append(y)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def test_strips_for_pages_small():
    assert strips_for_pages(10) == (10, 1)


def test_strips_for_pages_exact_20():
    assert strips_for_pages(20) == (20, 1)


def test_strips_for_pages_100():
    assert strips_for_pages(100) == (20, 5)


def test_strips_for_pages_41():
    # ceil(41/20)=3 页/条, 条数=ceil(41/3)=14
    assert strips_for_pages(41) == (14, 3)


def test_strips_for_pages_rejects_zero():
    with pytest.raises(ValueError):
        strips_for_pages(0)


def test_split_stamp_image_widths_sum():
    img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
    strips = split_stamp_image(img, 3)
    widths = [s.width for s, _ in strips]
    assert sum(widths) == 100
    assert max(widths) - min(widths) <= 1


def test_split_stamp_image_height_untouched():
    img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
    strips = split_stamp_image(img, 4)
    assert all(s.height == 100 for s, _ in strips)


def test_split_stamp_image_offsets_ascending():
    img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
    strips = split_stamp_image(img, 3)
    offsets = [left for _, left in strips]
    assert offsets == [0, 33, 67]


def test_trim_to_content_removes_transparent_margin(padded_seal_png):
    img = Image.open(padded_seal_png).convert("RGBA")
    trimmed = trim_to_content(img)
    assert trimmed.size == (201, 151)


def test_trim_to_content_rejects_fully_transparent():
    img = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    with pytest.raises(ValueError, match="全透明"):
        trim_to_content(img)


def test_assemble_strips_restores_trimmed_stamp(padded_seal_png):
    trimmed = trim_to_content(Image.open(padded_seal_png).convert("RGBA"))
    strips = split_stamp_image(trimmed, 7)
    restored = assemble_strips(strips)
    assert restored.size == trimmed.size


def test_padded_stamp_leaves_ink_on_every_page(tmp_path, sample_pdf, padded_seal_png):
    """回归：透明边不能裁掉，否则首末页分到空条，预览看起来「没反应」。"""
    out = tmp_path / "sealed.pdf"
    result = apply_paging_seal(sample_pdf, out, padded_seal_png)
    assert result.ok, result.error
    for page in PdfReader(out).pages:
        images = list(page.images)
        assert images, "overlay 图片缺失"
        assert all(img.image.getchannel("A").getextrema()[1] > 0 for img in images)


def test_strip_sits_on_right_edge_vertically_centered(tmp_path, sample_pdf,
                                                      padded_seal_png):
    out = tmp_path / "sealed.pdf"
    apply_paging_seal(sample_pdf, out, padded_seal_png)
    doc = PdfDocument(str(out))
    for idx in (0, len(doc) - 1):
        img = doc[idx].render(scale=1).to_pil()
        box = _red_bbox(img)
        assert box, f"page {idx} 没有印章像素"
        left, top, right, bottom = box
        assert right >= img.width - 3, "印章没有贴右边缘"
        assert left >= img.width - 170, "印章竖条过宽，未按切条绘制"
        center_y = (top + bottom) / 2
        assert abs(center_y - img.height / 2) < img.height * 0.1


def test_rotated_page_places_strip_on_visual_right_edge(tmp_path, sample_pdf,
                                                        padded_seal_png):
    """/Rotate 90 的扫描件：竖条应仍在视觉右边缘，而不是底边。"""
    rotated = tmp_path / "rotated.pdf"
    writer = PdfWriter()
    for page in PdfReader(sample_pdf).pages:
        page.rotate(90)
        writer.add_page(page)
    with open(rotated, "wb") as f:
        writer.write(f)

    out = tmp_path / "sealed.pdf"
    result = apply_paging_seal(rotated, out, padded_seal_png)
    assert result.ok, result.error
    img = PdfDocument(str(out))[0].render(scale=1).to_pil()
    assert img.width > img.height, "旋转后应为横向页面"
    box = _red_bbox(img)
    assert box, "没有印章像素"
    left, top, right, bottom = box
    assert right >= img.width - 3
    center_y = (top + bottom) / 2
    assert abs(center_y - img.height / 2) < img.height * 0.1


def test_apply_seal_page_count_unchanged(tmp_path, sample_pdf, seal_png):
    out = tmp_path / "sealed.pdf"
    result = apply_paging_seal(sample_pdf, out, seal_png)
    assert result.ok, result.error
    assert len(PdfReader(out).pages) == 3


def test_apply_seal_each_page_has_strip(tmp_path, sample_pdf, seal_png):
    out = tmp_path / "sealed.pdf"
    apply_paging_seal(sample_pdf, out, seal_png)
    for page in PdfReader(out).pages:
        assert len(page.images) == 1


def test_apply_seal_long_document_groups(tmp_path, seal_png):
    # 45 页 > 20：ceil(45/20)=3 页/条, 15 条 → 每页都有图
    src = make_pdf(tmp_path / "long.pdf", pages=45)
    out = tmp_path / "sealed.pdf"
    result = apply_paging_seal(src, out, seal_png)
    assert result.ok, result.error
    pages = PdfReader(out).pages
    assert len(pages) == 45
    assert all(len(p.images) == 1 for p in pages)


def test_apply_seal_rejects_encrypted(tmp_path, encrypted_pdf, seal_png):
    result = apply_paging_seal(encrypted_pdf, tmp_path / "x.pdf", seal_png)
    assert not result.ok and "加密" in result.error
