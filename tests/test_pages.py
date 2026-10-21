import pytest

from pdf_gui.core.pages import parse_page_spec


def test_all_pages():
    assert parse_page_spec("all", 3) == [0, 1, 2]


def test_empty_means_all():
    assert parse_page_spec("", 3) == [0, 1, 2]


def test_last_page():
    assert parse_page_spec("last", 5) == [4]


def test_explicit_list():
    assert parse_page_spec("1,3,5", 5) == [0, 2, 4]


def test_out_of_range_raises():
    with pytest.raises(ValueError):
        parse_page_spec("6", 5)


def test_zero_raises():
    with pytest.raises(ValueError):
        parse_page_spec("0", 5)


def test_garbage_raises():
    with pytest.raises(ValueError):
        parse_page_spec("x", 5)
