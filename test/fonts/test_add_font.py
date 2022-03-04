import os
from contextlib import suppress
from pathlib import Path

import pytest

from fpdf import FPDF
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_add_font_non_existing():
    pdf = FPDF()
    for uni in (True, False):
        with pytest.raises(FileNotFoundError) as error:
            pdf.add_font("non-existing", uni=uni)
        expected_msg = "[Errno 2] No such file or directory: 'non-existing.pkl'"
        assert str(error.value) == expected_msg


def test_deprecation_warning_for_FPDF_CACHE_DIR():
    # pylint: disable=import-outside-toplevel,pointless-statement,reimported
    from fpdf import fpdf

    with pytest.warns(DeprecationWarning):
        fpdf.FPDF_CACHE_DIR
    with pytest.warns(DeprecationWarning):
        fpdf.FPDF_CACHE_DIR = "/tmp"
    with pytest.warns(DeprecationWarning):
        fpdf.FPDF_CACHE_MODE
    with pytest.warns(DeprecationWarning):
        fpdf.FPDF_CACHE_MODE = 1

    fpdf.SOME = 1
    assert fpdf.SOME == 1

    import fpdf

    with pytest.warns(DeprecationWarning):
        fpdf.FPDF_CACHE_DIR
    with pytest.warns(DeprecationWarning):
        fpdf.FPDF_CACHE_DIR = "/tmp"
    with pytest.warns(DeprecationWarning):
        fpdf.FPDF_CACHE_MODE
    with pytest.warns(DeprecationWarning):
        fpdf.FPDF_CACHE_MODE = 1

    fpdf.SOME = 1
    assert fpdf.SOME == 1


def test_add_font_unicode_with_path_fname_ok(tmp_path):
    for font_cache_dir in (True, tmp_path, None):
        pdf = FPDF(font_cache_dir=font_cache_dir)
        font_file_path = HERE / "Roboto-Regular.ttf"
        pdf.add_font("Roboto-Regular", fname=str(font_file_path))
        pdf.set_font("Roboto-Regular", size=64)
        pdf.add_page()
        pdf.cell(txt="Hello World!")
        assert_pdf_equal(pdf, HERE / "add_font_unicode.pdf", tmp_path)


def test_add_font_unicode_with_str_fname_ok(tmp_path):
    for font_cache_dir in (True, str(tmp_path), None):
        pdf = FPDF(font_cache_dir=font_cache_dir)
        font_file_path = HERE / "Roboto-Regular.ttf"
        pdf.add_font("Roboto-Regular", fname=str(font_file_path))
        pdf.set_font("Roboto-Regular", size=64)
        pdf.add_page()
        pdf.cell(txt="Hello World!")
        assert_pdf_equal(pdf, HERE / "add_font_unicode.pdf", tmp_path)


def teardown():
    # Clean-up for test_add_font_from_pkl
    with suppress(FileNotFoundError):
        os.remove("Roboto-Regular.pkl")


def test_add_core_fonts():
    """Try to add core fonts. This shouldn't add any fonts, as core fonts like
    Helvetica are built-in"""
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Helvetica")
    pdf.add_font("Helvetica", style="B")
    pdf.add_font("helvetica", style="IB")
    pdf.add_font("times", style="")
    pdf.add_font("courier")
    assert not pdf.fonts  # No fonts added, as all of them are core fonts


def test_render_en_dash(tmp_path):  # issue-166
    pdf = FPDF()
    font_file_path = HERE / "Roboto-Regular.ttf"
    pdf.add_font("Roboto-Regular", fname=str(font_file_path))
    pdf.set_font("Roboto-Regular", size=120)
    pdf.add_page()
    pdf.cell(w=pdf.epw, txt="–")  # U+2013
    assert_pdf_equal(pdf, HERE / "render_en_dash.pdf", tmp_path)
