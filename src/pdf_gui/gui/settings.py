"""用户设置：JSON 持久化到用户主目录，损坏/缺键容错。"""

import json
from pathlib import Path

SETTINGS_PATH = Path.home() / ".pdf_office_toolkit.json"

DEFAULTS = {
    "lang": "zh",
    "out_dir": str(Path.home() / "Documents" / "PDF_Toolkit"),
    "conflict": "rename",  # rename | overwrite | skip
    "merge_name": "合并.pdf",
    "auto_open_out": False,  # 批处理成功后自动打开输出目录
}


def load_settings(path: Path | str | None = None) -> dict:
    """读设置；文件缺失/损坏/含未知键时静默回退默认值。"""
    path = Path(path) if path is not None else SETTINGS_PATH
    data = dict(DEFAULTS)
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            data.update({k: v for k, v in loaded.items() if k in DEFAULTS})
    except (OSError, ValueError):
        pass
    return data


def save_settings(settings: dict, path: Path | str | None = None) -> bool:
    """写设置；失败返回 False，不抛异常（如主目录只读）。"""
    path = Path(path) if path is not None else SETTINGS_PATH
    data = {k: v for k, v in settings.items() if k in DEFAULTS}
    try:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except OSError:
        return False
