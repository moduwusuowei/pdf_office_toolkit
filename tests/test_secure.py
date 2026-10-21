from pypdf import PdfReader

from pdf_gui.core.secure import decrypt_pdf, encrypt_pdf


def test_encrypt_output_is_encrypted(tmp_path, sample_pdf):
    out = tmp_path / "enc.pdf"
    result = encrypt_pdf(sample_pdf, out, user_password="pw123")
    assert result.ok, result.error
    assert PdfReader(out).is_encrypted


def test_encrypt_rejects_encrypted_source(tmp_path, encrypted_pdf):
    result = encrypt_pdf(encrypted_pdf, tmp_path / "x.pdf", user_password="a")
    assert not result.ok and "加密" in result.error


def test_roundtrip(tmp_path, sample_pdf):
    enc = tmp_path / "enc.pdf"
    dec = tmp_path / "dec.pdf"
    encrypt_pdf(sample_pdf, enc, user_password="pw123")
    result = decrypt_pdf(enc, dec, "pw123")
    assert result.ok, result.error
    assert len(PdfReader(dec).pages) == 3


def test_decrypt_wrong_password_fails(tmp_path, sample_pdf):
    enc = tmp_path / "enc.pdf"
    encrypt_pdf(sample_pdf, enc, user_password="pw123")
    result = decrypt_pdf(enc, tmp_path / "dec.pdf", "wrong")
    assert not result.ok


def test_decrypt_unencrypted_passthrough(tmp_path, sample_pdf):
    out = tmp_path / "copy.pdf"
    result = decrypt_pdf(sample_pdf, out, "whatever")
    assert result.ok
    assert len(PdfReader(out).pages) == 3
