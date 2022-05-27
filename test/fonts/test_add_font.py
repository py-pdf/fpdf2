from pathlib import Path

import pytest

from fpdf import FPDF
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_add_font_non_existing_file():
    pdf = FPDF()
    with pytest.raises(FileNotFoundError) as error:
        pdf.add_font("MyFont", fname="non-existing-file.ttf")
    assert str(error.value) == "TTF Font file not found: non-existing-file.ttf"


def test_add_font_pkl():
    pdf = FPDF()
    with pytest.raises(ValueError) as error:
        pdf.add_font("MyFont", fname="non-existing-file.pkl")
    assert str(error.value) == (
        "Unsupported font file extension: .pkl. add_font() used to accept .pkl file as input, "
        "but for security reasons this feature is deprecated since v2.5.1 and has been removed in v2.5.3."
    )


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


def test_add_font_with_str_fname_ok(tmp_path):
    font_file_path = HERE / "Roboto-Regular.ttf"
    for font_cache_dir in (True, str(tmp_path), None):
        with pytest.warns(DeprecationWarning):
            pdf = FPDF(font_cache_dir=font_cache_dir)
            pdf.add_font("Roboto-Regular", fname=str(font_file_path))
            pdf.set_font("Roboto-Regular", size=64)
            pdf.add_page()
            pdf.cell(txt="Hello World!")
            assert_pdf_equal(pdf, HERE / "add_font_unicode.pdf", tmp_path)


def test_add_core_fonts():
    font_file_path = HERE / "Roboto-Regular.ttf"
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Helvetica", fname=font_file_path)
    pdf.add_font("Helvetica", style="B", fname=font_file_path)
    pdf.add_font("helvetica", style="IB", fname=font_file_path)
    pdf.add_font("times", style="", fname=font_file_path)
    pdf.add_font("courier", fname=font_file_path)
    assert not pdf.fonts  # No fonts added, as all of them are core fonts


def test_render_en_dash(tmp_path):  # issue-166
    pdf = FPDF()
    font_file_path = HERE / "Roboto-Regular.ttf"
    pdf.add_font("Roboto-Regular", fname=str(font_file_path))
    pdf.set_font("Roboto-Regular", size=120)
    pdf.add_page()
    pdf.cell(w=pdf.epw, txt="–")  # U+2013
    assert_pdf_equal(pdf, HERE / "render_en_dash.pdf", tmp_path)


def test_add_font_otf():
    pdf = FPDF()
    font_file_path = HERE / "Quicksand-Regular.otf"
    with pytest.raises(RuntimeError) as error:
        pdf.add_font("Quicksand", fname=font_file_path)
    assert str(error.value) == "Postscript outlines are not supported"
