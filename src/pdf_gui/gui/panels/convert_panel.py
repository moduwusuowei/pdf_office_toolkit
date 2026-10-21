"""转图片面板：每文件一个子目录 {stem}_{fmt}/，输出 001 起编号图片。"""

from pathlib import Path

from ...core import pdf_to_images
from ...workers import Job
from .base import PanelBase


class ConvertPanel(PanelBase):
    name = "convert"
    title_key = "conv_title"
    multi_file = True

    def build_params(self, parent):
        self._labeled_slider(parent, "dpi", "conv_dpi", 72, 300, 150,
                             steps=228, fmt=int)
        self._option(parent, "fmt", "conv_fmt", ["PNG", "JPG"], default_index=0)
        self._labeled_slider(parent, "quality", "conv_quality", 50, 100, 90,
                             steps=50, fmt=int)

    def make_jobs(self, files, out_dir):
        rule = self.conflict_rule
        fmt = "png" if self.state.get("fmt", 0) == 0 else "jpg"
        jobs, skipped = [], []
        for f in files:
            f = Path(f)
            sub = out_dir / f"{f.stem}_{fmt}"
            if rule == "skip" and any(sub.glob(f"*.{fmt}")):
                skipped.append(f.name)
                continue
            jobs.append(Job(pdf_to_images, {
                "src": f, "out_dir": sub, "fmt": fmt,
                "dpi": int(float(self.state.get("dpi", 150))),
                "quality": int(float(self.state.get("quality", 90))),
            }, label=f.name))
        return jobs, skipped
