from pathlib import Path
from pytest import raises

import qrcode

from fpdf.template import Template, FPDFException

from ..conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_template_nominal_hardcoded(tmp_path):
    """Taken from docs/Templates.md"""
    elements = [
        {
            "name": "company_logo",
            "type": "I",
            "x1": 20,
            "y1": 20,
            "x2": 70,
            "y2": 70,
            "font": None,
            "size": 0,
            "bold": 0,
            "italic": 0,
            "underline": 0,
            "foreground": 0,
            "align": "I",
            "text": "logo",
            "priority": 2,
        },
        {
            "name": "company_name",
            "type": "T",
            "x1": 20,
            "y1": 75,
            "x2": 118,
            "y2": 90,
            "font": "helvetica",
            "size": 12,
            "bold": 1,
            "italic": 0,
            "underline": 0,
            "foreground": 0,
            "align": "I",
            "text": "",
            "priority": 2,
            # multiline is optional, so we test some items without it.
        },
        {
            "name": "multline_text",
            "type": "T",
            "x1": 20,
            "y1": 100,
            "x2": 40,
            "y2": 105,
            "font": "helvetica",
            "size": 12,
            "bold": 0,
            "italic": 0,
            "underline": 0,
            "foreground": 0,
            "background": 0x88FF00,
            "align": "I",
            "text": "Lorem ipsum dolor sit amet, consectetur adipisici elit",
            "priority": 2,
            "multiline": 1,
        },
        {
            "name": "box",
            "type": "B",
            "x1": 15,
            "y1": 15,
            "x2": 185,
            "y2": 260,
            "font": "helvetica",
            "size": 0,
            "bold": 0,
            "italic": 0,
            "underline": 0,
            "foreground": 0,
            "align": "I",
            "text": None,
            "priority": 0,
            "multiline": 0,
        },
        {
            "name": "box_x",
            "type": "B",
            "x1": 95,
            "y1": 15,
            "x2": 105,
            "y2": 25,
            "font": "helvetica",
            "size": 0,
            "bold": 1,
            "italic": 0,
            "underline": 0,
            "foreground": 0,
            "align": "I",
            "text": None,
            "priority": 2,
            "multiline": 0,
        },
        {
            "name": "line1",
            "type": "L",
            "x1": 100,
            "y1": 25,
            "x2": 100,
            "y2": 57,
            "font": "helvetica",
            "size": 0,
            "bold": 0,
            "italic": 0,
            "underline": 0,
            "foreground": 0,
            "align": "I",
            "text": None,
            "priority": 3,
            "multiline": 0,
        },
        {
            "name": "barcode",
            "type": "BC",
            "x1": 20,
            "y1": 246.5,
            "x2": 140,
            "y2": 254,
            "font": "Interleaved 2of5 NT",
            "size": 0.75,
            "bold": 0,
            "italic": 0,
            "underline": 0,
            "foreground": 0,
            "align": "I",
            "text": "200000000001000159053338016581200810081",
            "priority": 3,
            "multiline": 0,
        },
    ]
    tmpl = Template(format="A4", elements=elements, title="Sample Invoice")
    tmpl.add_page()
    tmpl["company_name"] = "Sample Company"
    assert tmpl["company_name"] == "Sample Company"  # testing Template.__getitem__
    tmpl["company_logo"] = HERE.parent.parent / "docs/fpdf2-logo.png"
    assert_pdf_equal(tmpl, HERE / "template_nominal_hardcoded.pdf", tmp_path)


def test_template_nominal_csv(tmp_path):
    """Same data as in docs/Templates.md
    The numeric_text tests for a regression."""
    tmpl = Template(format="A4", title="Sample Invoice")
    tmpl.parse_csv(HERE / "mycsvfile.csv", delimiter=";")
    tmpl.add_page()
    tmpl["empty_fields"] = "empty"
    assert_pdf_equal(tmpl, HERE / "template_nominal_csv.pdf", tmp_path)
    tmpl = Template(format="A4", title="Sample Invoice")
    tmpl.parse_csv(HERE / "mycsvfile.csv", delimiter=";", encoding="utf-8")
    tmpl.add_page()
    tmpl["empty_fields"] = "empty"
    assert_pdf_equal(tmpl, HERE / "template_nominal_csv.pdf", tmp_path)


