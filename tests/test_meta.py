import re

from pdf_gui.gui.meta import load_meta


def test_meta_has_required_keys():
    meta = load_meta()
    assert {"version", "copyright", "repository"} <= set(meta)


def test_meta_version_format():
    assert re.fullmatch(r"\d+\.\d+\.\d+", load_meta()["version"])


def test_meta_copyright_owner():
    assert "魔都吴所谓" in load_meta()["copyright"]


def test_meta_repository_is_url():
    assert load_meta()["repository"].startswith("https://")
