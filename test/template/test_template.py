from pathlib import Path

from fpdf.template import Template
from ..utilities import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_nominal_hardcoded(tmp_path):
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
            "background": 0,
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
            "background": 0,
            "align": "I",
            "text": "",
            "priority": 2,
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
            "background": 0,
            "align": "I",
            "text": None,
            "priority": 0,
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
            "background": 0,
            "align": "I",
            "text": None,
            "priority": 2,
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
            "background": 0,
            "align": "I",
            "text": None,
            "priority": 3,
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
            "background": 0,
            "align": "I",
            "text": "200000000001000159053338016581200810081",
            "priority": 3,
        },
    ]
    tmpl = Template(format="A4", elements=elements, title="Sample Invoice")
    tmpl.add_page()
    tmpl["company_name"] = "Sample Company"
    tmpl["company_logo"] = HERE.parent.parent / "docs/fpdf2-logo.png"
    assert_pdf_equal(tmpl, HERE / "template_nominal_hardcoded.pdf", tmp_path)


def test_nominal_csv(tmp_path):
    """Taken from docs/Templates.md"""
    tmpl = Template(format="A4", title="Sample Invoice")
    tmpl.parse_csv(HERE / "mycsvfile.csv", delimiter=";")
    tmpl.add_page()
    tmpl["company_name"] = "Sample Company"
    assert_pdf_equal(tmpl, HERE / "template_nominal_csv.pdf", tmp_path)
