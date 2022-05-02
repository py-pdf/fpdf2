from pathlib import Path
from pytest import raises, warns

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
            "italic": 1,
            "underline": 1,
            "foreground": 0,
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
            "text": "Lorem ipsum dolor sit amet, consectetur adipisici elit",
            "priority": 2,
            "multiline": True,
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
            "text": None,
            "priority": 3,
            "multiline": False,
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
            "text": "200000000001000159053338016581200810081",
            "priority": 3,
            "multiline": False,
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


def test_template_textstyles(tmp_path):
    """Testing bold, italic, underline in template and in tags."""
    elements = [
        {
            "name": "tb",
            "type": "T",
            "x1": 20,
            "y1": 20,
            "x2": 30,
            "y2": 25,
            "text": "text bold",
            "bold": True,
        },
        {
            "name": "ti",
            "type": "T",
            "x1": 20,
            "y1": 30,
            "x2": 30,
            "y2": 35,
            "text": "text italic",
            "italic": True,
        },
        {
            "name": "tu",
            "type": "T",
            "x1": 20,
            "y1": 40,
            "x2": 30,
            "y2": 45,
            "text": "text underline",
            "underline": True,
        },
        {
            "name": "tbiu",
            "type": "T",
            "x1": 20,
            "y1": 50,
            "x2": 30,
            "y2": 55,
            "text": "text all",
            "bold": True,
            "italic": True,
            "underline": True,
        },
        {
            "name": "wb",
            "type": "W",
            "x1": 20,
            "y1": 60,
            "x2": 30,
            "y2": 65,
            "text": "write bold",
            "bold": True,
        },
        {
            "name": "wi",
            "type": "W",
            "x1": 20,
            "y1": 70,
            "x2": 30,
            "y2": 75,
            "text": "write italic",
            "italic": True,
        },
        {
            "name": "wu",
            "type": "W",
            "x1": 20,
            "y1": 80,
            "x2": 30,
            "y2": 85,
            "text": "write underline",
            "underline": True,
        },
        {
            "name": "wbiu",
            "type": "W",
            "x1": 20,
            "y1": 90,
            "x2": 30,
            "y2": 95,
            "text": "write all",
            "bold": True,
            "italic": True,
            "underline": True,
        },
        {
            "name": "tbt",
            "type": "T",
            "x1": 20,
            "y1": 100,
            "x2": 30,
            "y2": 105,
            "text": "<B>text bold tags</B>",
        },
        {
            "name": "tit",
            "type": "T",
            "x1": 20,
            "y1": 110,
            "x2": 30,
            "y2": 115,
            "text": "<I>text italic tags</I>",
        },
        {
            "name": "tut",
            "type": "T",
            "x1": 20,
            "y1": 120,
            "x2": 30,
            "y2": 125,
            "text": "<U>text underline tags</U>",
        },
        {
            "name": "wbt",
            "type": "W",
            "x1": 20,
            "y1": 130,
            "x2": 30,
            "y2": 135,
            "text": "<B>write bold tags</B>",
        },
        {
            "name": "wit",
            "type": "W",
            "x1": 20,
            "y1": 140,
            "x2": 30,
            "y2": 145,
            "text": "<I>write italic tags</I>",
        },
        {
            "name": "wut",
            "type": "W",
            "x1": 20,
            "y1": 150,
            "x2": 30,
            "y2": 155,
            "text": "<U>write underline tags</U>",
        },
    ]
    tmpl = Template(elements=elements)
    tmpl.add_page()
    assert_pdf_equal(tmpl, HERE / "template_textstyles.pdf", tmp_path)


def test_template_item_access():
    """Testing Template() getitem/setitem."""
    elements = [
        {
            "name": "name",
            "type": "T",
            "x1": 20,
            "y1": 75,
            "x2": 30,
            "y2": 90,
            "text": "default text",
        }
    ]
    templ = Template(elements=elements)
    assert ("notthere" in templ) is False
    with raises(FPDFException):
        templ["notthere"] = "something"
    with raises(KeyError):
        # pylint: disable=pointless-statement
        templ["notthere"]
    defaultval = templ["name"]  # find in default data
    assert defaultval == "default text"
    templ["name"] = "new text"
    defaultval = templ["name"]  # find in text data
    assert defaultval == "new text"
    # bad type item access
    with raises(AssertionError):
        # pylint: disable=pointless-statement
        templ[7]
    with raises(AssertionError):
        templ[7] = 8
    with raises(AssertionError):
        # pylint: disable=pointless-statement
        7 in templ


