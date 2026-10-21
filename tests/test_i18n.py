from pdf_gui.gui.i18n import _STRINGS, available_langs, get_lang, set_lang, t


def test_zh_en_key_parity():
    zh, en = _STRINGS["zh"], _STRINGS["en"]
    assert set(zh) == set(en)
    assert all(str(v).strip() for v in zh.values())
    assert all(str(v).strip() for v in en.values())


def test_t_returns_current_lang():
    set_lang("zh")
    assert t("start") == "开始"
    set_lang("en")
    assert t("start") == "Start"
    set_lang("zh")


def test_t_format_kwargs():
    set_lang("zh")
    assert t("password_prompt", name="a.pdf") == "请输入 a.pdf 的密码"
    assert t("job_progress", label="x", done=1, total=2) == "x：1/2"


def test_unknown_key_returns_key():
    assert t("no_such_key_xyz") == "no_such_key_xyz"


def test_available_langs():
    assert set(available_langs()) == {"zh", "en"}


def test_get_lang_default_zh():
    set_lang("zh")
    assert get_lang() == "zh"
