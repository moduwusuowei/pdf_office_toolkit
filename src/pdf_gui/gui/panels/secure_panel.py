"""加密与解密面板：加密=用户密码+可选所有者密码；解密=密码。"""

from pathlib import Path

from ...core import decrypt_pdf, encrypt_pdf
from ...workers import Job, resolve_conflict
from ..i18n import t
from .base import PanelBase


class SecurePanel(PanelBase):
    name = "secure"
    title_key = "secure_title"
    multi_file = True

    def build_params(self, parent):
        self._radio(parent, "mode", [(t("secure_mode_enc"), "enc"),
                                     (t("secure_mode_dec"), "dec")])
        self._labeled_entry(parent, "pw", "secure_pw", default="", show="•")
        self._labeled_entry(parent, "ownerpw", "secure_ownerpw", default="", show="•")

    def make_jobs(self, files, out_dir):
        rule = self.conflict_rule
        pw = (self.state.get("pw") or "").strip()
        if not pw:
            raise ValueError(t("secure_pw"))
        encrypting = self.state.get("mode", 0) == 0
        ownerpw = (self.state.get("ownerpw") or "").strip()
        if encrypting and not ownerpw:
            ownerpw = None  # 未填所有者密码时与用户密码一致（core 默认行为）
        jobs, skipped = [], []
        for f in files:
            f = Path(f)
            out = resolve_conflict(out_dir / f.name, rule)
            if out is None:
                skipped.append(f.name)
                continue
            if encrypting:
                jobs.append(Job(encrypt_pdf, {
                    "src": f, "dst": out, "user_password": pw,
                    "owner_password": ownerpw,
                }, label=f.name))
            else:
                jobs.append(Job(decrypt_pdf, {
                    "src": f, "dst": out, "password": pw,
                }, label=f.name))
        return jobs, skipped
