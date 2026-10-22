"""界面配色：默认沿用 CustomTkinter 内置蓝主题，用户可通过配置文件覆盖。

配置文件：~/.pdf_office_toolkit_theme.json
颜色值可写单个颜色（明暗通用），或 [浅色, 深色] 两元素数组。
修改后重启程序生效；未知键与非法颜色值会被忽略（回退默认）。
"""

import json
from pathlib import Path

import customtkinter as ctk

THEME_PATH = Path.home() / ".pdf_office_toolkit_theme.json"

DEFAULT_THEME = {
    "_说明": "单色写字符串；明暗分开写 [浅色, 深色]；改完重启生效。",
    "window_bg": ["gray92", "gray14"],
    "card_bg": ["gray86", "gray17"],
    "accent": ["#3B8ED0", "#1F6AA5"],
    # 与 _darken(accent) 保持一致：只改主色时悬停色按同一规则重新推导
    "accent_hover": ["#2F71A6", "#185484"],
    "button_text": ["#DCE4EE", "#DCE4EE"],
    "text": ["gray10", "#DCE4EE"],
    "muted_text": ["gray", "gray"],
    "entry_bg": ["#F9F9FA", "#343638"],
    "border": ["#979DA2", "#565B5E"],
    "progress_track": ["#939BA2", "#4A4D50"],
}

# 配色编辑器里展示的项（顺序即界面顺序）：(token, 显示名 key)
THEME_TOKENS = [
    ("window_bg", "theme_tok_window_bg"),
    ("card_bg", "theme_tok_card_bg"),
    ("accent", "theme_tok_accent"),
    ("accent_hover", "theme_tok_accent_hover"),
    ("button_text", "theme_tok_button_text"),
    ("text", "theme_tok_text"),
    ("muted_text", "theme_tok_muted_text"),
    ("entry_bg", "theme_tok_entry_bg"),
    ("border", "theme_tok_border"),
    ("progress_track", "theme_tok_progress_track"),
]


def _valid_color(value) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return all(isinstance(c, str) and c.strip() for c in value)
    return False


def _pair(value) -> list[str]:
    """单色 → [浅色, 深色]；已经是两项的原样返回。"""
    return [value, value] if isinstance(value, str) else [str(value[0]), str(value[1])]


def _darken(value: str, factor: float = 0.8) -> str:
    """#RRGGBB 按比例调暗；gray50 之类的命名色无法计算，原样返回。"""
    if not (isinstance(value, str) and len(value) == 7 and value.startswith("#")):
        return value
    try:
        r, g, b = (int(value[i:i + 2], 16) for i in (1, 3, 5))
    except ValueError:
        return value
    return "#%02X%02X%02X" % (int(r * factor), int(g * factor), int(b * factor))


def derive_hover(accent: str | list[str]) -> list[str]:
    """由主色推出悬停色：只改主色时，按钮悬停、下拉箭头等跟着一起变。"""
    return [_darken(c) for c in _pair(accent)]


def load_theme(path: Path | str | None = None, *, derive: bool = True) -> dict:
    """读取主题配置；缺失/损坏/非法项静默回退默认值。

    derive=True 时，文件里只写了 accent 没写 accent_hover 的，悬停色按主色推导，
    避免改了主色、下拉箭头/按钮悬停还是默认蓝。
    """
    path = Path(path) if path is not None else THEME_PATH
    theme = {k: v for k, v in DEFAULT_THEME.items() if not k.startswith("_")}
    explicit: set[str] = set()
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        loaded = None
    if isinstance(loaded, dict):
        for key, value in loaded.items():
            if key in theme and _valid_color(value):
                theme[key] = value
                explicit.add(key)
    if derive and "accent" in explicit and "accent_hover" not in explicit:
        theme["accent_hover"] = derive_hover(theme["accent"])
    return theme


def save_theme(theme: dict, path: Path | str | None = None) -> bool:
    """写主题配置；失败返回 False，不抛异常。"""
    path = Path(path) if path is not None else THEME_PATH
    data = {"_说明": DEFAULT_THEME["_说明"]}
    for key in DEFAULT_THEME:
        if key.startswith("_"):
            continue
        if key in theme and _valid_color(theme[key]):
            data[key] = theme[key]
    try:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except OSError:
        return False


