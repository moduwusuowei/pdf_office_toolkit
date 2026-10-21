"""合并面板：全部合并为一个 / 按所在文件夹分别合并。"""

from pathlib import Path

from ...core import merge_files
from ...workers import Job, resolve_conflict
from ..i18n import t
from .base import PanelBase


class MergePanel(PanelBase):
    name = "merge"
    title_key = "merge_title"
    multi_file = True

    def build_params(self, parent):
        self._radio(parent, "mode", [(t("merge_single"), "single"),
                                     (t("merge_per_folder"), "per_folder")])
        self._labeled_entry(parent, "merge_name", "merge_name",
                            default=self.state.get("merge_name", "合并.pdf"))

    def make_jobs(self, files, out_dir):
        rule = self.conflict_rule
        jobs, skipped = [], []
        if self.state.get("mode", 0) == 0:  # 全部合并为一个
            name = (self.state.get("merge_name") or "").strip()
            if not name:
                raise ValueError(t("merge_name"))
            if not name.lower().endswith(".pdf"):
                name += ".pdf"
            out = resolve_conflict(out_dir / name, rule)
            if out is None:
                return [], []
            jobs.append(Job(merge_files,
                            {"paths": [str(p) for p in files], "output": out},
                            label=out.name))
            return jobs, skipped
        # 按所在文件夹分别合并，输出到 out_dir，命名为 {文件夹名}_{merge_name}
        name = (self.state.get("merge_name") or "merged.pdf")
        if not name.lower().endswith(".pdf"):
            name += ".pdf"
        groups: dict[Path, list] = {}
        for p in files:
            groups.setdefault(Path(p).parent, []).append(p)
        for folder in sorted(groups):
            out = resolve_conflict(out_dir / f"{folder.name}_{name}", rule)
            if out is None:
                skipped.append(f"{folder.name}_{name}")
                continue
            jobs.append(Job(merge_files,
                            {"paths": [str(p) for p in groups[folder]], "output": out},
                            label=out.name))
        return jobs, skipped
