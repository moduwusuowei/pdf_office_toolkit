"""版本 / 版权 / 仓库地址：统一从 app_meta.json 读取（改配置不改代码）。"""

import json
from functools import lru_cache
from pathlib import Path

_DEFAULTS = {"version": "0.1.0", "copyright": "© 2026 魔都吴所谓", "repository": ""}


@lru_cache(maxsize=1)
def load_meta() -> dict:
    """读取包内 app_meta.json；缺失或损坏时回退默认值。"""
    path = Path(__file__).parent / "app_meta.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return dict(_DEFAULTS)
    return {**_DEFAULTS, **data}
