from pathlib import Path

from fpdf import FPDF
from fpdf.actions import GoToAction, GoToRemoteAction, LaunchAction, NamedAction
from fpdf.syntax import DestinationXYZ
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_text_annotation(tmp_path):
    pdf = FPDF()
    pdf.set_font("Helvetica", size=24)
    pdf.add_page()
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


def test_highlighted(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=24)
    with pdf.add_highlight("Highlight comment"):
        pdf.text(50, 50, "Line 1")
        pdf.set_y(50)
        pdf.multi_cell(w=30, txt="Line 2")
    pdf.cell(w=60, txt="Not highlighted", border=1)
    assert_pdf_equal(pdf, HERE / "highlighted.pdf", tmp_path)


def test_highlighted_over_page_break(tmp_path):
    text_data = (
        "Lorem ipsum Ut nostrud irure reprehenderit anim nostrud dolore sed "
        "ut Excepteur dolore ut sunt irure consectetur tempor eu tempor "
        "nostrud dolore sint exercitation aliquip velit ullamco esse dolore "
        "mollit ea sed voluptate commodo amet eiusmod incididunt Excepteur "
        "Excepteur officia est ea dolore sed id in cillum incididunt quis ex "
        "id aliqua ullamco reprehenderit cupidatat in quis pariatur ex et "
        "veniam consectetur et minim minim nulla ea in quis Ut in "
        "consectetur cillum aliquip pariatur qui quis sint reprehenderit "
        "anim incididunt laborum dolor dolor est dolor fugiat ut officia do "
        "dolore deserunt nulla voluptate officia mollit elit consequat ad "
        "aliquip non nulla dolor nisi magna consectetur anim sint officia "
        "sit tempor anim do laboris ea culpa eu veniam sed cupidatat in anim "
        "fugiat culpa enim"
    )
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=24)
    pdf.y = 20
    pdf.write(txt=text_data)
    pdf.ln()
    with pdf.add_highlight("Comment", title="Freddy Mercury"):
        pdf.write(txt=text_data)
    assert_pdf_equal(pdf, HERE / "highlighted_over_page_break.pdf", tmp_path)