def test_template_badinput():
    """Testing Template() with non-conforming definitions."""
    for arg in (
        "format",
        "orientation",
        "unit",
        "title",
        "author",
        "subject",
        "creator",
        "keywords",
    ):
        with raises(TypeError):
            Template(**{arg: 7})  # numeric instead of str
    elements = [{}]
    with raises(KeyError):
        tmpl = Template(elements=elements)
    elements = [{"name": "n", "type": "X"}]
    with raises(KeyError):
        tmpl = Template(elements=elements)
        tmpl.render()
    elements = [  # missing mandatory x2
        {
            "name": "n",
            "type": "T",
            "x1": 0,
            "y1": 0,
            "y2": 0,
            "text": "Hello!",
        }
    ]
    with raises(KeyError):
        tmpl = Template(elements=elements)
        tmpl["n"] = "hello"
        tmpl.render()
    elements = [  # malformed y2
        {
            "name": "n",
            "type": "T",
            "x1": 0,
            "y1": 0,
            "x2": 0,
            "y2": "x",
            "text": "Hello!",
        }
    ]
    with raises(TypeError):
        tmpl = Template(elements=elements)
        tmpl["n"] = "hello"
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
    with warns(DeprecationWarning):
        Template(infile="whatever")
    with raises(AttributeError):
        with warns(DeprecationWarning):
            tmpl = Template()
            tmpl.render(dest="whatever")


def test_template_code39(tmp_path):  # issue-161
    elements = [
        {
            "name": "code39",
            "type": "C39",
            "x1": 40,
            "y1": 50,
            "y2": 70,
            "size": 1.5,
            "text": "*Code 39 barcode*",
            "priority": 1,
        },
    ]
    tmpl = Template(format="A4", title="Sample Code 39 barcode", elements=elements)
    tmpl.add_page()
    assert_pdf_equal(tmpl, HERE / "template_code39.pdf", tmp_path)


def test_template_code39_legacy(tmp_path):
    # check that old parameters still work
    # This uses the same values as above, and compares to the same file.
    elements = [
        {
            "name": "code39",
            "type": "C39",
            "x": 40,
            "y": 50,
            "w": 1.5,
            "h": 20,
            "text": "*Code 39 barcode*",
            "priority": 1,
        },
    ]
    with warns(DeprecationWarning):
        tmpl = Template(format="A4", title="Sample Code 39 barcode", elements=elements)
        tmpl.add_page()
        assert_pdf_equal(tmpl, HERE / "template_code39.pdf", tmp_path)


def test_template_code39_defaultheight(tmp_path):  # height <= 0 invokes default
    elements = [
        {
            "name": "code39",
            "type": "C39",
            "x1": 40,
            "y1": 50,
            "y2": 50,
            "size": 1.5,
            "text": "*Code 39 barcode*",
            "priority": 1,
        },
    ]
    tmpl = Template(format="A4", title="Sample Code 39 barcode", elements=elements)
    tmpl.add_page()
    assert_pdf_equal(tmpl, HERE / "template_code39_defaultheight.pdf", tmp_path)


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


def test_template_split_multicell():
    elements = [
        {
            "name": "multline_text",
            "type": "T",
            "x1": 20,
            "y1": 100,
            "x2": 60,
            "y2": 105,
            "font": "helvetica",
            "size": 12,
            "text": "Lorem ipsum",
        }
    ]
    text = (
        "Lorem ipsum dolor sit amet, consetetur sadipscing elitr,"
        " sed diam nonumy eirmod tempor invidunt ut labore et dolore"
        " magna aliquyam erat, sed diam voluptua."
    )
    expected = [
        "Lorem ipsum dolor",
        "sit amet, consetetur",
        "sadipscing elitr, sed",
        "diam nonumy",
        "eirmod tempor",
        "invidunt ut labore et",
        "dolore magna",
        "aliquyam erat, sed",
        "diam voluptua.",
    ]
    tmpl = Template(format="A4", unit="pt", elements=elements)
    res = tmpl.split_multicell(text, "multline_text")
    assert res == expected
