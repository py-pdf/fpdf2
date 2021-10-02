from pathlib import Path
from pytest import raises
import qrcode
from fpdf.fpdf import FPDF
from fpdf.template import FlexTemplate
from ..conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_flextemplate_offset(tmp_path):
    elements = [
        {
            "name": "box",
            "type": "B",
            "x1": 0,
            "y1": 0,
            "x2": 50,
            "y2": 50,
        },
        {
            "name": "d1",
            "type": "L",
            "x1": 0,
            "y1": 0,
            "x2": 50,
            "y2": 50,
        },
        {
            "name": "d2",
            "type": "L",
            "x1": 0,
            "y1": 50,
            "x2": 50,
            "y2": 0,
        },
        {
            "name": "label",
            "type": "T",
            "x1": 0,
            "y1": 52,
            "x2": 50,
            "y2": 57,
            "text": "Label",
        },
    ]
    pdf = FPDF()
    pdf.add_page()
    templ = FlexTemplate(pdf, elements)
    templ["label"] = "Offset: 50 / 50 mm"
    templ.render(offsetx=50, offsety=50)
    templ["label"] = "Offset: 50 / 120 mm"
    templ.render(offsetx=50, offsety=120)
    templ["label"] = "Offset: 120 / 50 mm, Scale: 0.5"
    templ.render(offsetx=120, offsety=50, scale=0.5)
    templ["label"] = "Offset: 120 / 120 mm, Rotate: 30°, Scale: 0.5"
    templ.render(offsetx=120, offsety=120, rotate=30.0, scale=0.5)
    assert_pdf_equal(pdf, HERE / "flextemplate_offset.pdf", tmp_path)


def test_flextemplate_multipage(tmp_path):

    elements = [
        {
            "name": "box",
            "type": "B",
            "x1": 0,
            "y1": 0,
            "x2": 50,
            "y2": 50,
        },
        {
            "name": "d1",
            "type": "L",
            "x1": 0,
            "y1": 0,
            "x2": 50,
            "y2": 50,
        },
        {
            "name": "d2",
            "type": "L",
            "x1": 0,
            "y1": 50,
            "x2": 50,
            "y2": 0,
        },
        {
            "name": "label",
            "type": "T",
            "x1": 0,
            "y1": 52,
            "x2": 50,
            "y2": 57,
            "text": "Label",
        },
    ]
    pdf = FPDF()
    pdf.add_page()
    tmpl_0 = FlexTemplate(pdf, elements)
    tmpl_0["label"] = "Offset: 50 / 50 mm"
    tmpl_0.render(offsetx=50, offsety=50)
    tmpl_0["label"] = "Offset: 50 / 120 mm"
    tmpl_0.render(offsetx=50, offsety=120)
    tmpl_0["label"] = "Offset: 120 / 50 mm"
    tmpl_0.render(offsetx=120, offsety=50)
    tmpl_0["label"] = "Offset: 120 / 120 mm"
    tmpl_0.render(offsetx=120, offsety=120, rotate=30.0)
    pdf.add_page()
    tmpl_0["label"] = "Offset: 120 / 50 mm"
    tmpl_0.render(offsetx=120, offsety=50)
    tmpl_0["label"] = "Offset: 120 / 120 mm"
    tmpl_0.render(offsetx=120, offsety=120, rotate=30.0)
    tmpl_1 = FlexTemplate(pdf)
    tmpl_1.parse_csv(HERE / "mycsvfile.csv", delimiter=";")
    tmpl_1.render()
    assert_pdf_equal(pdf, HERE / "flextemplate_multipage.pdf", tmp_path)


def test_flextemplate_rotation(tmp_path):
    elements = [
        {
            "name": "box",
            "type": "B",
            "x1": 30,
            "y1": 0,
            "x2": 80,
            "y2": 20,
            "rotate": 10.0,
        },
        {
            "name": "line",
            "type": "L",
            "x1": 0,
            "y1": 0,
            "x2": 50,
            "y2": 20,
            "rotate": 15.0,
        },
        {
            "name": "text!",
            "type": "T",
            "x1": 40,
            "y1": 10,
            "x2": 60,
            "y2": 15,
            "text": "rotatapalooza!",
            "rotate": -15.0,
        },
        {
            "name": "multi",
            "type": "T",
            "x1": 80,
            "y1": 10,
            "x2": 100,
            "y2": 15,
            "text": "Lorem ipsum dolor sit amet, consectetur adipisici elit",
            "rotate": 90.0,
            "multiline": True,
        },
        {
            "name": "write",
            "type": "W",
            "x1": 35,
            "y1": 0,
            "x2": 45,
            "y2": 5,
            "text": "Writing",
            "rotate": -30.0,
        },
        {
            "name": "barcode",
            "type": "BC",
            "x1": 60,
            "y1": 00,
            "x2": 70,
            "y2": 10,
            "text": "123456",
            "size": 1,
            "rotate": 30.0,
        },
        {
            "name": "code39",
            "type": "C39",
            "x1": 80,
            "y1": 10,
            "x2": 70,
            "y2": 15,
            "text": "*987*",
            "size": 1,
            "rotate": 60.0,
        },
        {
            "name": "qrcode",
            "type": "I",
            "x1": 30,
            "y1": 0,
            "x2": 40,
            "y2": 10,
            "rotate": 45,
        },
    ]
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("courier", "", 10)
    templ = FlexTemplate(pdf, elements)
    templ["qrcode"] = qrcode.make("Test 0").get_image()
    templ.render(offsetx=100, offsety=100, rotate=5)
    pdf.add_page()
    scale = 1.2
    for i in range(0, 360, 6):
        templ["qrcode"] = qrcode.make("Test 0").get_image()
        templ.render(offsetx=100, offsety=130, rotate=i, scale=scale)
        scale -= 0.01
    assert_pdf_equal(pdf, HERE / "flextemplate_rotation.pdf", tmp_path)


# pylint: disable=unused-argument
def test_flextemplate_badinput(tmp_path):
    with raises(TypeError):
        FlexTemplate("NotAnFPDF()Instance")
