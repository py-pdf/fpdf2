from pathlib import Path

from fpdf import FPDF
from fpdf.transitions import (
    SplitTransition,
    BlindsTransition,
    BoxTransition,
    WipeTransition,
    DissolveTransition,
    GlitterTransition,
    FlyTransition,
    PushTransition,
    CoverTransition,
    UncoverTransition,
    FadeTransition,
    Transition,
)
from test.conftest import assert_pdf_equal
import pytest

HERE = Path(__file__).resolve().parent


def test_transitions(tmp_path):
    pdf = FPDF()
    pdf.set_font("Helvetica", size=120)
    pdf.add_page()
    pdf.text(x=40, y=150, txt="Page 0")
    pdf.add_page(transition=SplitTransition("V", "O"))
    pdf.text(x=40, y=150, txt="Page 1")
    pdf.add_page(transition=BlindsTransition("H"))
    pdf.text(x=40, y=150, txt="Page 2")
    pdf.add_page(transition=BoxTransition("I"))
    pdf.text(x=40, y=150, txt="Page 3")
    pdf.add_page(transition=WipeTransition(90))
    pdf.text(x=40, y=150, txt="Page 4")
    pdf.add_page(transition=DissolveTransition())
    pdf.text(x=40, y=150, txt="Page 5")
    pdf.add_page(transition=GlitterTransition(315))
    pdf.text(x=40, y=150, txt="Page 6")
    pdf.add_page(transition=FlyTransition("H"))
    pdf.text(x=40, y=150, txt="Page 7")
    pdf.add_page(transition=PushTransition(270))
    pdf.text(x=40, y=150, txt="Page 8")
    pdf.add_page(transition=CoverTransition(270))
    pdf.text(x=40, y=150, txt="Page 9")
    pdf.add_page(transition=UncoverTransition(270))
    pdf.text(x=40, y=150, txt="Page 10")
    pdf.add_page(transition=FadeTransition())
    pdf.text(x=40, y=150, txt="Page 11")
    assert_pdf_equal(pdf, HERE / "transitions.pdf", tmp_path)


def test_transition_errors():
    pdf = FPDF()
    pdf.set_font("Helvetica", size=120)
    with pytest.raises(NotImplementedError):
        Transition().dict_as_string()

    with pytest.raises(ValueError):
        pdf.add_page(transition=SplitTransition("A", "B"))

    with pytest.raises(ValueError):
        pdf.add_page(transition=BlindsTransition("A"))

    with pytest.raises(ValueError):
        pdf.add_page(transition=BoxTransition("A"))

    with pytest.raises(ValueError):
        pdf.add_page(transition=WipeTransition(-1))

    with pytest.raises(ValueError):
        pdf.add_page(transition=GlitterTransition(-1))

    with pytest.raises(ValueError):
        pdf.add_page(transition=FlyTransition("A", -1))

    with pytest.raises(ValueError):
        pdf.add_page(transition=PushTransition(-1))

    with pytest.raises(ValueError):
        pdf.add_page(transition=CoverTransition(-1))

    with pytest.raises(ValueError):
        pdf.add_page(transition=UncoverTransition(-1))
