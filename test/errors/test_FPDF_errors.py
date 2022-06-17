from pathlib import Path
from test.conftest import assert_pdf_equal

import fpdf
import pytest
from fpdf.errors import FPDFException, FPDFUnicodeEncodingException
from fpdf.image_parsing import get_img_info
from PIL import Image

HERE = Path(__file__).resolve().parent


def test_add_page_throws_without_page():
    pdf = fpdf.FPDF()
    with pytest.raises(FPDFException) as e:
        pdf.text(1, 2, "ok")

    msg = "No page open, you need to call add_page() first"
    assert str(e.value) == msg


def test_encoding_exception():
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=15)
    with pytest.raises(FPDFUnicodeEncodingException) as error:
        pdf.cell(txt="Joséō")
        # This should through an error since Helvetica is a latin-1 encoder and the ō is out of range.
    msg = (
        'Character "ō" at index 4 in text is outside the range of characters supported by the font '
        'used: "helvetica". Please consider using a Unicode font.'
    )
    assert str(error.value) == msg


def test_orientation_portrait_landscape():
    l = fpdf.FPDF(orientation="l")
    landscape = fpdf.FPDF(orientation="landscape")
    p = fpdf.FPDF(orientation="p")
    portrait = fpdf.FPDF(orientation="portrait")

    assert l.w_pt == landscape.w_pt
    assert l.h_pt == landscape.h_pt
    assert l.def_orientation == landscape.def_orientation

    assert p.w_pt == portrait.w_pt
    assert p.h_pt == portrait.h_pt
    assert p.def_orientation == portrait.def_orientation

    assert landscape.w_pt == portrait.h_pt
    assert landscape.h_pt == portrait.w_pt


def test_incorrect_orientation():
    with pytest.raises(FPDFException) as e:
        fpdf.FPDF(orientation="hello")

    msg = "Incorrect orientation: hello"
    assert str(e.value) == msg


def test_units():
    with pytest.raises(ValueError) as e:
        fpdf.FPDF(unit="smiles")

    assert str(e.value) == "Incorrect unit: smiles"

    assert fpdf.FPDF(unit="pt").k == pytest.approx(1)
    assert fpdf.FPDF(unit="mm").k == pytest.approx(2.83464566929)
    assert fpdf.FPDF(unit="cm").k == pytest.approx(28.3464566929)
    assert fpdf.FPDF(unit="in").k == pytest.approx(72)


def test_doc_option_only_core_fonts_encoding():
    pdf = fpdf.FPDF()
    pdf.set_doc_option("core_fonts_encoding", 4)
    assert pdf.core_fonts_encoding == 4

    with pytest.raises(FPDFException) as e:
        pdf.set_doc_option("not core_fonts_encoding", None)

    msg = 'Unknown document option "not core_fonts_encoding"'
    assert str(e.value) == msg


def test_adding_content_after_closing():
    pdf = fpdf.FPDF()
    pdf.set_font("helvetica", size=24)
    pdf.add_page()
    pdf.cell(w=pdf.epw, txt="Hello fpdf2!", align="C")
    pdf.output()
    with pytest.raises(FPDFException) as error:
        pdf.add_page()
    assert (
        str(error.value)
        == "A page cannot be added on a closed document, after calling output()"
    )
    with pytest.raises(FPDFException) as error:
        pdf.cell(w=pdf.epw, txt="Hello again!", align="C")
    assert (
        str(error.value)
        == "Content cannot be added on a closed document, after calling output()"
    )


def test_repeated_calls_to_output(tmp_path):
    pdf = fpdf.FPDF()
    assert_pdf_equal(pdf, HERE / "repeated_calls_to_output.pdf", tmp_path)
    assert_pdf_equal(pdf, HERE / "repeated_calls_to_output.pdf", tmp_path)


def test_unsupported_image_filter_error():
    image_filter = "N/A"
    with pytest.raises(FPDFException) as error:
        get_img_info(img=Image.open(HERE / "flowers.png"), image_filter=image_filter)
    assert str(error.value) == f'Unsupported image filter: "{image_filter}"'


def test_incorrent_number_of_pages_toc():
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.insert_toc_placeholder(lambda a, b: None, 10)
    with pytest.raises(FPDFException):
        pdf.close()
