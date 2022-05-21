from pathlib import Path

from fpdf import FPDF
from fpdf.actions import GoToAction, GoToRemoteAction, LaunchAction, NamedAction
from fpdf.enums import AnnotationName
from fpdf.syntax import DestinationXYZ, iobj_ref as pdf_ref
from fpdf.util import object_id_for_page

from test.conftest import assert_pdf_equal, EPOCH, LOREM_IPSUM

HERE = Path(__file__).resolve().parent


def test_text_annotation(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    all_visible_flags = (
        "PRINT",
        "NO_ZOOM",
        "NO_ROTATE",
        "READ_ONLY",
        "LOCKED",
        "TOGGLE_NO_VIEW",
        "LOCKED_CONTENTS",
    )
    for i, flags in enumerate((("PRINT",), all_visible_flags)):
        for j, flag in enumerate(flags):
            pdf.text(x=15 + 50 * i, y=10 + 5 * j, txt=flag)
        for j, name in enumerate(
            (None,)
            + tuple(AnnotationName.__members__.keys())
            + tuple(AnnotationName.__members__.values())
        ):
            pdf.text_annotation(
                x=20 + 50 * i,
                y=50 + 15 * j,
                text=f"This is a {name or 'default'} annotation.",
                name=name,
                flags=flags,
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


def test_goto_next_page_chained(tmp_path):
    "As of 2022, neither Adobe Acrobat nor Sumatra PDF readers trigger those actions"
    pdf = FPDF()
    pdf.set_margin(0)
    pdf.set_font("Helvetica", size=24)
    pdf.add_page()
    pdf.cell(txt="Page 1 (first page)")
    pdf.add_action(
        GoToAction(
            DestinationXYZ(page=1).as_str(pdf),
            next_action=pdf_ref(object_id_for_page(pdf.page + 1)),
        ),
        x=0,
        y=0,
        w=pdf.epw,
        h=pdf.eph,
    )
    pdf.add_page()
    pdf.cell(txt="Page 2")
    pdf.add_action(
        GoToAction(
            DestinationXYZ(page=1).as_str(pdf),
            next_action=pdf_ref(object_id_for_page(pdf.page + 1)),
        ),
        x=0,
        y=0,
        w=pdf.epw,
        h=pdf.eph,
    )
    pdf.add_page()
    pdf.cell(txt="Page 3 (last page)")
    assert_pdf_equal(pdf, HERE / "goto_next_page_chained.pdf", tmp_path)


def test_infinite_loop_with_goto_action(tmp_path):
    """
    Based on Jens Müller talk at NDSS: Processing Dangerous Paths.
    As of 2022, neither Adobe Acrobat nor Sumatra PDF readers seem vulnerable.
    """
    pdf = FPDF()
    pdf.set_margin(0)
    pdf.add_page()
    pdf.add_action(
        GoToAction(
            DestinationXYZ(page=1).as_str(pdf),
            next_action=pdf_ref(object_id_for_page(pdf.page)),
        ),
        x=0,
        y=0,
        w=pdf.epw,
        h=pdf.eph,
    )
    assert_pdf_equal(pdf, HERE / "infinite_loop_with_goto_action.pdf", tmp_path)


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
    with pdf.highlight("Highlight comment", type="Squiggly", modification_time=EPOCH):
        pdf.text(50, 50, "Line 1")
        pdf.set_y(50)
        pdf.multi_cell(w=30, txt="Line 2")
    pdf.cell(w=60, txt="Not highlighted", border=1)
    assert_pdf_equal(pdf, HERE / "highlighted.pdf", tmp_path)


def test_highlighted_over_page_break(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=24)
    pdf.write(txt=LOREM_IPSUM)
    pdf.ln()
    with pdf.highlight("Comment", title="Freddy Mercury", modification_time=EPOCH):
        pdf.write(txt=LOREM_IPSUM)
    assert_pdf_equal(pdf, HERE / "highlighted_over_page_break.pdf", tmp_path)


def test_ink_annotation(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=24)
    pdf.text(50, 50, "Some text")
    pdf.ink_annotation(
        [(40, 50), (70, 25), (100, 50), (70, 75), (40, 50)],
        title="Lucas",
        contents="Hello world!",
    )
    assert_pdf_equal(pdf, HERE / "ink_annotation.pdf", tmp_path)
