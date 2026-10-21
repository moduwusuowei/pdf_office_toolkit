"""渲染：pypdfium2 页面渲染与空白页检测。"""

import pypdfium2 as pdfium


def open_document(path):
    return pdfium.PdfDocument(str(path))


def render_page(doc, index: int, scale: float = 1.0):
    """渲染第 index 页（0 起）为 PIL Image。"""
    return doc[index].render(scale=scale).to_pil()


def page_is_blank(img, threshold: int = 250) -> bool:
    """近全白即视为空白页。"""
    return img.convert("L").getextrema()[0] >= threshold
