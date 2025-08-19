import pytest
from pathlib import Path

from fpdf import FPDF
from fpdf.drawing import PaintedPath, PaintComposite
from fpdf.enums import CompositingOperation, PathPaintRule
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def _blue_square():
    p = PaintedPath()
    p.rectangle(10, 10, 50, 50)
    p.style.fill_color = "#0000ff"
    p.style.fill_opacity = 1
    p.style.paint_rule = PathPaintRule.FILL_NONZERO
    return p


def _red_square():
    p = PaintedPath()
    p.rectangle(35, 35, 50, 50)
    p.style.fill_color = "#ff0000"
    p.style.fill_opacity = 1
    p.style.paint_rule = PathPaintRule.FILL_NONZERO
    return p


def _generate_pdf(op: CompositingOperation):
    pdf = FPDF()
    pdf.page_background = (211, 211, 211)
    pdf.add_page()
    with pdf.drawing_context() as gc:
        src = _blue_square()
        dst = _red_square()
        comp = PaintComposite(backdrop=dst, source=src, operation=op)
        gc.add_item(comp)
    return pdf


@pytest.mark.parametrize(
    "op",
    [
        CompositingOperation.CLEAR,
        CompositingOperation.SOURCE_OVER,
        CompositingOperation.DESTINATION_OVER,
        CompositingOperation.SOURCE_IN,
        CompositingOperation.DESTINATION_IN,
        CompositingOperation.SOURCE_OUT,
        CompositingOperation.DESTINATION_OUT,
        CompositingOperation.SOURCE_ATOP,
        CompositingOperation.DESTINATION_ATOP,
        CompositingOperation.XOR,
    ],
)
def test_compositing_operations(op, tmp_path):
    pdf = _generate_pdf(op)
    name = f"compositing_{op.value}.pdf"
    assert_pdf_equal(
        pdf,
        HERE / "generated_pdf" / name,
        tmp_path,
    )
