"""overlay 通用件：把 reportlab 绘制内容变成 pypdf 可叠加的单页 PDF。"""

import io

from pypdf import PdfReader
from reportlab.pdfgen import canvas as rl_canvas


def make_overlay(page_w: float, page_h: float, draw):
    """执行 draw(canvas) 生成单页 overlay，返回该页的 PdfReader。

    draw 必须用 saveState/restoreState 自行保护坐标状态。
    """
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(page_w, page_h))
    draw(c)
    c.showPage()
    c.save()
    buf.seek(0)
    return PdfReader(buf)


def append_with_overlay(reader_page, overlay_reader, writer):
    """把 overlay 页合并进 reader_page，然后追加到 writer。"""
    reader_page.merge_page(overlay_reader.pages[0])
    writer.add_page(reader_page)
