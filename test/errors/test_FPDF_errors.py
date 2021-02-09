import pytest

import fpdf
from fpdf.errors import FPDFException


def test_add_page_throws_without_page():
    pdf = fpdf.FPDF()
    with pytest.raises(FPDFException) as e:
        pdf.text(1, 2, "ok")

    msg = "No page open, you need to call add_page() first"
    assert str(e.value) == msg


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
    with pytest.raises(FPDFException) as e:
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
    pdf.cell(w=pdf.epw, h=10, txt="Hello fpdf2!", align="C")
    pdf.output()
    with pytest.raises(FPDFException) as error:
        pdf.add_page()
    assert (
        str(error.value)
        == "A page cannot be added on a closed document, after calling output()"
    )
    with pytest.raises(FPDFException) as error:
        pdf.cell(w=pdf.epw, h=10, txt="Hello again!", align="C")
    assert (
        str(error.value)
        == "Content cannot be added on a closed document, after calling output()"
    )
