import pytest
from pypdf import PdfReader
from tests.conftest import make_pdf

from pdf_gui.core.split import (
    parse_ranges,
    split_by_blank_pages,
    split_by_ranges,
    split_every_n,
)


def test_parse_simple_and_range():
    assert parse_ranges("1-3,5", 10) == [range(1, 4), range(5, 6)]


def test_parse_end_range():
    assert parse_ranges("8-10", 10) == [range(8, 11)]


def test_parse_single_page():
    assert parse_ranges("2", 3) == [range(2, 3)]


def test_parse_chinese_comma_and_spaces():
    assert parse_ranges(" 1-3，5 ", 10) == [range(1, 4), range(5, 6)]


def test_parse_rejects_zero():
    with pytest.raises(ValueError):
        parse_ranges("0", 10)


def test_parse_rejects_out_of_total():
    with pytest.raises(ValueError):
        parse_ranges("11", 10)


def test_parse_rejects_descending():
    with pytest.raises(ValueError):
        parse_ranges("3-1", 10)


def test_parse_rejects_garbage():
    with pytest.raises(ValueError):
        parse_ranges("abc", 10)


def test_parse_rejects_empty():
    with pytest.raises(ValueError):
        parse_ranges("", 10)


def test_split_every_n(tmp_path, ten_page_pdf):
    out_dir = tmp_path / "parts"
    result = split_every_n(ten_page_pdf, 3, out_dir)
    assert result.ok, result.error
    parts = sorted(result.outputs)  # 按文件名 _01.._04 排序
    assert len(parts) == 4  # 3+3+3+1
    counts = [len(PdfReader(p).pages) for p in parts]
    assert counts == [3, 3, 3, 1]
    assert all(p.parent == out_dir for p in parts)


def test_split_every_n_rejects_encrypted(tmp_path, encrypted_pdf):
    result = split_every_n(encrypted_pdf, 2, tmp_path / "x")
    assert not result.ok and "加密" in result.error


def test_split_by_ranges(tmp_path, ten_page_pdf):
    out_dir = tmp_path / "parts"
    result = split_by_ranges(ten_page_pdf, "1-3,5", out_dir)
    assert result.ok, result.error
    assert len(result.outputs) == 2
    assert len(PdfReader(result.outputs[0]).pages) == 3
    assert len(PdfReader(result.outputs[1]).pages) == 1
    assert PdfReader(result.outputs[1]).pages[0].extract_text().strip() == "page 5"


def test_split_by_blank_pages(tmp_path):
    src = make_pdf(tmp_path / "b.pdf", pages=5, blank_pages={3})
    out_dir = tmp_path / "parts"
    result = split_by_blank_pages(src, out_dir)
    assert result.ok, result.error
    assert len(result.outputs) == 2
    assert len(PdfReader(result.outputs[0]).pages) == 2
    assert len(PdfReader(result.outputs[1]).pages) == 2


def test_split_by_blank_pages_no_blank(tmp_path, sample_pdf):
    out_dir = tmp_path / "parts"
    result = split_by_blank_pages(sample_pdf, out_dir)
    assert result.ok
    assert len(result.outputs) == 1
    assert len(PdfReader(result.outputs[0]).pages) == 3
