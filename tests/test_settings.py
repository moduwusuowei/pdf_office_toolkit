from pdf_gui.gui.settings import DEFAULTS, load_settings, save_settings


def test_load_missing_file_returns_defaults(tmp_path):
    assert load_settings(tmp_path / "nope.json") == DEFAULTS


def test_save_and_roundtrip(tmp_path):
    p = tmp_path / "s.json"
    assert save_settings({"lang": "en"}, p) is True
    s = load_settings(p)
    assert s["lang"] == "en"
    # 未保存的键取默认值
    assert s["conflict"] == DEFAULTS["conflict"]


def test_load_tolerates_corruption(tmp_path):
    p = tmp_path / "s.json"
    p.write_text("{bad json", encoding="utf-8")
    assert load_settings(p) == DEFAULTS


def test_load_ignores_unknown_keys(tmp_path):
    p = tmp_path / "s.json"
    p.write_text('{"lang": "en", "hack": 1}', encoding="utf-8")
    s = load_settings(p)
    assert "hack" not in s
    assert s["lang"] == "en"


def test_save_failure_returns_false(tmp_path):
    # 路径是目录 → 写入 OSError → False 而非抛异常
    d = tmp_path / "as_dir"
    d.mkdir()
    assert save_settings({"lang": "zh"}, d) is False