def ensure_theme_file(path: Path | str | None = None) -> bool:
    """首次运行时落一份默认配色文件，方便用户直接改。"""
    path = Path(path) if path is not None else THEME_PATH
    if path.exists():
        return False
    return save_theme(load_theme(), path)


def apply_theme(theme: dict | None = None) -> None:
    """把主题色注入 CustomTkinter 的全局主题表；须在建控件前调用。"""
    theme = theme or load_theme()
    manager = getattr(ctk, "ThemeManager", None)
    table = getattr(manager, "theme", None)
    if not isinstance(table, dict):
        return  # CTk 版本不支持时保持内置配色

    def put(widget: str, field: str, key: str) -> None:
        row = table.get(widget)
        if isinstance(row, dict) and field in row:
            row[field] = theme.get(key, row[field])

    for widget in ("CTk", "CTkToplevel"):
        put(widget, "fg_color", "window_bg")
    put("CTkFrame", "fg_color", "card_bg")
    put("CTkFrame", "top_fg_color", "card_bg")
    put("CTkFrame", "border_color", "border")
    put("CTkScrollableFrame", "label_fg_color", "card_bg")
    put("CTkButton", "fg_color", "accent")
    put("CTkButton", "hover_color", "accent_hover")
    put("CTkButton", "text_color", "button_text")
    put("CTkButton", "text_color_disabled", "muted_text")
    put("CTkButton", "border_color", "border")
    put("CTkOptionMenu", "fg_color", "accent")
    put("CTkOptionMenu", "button_color", "accent_hover")
    put("CTkOptionMenu", "button_hover_color", "accent_hover")
    put("CTkOptionMenu", "text_color", "button_text")
    put("CTkOptionMenu", "text_color_disabled", "muted_text")
    put("CTkComboBox", "fg_color", "entry_bg")
    put("CTkComboBox", "border_color", "border")
    put("CTkComboBox", "text_color", "text")
    put("CTkComboBox", "text_color_disabled", "muted_text")
    put("CTkRadioButton", "fg_color", "accent")
    put("CTkRadioButton", "hover_color", "accent_hover")
    put("CTkRadioButton", "border_color", "border")
    put("CTkRadioButton", "text_color", "text")
    put("CTkRadioButton", "text_color_disabled", "muted_text")
    put("CTkCheckBox", "fg_color", "accent")
    put("CTkCheckBox", "hover_color", "accent_hover")
    put("CTkCheckBox", "border_color", "border")
    put("CTkCheckBox", "checkmark_color", "button_text")
    put("CTkCheckBox", "text_color", "text")
    put("CTkSwitch", "fg_color", "progress_track")
    put("CTkSwitch", "progress_color", "accent")
    put("CTkSwitch", "text_color", "text")
    put("CTkSlider", "fg_color", "progress_track")
    put("CTkSlider", "progress_color", "accent")
    put("CTkSlider", "button_color", "accent")
    put("CTkSlider", "button_hover_color", "accent_hover")
    put("CTkProgressBar", "fg_color", "progress_track")
    put("CTkProgressBar", "progress_color", "accent")
    put("CTkLabel", "text_color", "text")
    put("CTkEntry", "fg_color", "entry_bg")
    put("CTkEntry", "border_color", "border")
    put("CTkEntry", "text_color", "text")
    put("CTkEntry", "placeholder_text_color", "muted_text")
    put("CTkTextbox", "fg_color", "entry_bg")
    put("CTkTextbox", "border_color", "border")
    put("CTkTextbox", "text_color", "text")
    put("DropdownMenu", "fg_color", "entry_bg")
    put("DropdownMenu", "hover_color", "card_bg")
    put("DropdownMenu", "text_color", "text")


def color(key: str) -> str | list:
    """取当前主题色（供需要显式着色的控件使用）。"""
    theme = load_theme()
    return theme.get(key, DEFAULT_THEME.get(key, "gray"))
