from pathlib import Path

from fpdf import FPDF
from fpdf.actions import GoToAction, GoToRemoteAction, LaunchAction, NamedAction
from fpdf.syntax import DestinationXYZ
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_text_annotation(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=24)
    pdf.text(x=60, y=140, txt="Some text.")
    pdf.text_annotation(
        x=100,
        y=130,
        text="This is a text annotation.",
    )
    assert_pdf_equal(pdf, HERE / "text_annotation.pdf", tmp_path)


def test_named_actions(tmp_path):
    pdf = FPDF()
    pdf.set_font("Helvetica", size=24)
    pdf.add_page()
    pdf.text(x=80, y=140, txt="First page")
    pdf.add_page()
    pdf.underline = True
    for x, y, named_action in (
        (40, 80, "NextPage"),
        (120, 80, "PrevPage"),
        (40, 200, "FirstPage"),
        (120, 200, "LastPage"),
    ):
        pdf.text(x=x, y=y, txt=named_action)
        pdf.add_action(
            NamedAction(named_action),
            x=x,
            y=y - pdf.font_size,
            w=pdf.get_string_width(named_action),
            h=pdf.font_size,
        )
    pdf.underline = False
    pdf.add_page()
    pdf.text(x=80, y=140, txt="Last page")
    assert_pdf_equal(pdf, HERE / "named_actions.pdf", tmp_path)


def test_goto_action(tmp_path):
    pdf = FPDF()
    pdf.set_font("Helvetica", size=24)
    pdf.add_page()
    x, y, text = 80, 140, "GoTo action"
    pdf.text(x=x, y=y, txt=text)
    pdf.add_action(
        GoToAction(dest=DestinationXYZ(page=2).as_str(pdf)),
        x=x,
        y=y - pdf.font_size,
        w=pdf.get_string_width(text),
        h=pdf.font_size,
    )
    pdf.add_page()
    pdf.text(x=80, y=140, txt="Page 2")
    assert_pdf_equal(pdf, HERE / "goto_action.pdf", tmp_path)


def test_goto_remote_action(tmp_path):
    pdf = FPDF()
    pdf.set_font("Helvetica", size=24)
    pdf.add_page()
    x, y, text = 80, 140, "GoTo-Remote action"
    pdf.text(x=x, y=y, txt=text)
    dest = DestinationXYZ(page=1, page_as_obj_id=False).as_str(pdf)
    pdf.add_action(
        GoToRemoteAction("goto_action.pdf", dest=dest),
        x=x,
        y=y - pdf.font_size,
        w=pdf.get_string_width(text),
        h=pdf.font_size,
    )
    assert_pdf_equal(pdf, HERE / "goto_remote_action.pdf", tmp_path)


def test_launch_action(tmp_path):
    pdf = FPDF()
    pdf.set_font("Helvetica", size=24)
    pdf.add_page()
    x, y, text = 80, 140, "Launch action"
    pdf.text(x=x, y=y, txt=text)
    pdf.add_action(
        LaunchAction(file="goto_action.pdf"),
        x=x,
        y=y - pdf.font_size,
        w=pdf.get_string_width(text),
        h=pdf.font_size,
    )
    assert_pdf_equal(pdf, HERE / "launch_action.pdf", tmp_path)
