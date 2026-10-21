"""PDF 办公百宝箱：离线批量 PDF 处理工具。版本号唯一来源为 gui/app_meta.json。"""

from .gui.meta import load_meta as _load_meta

__version__ = _load_meta()["version"]
