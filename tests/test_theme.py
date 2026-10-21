import json

import customtkinter as ctk

from pdf_gui.gui.i18n import _STRINGS
from pdf_gui.gui.theme import (
    DEFAULT_THEME,
    THEME_TOKENS,
    apply_theme,
    ensure_theme_file,
    load_theme,
    save_theme,
)


def test_missing_file_returns_defaults(tmp_path):
    theme = load_theme(tmp_path / "missing.json")
    assert theme["accent"] == DEFAULT_THEME["accent"]
    assert theme["window_bg"] == DEFAULT_THEME["window_bg"]
    assert "_说明" not in theme


def test_partial_override_keeps_other_defaults(tmp_path):
    path = tmp_path / "theme.json"
    path.write_text(json.dumps({"accent": "#123456"}), encoding="utf-8")
    theme = load_theme(path)
    assert theme["accent"] == "#123456"
    assert theme["card_bg"] == DEFAULT_THEME["card_bg"]


def test_invalid_values_fall_back(tmp_path):
    path = tmp_path / "theme.json"
    path.write_text(json.dumps({
        "accent": "",
        "text": ["#ffffff"],
        "window_bg": 42,
        "entry_bg": ["#ffffff", "#000000"],
        "unknown_key": "#ff0000",
    }), encoding="utf-8")
    theme = load_theme(path)
    assert theme["accent"] == DEFAULT_THEME["accent"]
    assert theme["text"] == DEFAULT_THEME["text"]
    assert theme["window_bg"] == DEFAULT_THEME["window_bg"]
    assert theme["entry_bg"] == ["#ffffff", "#000000"]
    assert "unknown_key" not in theme


def test_broken_json_falls_back(tmp_path):
    path = tmp_path / "theme.json"
    path.write_text("{not json", encoding="utf-8")
    assert load_theme(path) == {
        k: v for k, v in DEFAULT_THEME.items() if not k.startswith("_")}


def test_save_then_load_roundtrip(tmp_path):
    path = tmp_path / "theme.json"
    assert save_theme({"accent": ["#111111", "#222222"]}, path)
    assert load_theme(path)["accent"] == ["#111111", "#222222"]


def test_ensure_theme_file_writes_once(tmp_path):
    path = tmp_path / "theme.json"
    assert ensure_theme_file(path)
    assert path.exists()
    assert not ensure_theme_file(path)


def test_every_editor_token_has_default_and_translations():
    for token, label_key in THEME_TOKENS:
        assert token in DEFAULT_THEME
        assert label_key in _STRINGS["zh"]
        assert label_key in _STRINGS["en"]
        assert len(_STRINGS["zh"][label_key]) > 0
        assert len(_STRINGS["en"][label_key]) > 0


def test_apply_theme_reaches_extended_widgets(tmp_path):
    path = tmp_path / "theme.json"
    path.write_text(json.dumps({
        "accent": ["#AA0000", "#BB0000"],
        "border": ["#CCCCCC", "#333333"],
    }), encoding="utf-8")
    ctk.set_default_color_theme("blue")
    apply_theme(load_theme(path))
    table = ctk.ThemeManager.theme
    assert table["CTkRadioButton"]["fg_color"] == ["#AA0000", "#BB0000"]
    assert table["CTkCheckBox"]["fg_color"] == ["#AA0000", "#BB0000"]
    assert table["CTkSlider"]["progress_color"] == ["#AA0000", "#BB0000"]
    assert table["CTkEntry"]["border_color"] == ["#CCCCCC", "#333333"]
    assert table["CTkEntry"]["fg_color"] != ["#AA0000", "#BB0000"]

