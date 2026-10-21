"""压缩面板：无损 / 光栅化，输出 xxx_min.pdf 避免覆盖源文件。"""

from pathlib import Path

from ...core import compress_pdf
from ...workers import Job, resolve_conflict
from ..i18n import t
from .base import PanelBase


class CompressPanel(PanelBase):
    name = "compress"
    title_key = "comp_title"
    multi_file = True

    def build_params(self, parent):
        self._radio(parent, "mode", [(t("comp_mode_lossless"), "lossless"),
                                     (t("comp_mode_rasterize"), "rasterize")])
        self._labeled_slider(parent, "dpi", "comp_dpi", 50, 200, 100,
                             steps=150, fmt=int)
        self._labeled_slider(parent, "quality", "comp_quality", 30, 95, 70,
                             steps=65, fmt=int)

    def make_jobs(self, files, out_dir):
        rule = self.conflict_rule
        mode = "lossless" if self.state.get("mode", 0) == 0 else "rasterize"
        jobs, skipped = [], []
        for f in files:
            f = Path(f)
            out = resolve_conflict(out_dir / f"{f.stem}_min.pdf", rule)
            if out is None:
                skipped.append(f.name)
                continue
            jobs.append(Job(compress_pdf, {
                "src": f, "dst": out, "mode": mode,
                "dpi": int(float(self.state.get("dpi", 100))),
                "jpeg_quality": int(float(self.state.get("quality", 70))),
            }, label=f.name))
        return jobs, skipped
