"""拆分面板：每 N 页一拆 / 按页码范围 / 按空白页分段。"""

from pathlib import Path

from ...core import split_by_blank_pages, split_by_ranges, split_every_n
from ...workers import Job
from ..i18n import t
from .base import PanelBase


class SplitPanel(PanelBase):
    name = "split"
    title_key = "split_title"
    multi_file = True

    def build_params(self, parent):
        self._radio(parent, "mode", [(t("split_every"), "every"),
                                     (t("split_ranges"), "ranges"),
                                     (t("split_blank"), "blank")])
        self._labeled_entry(parent, "n", "split_n", default="3")
        self._labeled_entry(parent, "ranges", "split_ranges_hint", default="1-3,5")

    def make_jobs(self, files, out_dir):
        rule = self.conflict_rule
        mode = self.state.get("mode", 0)
        jobs, skipped = [], []
        for f in files:
            f = Path(f)
            if rule == "skip" and any(out_dir.glob(f"{f.stem}_*.pdf")):
                skipped.append(f.name)  # 多输出任务：跳过规则按已有产物判断
                continue
            if mode == 0:
                try:
                    n = int(self.state.get("n", 3))
                except ValueError:
                    raise ValueError(t("split_n")) from None
                jobs.append(Job(split_every_n,
                                {"src": f, "n": n, "out_dir": out_dir}, label=f.name))
            elif mode == 1:
                spec = (self.state.get("ranges") or "").strip()
                if not spec:
                    raise ValueError(t("split_ranges_hint"))
                jobs.append(Job(split_by_ranges,
                                {"src": f, "spec": spec, "out_dir": out_dir},
                                label=f.name))
            else:
                jobs.append(Job(split_by_blank_pages,
                                {"src": f, "out_dir": out_dir}, label=f.name))
        return jobs, skipped
