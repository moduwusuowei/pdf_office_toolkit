"""测试夹具：用 reportlab 现场生成样本 PDF 与印章图片，零二进制依赖。"""

import io
import random

import pytest
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas


def make_pdf(path, pages=3, blank_pages=frozenset(), landscape_pages=frozenset(),
              noisy_image=False):
    """生成样本 PDF。blank_pages/landscape_pages 用 1 起页码指定。"""
    c = rl_canvas.Canvas(str(path), pagesize=A4)
    for i in range(1, pages + 1):
        if i in landscape_pages:
            c.setPageSize(landscape(A4))
        else:
            c.setPageSize(A4)
        if noisy_image:
            # 生成噪声大图，用于压缩/图片水印测试
            random.seed(i)
            data = bytes(random.getrandbits(8) for _ in range(800 * 800 * 3))
            img = Image.frombytes("RGB", (800, 800), data)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            c.drawImage(ImageReader(buf), 0, 0, 400, 400)
        if i not in blank_pages:
            c.setFont("Helvetica", 12)
            c.drawString(72, 800, f"page {i}")
        c.showPage()
    c.save()
    return path


@pytest.fixture
def sample_pdf(tmp_path):
    """3 页普通 PDF。"""
    return make_pdf(tmp_path / "sample.pdf", pages=3)


@pytest.fixture
def ten_page_pdf(tmp_path):
    return make_pdf(tmp_path / "ten.pdf", pages=10)


@pytest.fixture
def seal_png(tmp_path):
    """透明底红色圆形印章 PNG。"""
    img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((10, 10, 190, 190), outline=(200, 0, 0, 255), width=6)
    d.text((60, 95), "SEAL", fill=(200, 0, 0, 255))
    p = tmp_path / "seal.png"
    img.save(p)
    return p


@pytest.fixture
def encrypted_pdf(tmp_path):
    """加密的 3 页 PDF，密码 'pw123'。"""
    from pypdf import PdfReader, PdfWriter

    src = make_pdf(tmp_path / "plain.pdf", pages=3)
    reader = PdfReader(src)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(user_password="pw123", algorithm="AES-256")
    out = tmp_path / "encrypted.pdf"
    with open(out, "wb") as f:
        writer.write(f)
    return out