def test_template_multipage(tmp_path):
    """Testing a Template() populating several pages."""
    tmpl = Template(format="A4", title="Sample Invoice")
    tmpl.parse_csv(HERE / "mycsvfile.csv", delimiter=";")
    tmpl.add_page()
    tmpl["name0"] = "Joe Doe"
    tmpl["title0"] = "Director"
    tmpl.add_page()
    tmpl["name0"] = "Jane Doe"
    tmpl["title0"] = "General Manager"
    tmpl.add_page()
    tmpl["name0"] = "Heinz Mustermann"
    tmpl["title0"] = "Worker"
    assert_pdf_equal(tmpl, HERE / "template_multipage.pdf", tmp_path)


def test_template_badinput(tmp_path):
    """Testing Template() with non-conforming definitions."""
    elements = [{ }]
    with raises(KeyError):
        tmpl = Template(elements=elements)
    elements = [{"name":"n", "type":"X"}]
    with raises(KeyError):
        tmpl = Template(elements=elements)
        tmpl.render()
    elements = [{"name":"n", "type":"T","x1":0,"y1":0,"x2":0,"y2":"x"}]
    with raises(TypeError):
        tmpl = Template(elements=elements)
        tmpl.render()
    tmpl = Template()
    with raises(FPDFException):
        tmpl.parse_csv(HERE / "mandmissing.csv", delimiter=";")
    with raises(ValueError):
        tmpl.parse_csv(HERE / "badint.csv", delimiter=";")
    with raises(ValueError):
        tmpl.parse_csv(HERE / "badfloat.csv", delimiter=";")
    with raises(KeyError):
        tmpl.parse_csv(HERE / "badtype.csv", delimiter=";")
        tmpl.render()


def test_template_code39(tmp_path):  # issue-161
    elements = [
        {
            "name": "code39",
            "type": "C39",
            "x1": 40,
            "y1": 50,
            "y2": 70,
            "size": 1.5,
            "text": "Code 39 barcode",
            "priority": 1,
        },
    ]
    tmpl = Template(format="A4", title="Sample Code 39 barcode", elements=elements)
    tmpl.add_page()
    assert_pdf_equal(tmpl, HERE / "template_code39.pdf", tmp_path)


def test_template_qrcode(tmp_path):  # issue-175
    elements = [
        {
            "name": "barcode_0",
            "type": "I",
            "x1": 50,
            "y1": 50,
            "x2": 100,
            "y2": 100,
            "priority": 0,
            "text": None,
        },
        {
            "name": "barcode_1",
            "type": "I",
            "x1": 150,
            "y1": 150,
            "x2": 200,
            "y2": 200,
            "priority": 0,
            "text": None,
        },
    ]
    tmpl = Template(format="letter", elements=elements)
    tmpl.add_page()
    tmpl["barcode_0"] = qrcode.make("Test 0").get_image()
    tmpl["barcode_1"] = qrcode.make("Test 1").get_image()
    assert_pdf_equal(tmpl, HERE / "template_qrcode.pdf", tmp_path)


def test_rect_background(tmp_path):  # issue-203
    elements = [
        {
            "name": "A rectangle",
            "type": "B",
            "background": 0x80FF00,
            "foreground": 0x80FF00,
            "text": None,
            "priority": 1,
            "x1": 50,
            "y1": 50,
            "x2": 150,
            "y2": 150,
        },
    ]
    tmpl = Template(format="A4", elements=elements)
    tmpl.add_page()
    assert_pdf_equal(tmpl, HERE / "template_rect_background.pdf", tmp_path)


def test_template_justify(tmp_path):  # issue-207
    elements = [
        {
            "name": "paragraph",
            "type": "T",
            "x1": 10,
            "y1": 15,
            "x2": 580,
            "y2": 45,
            "font": "helvetica",
            "size": 16,
            "align": "J",
            "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore"
            " et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi"
            " ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit"
            " esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident,"
            " sunt in culpa qui officia deserunt mollit anim id est laborum.",
            "priority": 1,
            "multiline": True,
        },
    ]
    tmpl = Template(format="A4", unit="pt", elements=elements)
    tmpl.add_page()
    assert_pdf_equal(tmpl, HERE / "template_justify.pdf", tmp_path)
