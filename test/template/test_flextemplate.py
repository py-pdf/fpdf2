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
            "name": "e",
            "type": "E",
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
            "background": 0xEEFFFF,
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
            "y2": 15,
            "text": "*987*",
            "size": 1,
            "rotate": 60.0,
        },
        {
            "name": "qrcode",
            "type": "I",
            "x1": 20,
            "y1": 0,
            "x2": 30,
            "y2": 10,
            "rotate": 45,
        },
        {
            "name": "ellipse",
            "type": "E",
            "x1": 45,
            "y1": -10,
            "x2": 65,
            "y2": 0,
            "background": 0x88FFFF,
            "rotate": -45,
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


def test_flextemplate_badinput():
    with raises(TypeError):
        FlexTemplate("NotAnFPDF()Instance")


def test_flextemplate_elements(tmp_path):
    """Check that all elements end up in the right place."""
    grid_elements = (
        dict(name="v02", type="L", x1=20, y1=20, x2=20, y2=280),
        dict(name="v04", type="L", x1=40, y1=20, x2=40, y2=280),
        dict(name="v06", type="L", x1=60, y1=20, x2=60, y2=280),
        dict(name="v08", type="L", x1=80, y1=20, x2=80, y2=280),
        dict(name="v10", type="L", x1=100, y1=20, x2=100, y2=280),
        dict(name="v12", type="L", x1=120, y1=20, x2=120, y2=280),
        dict(name="v14", type="L", x1=140, y1=20, x2=140, y2=280),
        dict(name="v15", type="L", x1=160, y1=20, x2=160, y2=280),
        dict(name="v18", type="L", x1=180, y1=20, x2=180, y2=280),
        dict(name="h02", type="L", x1=20, y1=20, x2=180, y2=20),
        dict(name="h04", type="L", x1=20, y1=40, x2=180, y2=40),
        dict(name="h06", type="L", x1=20, y1=60, x2=180, y2=60),
        dict(name="h08", type="L", x1=20, y1=80, x2=180, y2=80),
        dict(name="h10", type="L", x1=20, y1=100, x2=180, y2=100),
        dict(name="h12", type="L", x1=20, y1=120, x2=180, y2=120),
        dict(name="h14", type="L", x1=20, y1=140, x2=180, y2=140),
        dict(name="h16", type="L", x1=20, y1=160, x2=180, y2=160),
        dict(name="h18", type="L", x1=20, y1=180, x2=180, y2=180),
        dict(name="h20", type="L", x1=20, y1=200, x2=180, y2=200),
        dict(name="h22", type="L", x1=20, y1=220, x2=180, y2=220),
        dict(name="h24", type="L", x1=20, y1=240, x2=180, y2=240),
        dict(name="h26", type="L", x1=20, y1=260, x2=180, y2=260),
        dict(name="h28", type="L", x1=20, y1=280, x2=180, y2=280),
    )
    text_elements = (
        dict(
            name="t",
            type="T",
            x1=0,
            y1=0,
            x2=10,
            y2=4,
            text="text0",
            background=0xFFFF00,
        ),
        dict(
            name="t2",
            type="T",
            x1=20,
            y1=0,
            x2=30,
            y2=4,
            text="text2",
            background=0xFFBB00,
        ),
        dict(
            name="t3",
            type="T",
            x1=00,
            y1=30,
            x2=10,
            y2=34,
            text="text3",
            background=0xBBBF00,
            rotate=10,
        ),
    )
    ml_elements = (
        dict(
            name="ml",
            type="T",
            x1=0,
            y1=0,
            x2=15,
            y2=4,
            text="Lorem ipsum dolor sit amet",
            multiline=True,
        ),
        dict(
            name="ml2",
            type="T",
            x1=20,
            y1=0,
            x2=35,
            y2=4,
            text="Lorem ipsum dolor sit amet",
            multiline=True,
        ),
        dict(
            name="ml3",
            type="T",
            x1=00,
            y1=30,
            x2=15,
            y2=34,
            text="Lorem ipsum dolor sit amet",
            multiline=True,
            rotate=10,
        ),
    )
    write_elements = (
        dict(
            name="w",
            type="W",
            x1=0,
            y1=0,
            x2=10,
            y2=4,
            text="write0",
            background=0xFFFF00,
        ),
        dict(
            name="w2",
            type="W",
            x1=20,
            y1=0,
            x2=30,
            y2=4,
            text="write2",
            background=0xFFBB00,
        ),
        dict(
            name="w3",
            type="W",
            x1=00,
            y1=30,
            x2=10,
            y2=34,
            text="write3",
            background=0xBBBF00,
            rotate=10,
        ),
    )
    line_elements = (
        dict(name="l", type="L", x1=0, y1=0, x2=10, y2=0, size=2),
        dict(name="l2", type="L", x1=20, y1=0, x2=30, y2=0, size=2),
        dict(name="l3", type="L", x1=00, y1=30, x2=10, y2=30, size=2, rotate=10),
    )
    box_elements = (
        dict(name="b", type="B", x1=0, y1=0, x2=10, y2=4),
        dict(name="b2", type="B", x1=20, y1=0, x2=30, y2=4),
        dict(name="b3", type="B", x1=00, y1=30, x2=10, y2=34, rotate=10),
    )
    ellipse_elements = (
        dict(name="e", type="E", x1=0, y1=0, x2=10, y2=4),
        dict(name="e2", type="E", x1=20, y1=0, x2=30, y2=4),
        dict(name="e3", type="E", x1=00, y1=30, x2=10, y2=34, rotate=10),
    )
    bc_elements = (
        dict(name="bc", type="BC", x1=0, y1=0, x2=10, y2=4, text="98", size=1),
        dict(name="bc2", type="BC", x1=20, y1=0, x2=30, y2=4, text="01", size=1),
        dict(
            name="bc3",
            type="BC",
            x1=00,
            y1=30,
            x2=10,
            y2=34,
            text="01",
            size=1,
            rotate=10,
        ),
    )
    c39_elements = (
        dict(name="c39", type="C39", x1=0, y1=0, x2=10, y2=4, text="*xy*", size=0.7),
        dict(name="c39_2", type="C39", x1=20, y1=0, x2=30, y2=4, text="*01*", size=0.7),
        dict(
            name="c39_3",
            type="C39",
            x1=00,
            y1=30,
            x2=10,
            y2=34,
            text="*01*",
            size=0.7,
            rotate=10,
        ),
    )
    img_elements = (
        dict(name="i", type="I", x1=0, y1=0, x2=10, y2=10, size=0.7),
        dict(name="i2", type="I", x1=20, y1=0, x2=30, y2=10, size=0.7),
        dict(name="i3", type="I", x1=00, y1=30, x2=10, y2=40, size=0.7, rotate=10),
    )
    pdf = FPDF()
    grid_t = FlexTemplate(pdf, grid_elements)
    pdf.add_page()
    grid_t.render()
    text_t = FlexTemplate(pdf, text_elements)
    text_t.render(offsetx=40, offsety=40)
    text_t.render(offsetx=40, offsety=100, rotate=30)
    text_t.render(offsetx=80, offsety=200, rotate=45)
    pdf.add_page()
    grid_t.render()
    ml_t = FlexTemplate(pdf, ml_elements)
    ml_t.render(offsetx=40, offsety=40)
    ml_t.render(offsetx=40, offsety=100, rotate=30)
    ml_t.render(offsetx=80, offsety=200, rotate=45)
    pdf.add_page()
    grid_t.render()
    write_t = FlexTemplate(pdf, write_elements)
    write_t.render(offsetx=40, offsety=40)
    write_t.render(offsetx=40, offsety=100, rotate=30)
    write_t.render(offsetx=80, offsety=200, rotate=45)
    pdf.add_page()
    grid_t.render()
    line_t = FlexTemplate(pdf, line_elements)
    line_t.render(offsetx=40, offsety=40)
    line_t.render(offsetx=40, offsety=100, rotate=30)
    line_t.render(offsetx=80, offsety=200, rotate=45)
    pdf.add_page()
    grid_t.render()
    box_t = FlexTemplate(pdf, box_elements)
    box_t.render(offsetx=40, offsety=40)
    box_t.render(offsetx=40, offsety=100, rotate=30)
    box_t.render(offsetx=80, offsety=200, rotate=45)
    pdf.add_page()
    grid_t.render()
    ell_t = FlexTemplate(pdf, ellipse_elements)
    ell_t.render(offsetx=40, offsety=40)
    ell_t.render(offsetx=40, offsety=100, rotate=30)
    ell_t.render(offsetx=80, offsety=200, rotate=45)

    pdf.add_page()
    grid_t.render()
    bc_t = FlexTemplate(pdf, bc_elements)
    bc_t.render(offsetx=40, offsety=40)
    bc_t.render(offsetx=40, offsety=100, rotate=30)
    bc_t.render(offsetx=80, offsety=200, rotate=45)

    pdf.add_page()
    grid_t.render()
    c39_t = FlexTemplate(pdf, c39_elements)
    c39_t.render(offsetx=40, offsety=40)
    c39_t.render(offsetx=40, offsety=100, rotate=30)
    c39_t.render(offsetx=80, offsety=200, rotate=45)

    pdf.add_page()
    grid_t.render()
    img = qrcode.make("Test 0").get_image()
    img_t = FlexTemplate(pdf, img_elements)
    img_t["i"] = img
    img_t["i2"] = img
    img_t["i3"] = img
    img_t.render(offsetx=40, offsety=40)
    img_t["i"] = img
    img_t["i2"] = img
    img_t["i3"] = img
    img_t.render(offsetx=40, offsety=100, rotate=30)
    img_t["i"] = img
    img_t["i2"] = img
    img_t["i3"] = img
    img_t.render(offsetx=80, offsety=200, rotate=45)

    assert_pdf_equal(pdf, HERE / "flextemplate_elements.pdf", tmp_path)
