import contextlib
from pathlib import Path
from test.conftest import assert_pdf_equal, EPOCH, LOREM_IPSUM

import pytest

from fpdf import FPDF
from fpdf.recorder import FPDFRecorder

HERE = Path(__file__).resolve().parent


def init_pdf():
    pdf = FPDF()
    pdf.set_creation_date(EPOCH)
    pdf.set_font("helvetica", size=24)
    pdf.add_page()
    pdf.cell(w=pdf.epw, h=10, text="Hello fpdf2!", align="C")
    return pdf


def test_recorder_rewind_ok(tmp_path):
    pdf = init_pdf()
    recorder = FPDFRecorder(pdf)
    expected = recorder.output()  # close the document as a side-effect
    recorder.rewind()  # in order to un-close the document
    recorder.add_page()
    recorder.cell(w=recorder.epw, h=10, text="Hello again!", align="C")
    recorder.rewind()
    assert_pdf_equal(recorder, expected, tmp_path)


def test_recorder_rewind_twice_ok(tmp_path):
    pdf = init_pdf()
    recorder = FPDFRecorder(pdf)
    expected = recorder.output()  # close the document as a side-effect
    recorder.rewind()  # in order to un-close the document
    recorder.add_page()
    recorder.cell(w=recorder.epw, h=10, text="Hello again!", align="C")
    recorder.rewind()
    assert_pdf_equal(recorder, expected, tmp_path)


def test_recorder_replay_ok(tmp_path):
    recorder = FPDFRecorder(init_pdf())
    recorder.add_page()
    recorder.cell(w=recorder.epw, h=10, text="Hello again!", align="C")
    expected = recorder.output()
    recorder.rewind()
    recorder.replay()
    assert_pdf_equal(recorder, expected, tmp_path)


def test_recorder_override_accept_page_break_ok():
    recorder = FPDFRecorder(init_pdf(), accept_page_break=False)
    assert recorder.accept_page_break is False


def test_recorder_preserve_pages_count():
    pdf = init_pdf()
    pdf.set_y(250)
    assert pdf.pages_count == 1
    with pdf.offset_rendering() as recorder:
        pdf.multi_cell(text=LOREM_IPSUM, w=pdf.epw)
        assert pdf.pages_count == 2
    assert recorder.page_break_triggered
    assert pdf.pages_count == 1


def test_recorder_with_ttf_font(tmp_path):
    pdf = init_pdf()
    pdf.add_font(fname=str(HERE / "fonts" / "Roboto-Regular.ttf"))
    pdf.set_font("Roboto-Regular", size=64)
    pdf.add_page()
    pdf.cell(text="Hello!", align="C")
    recorder = FPDFRecorder(pdf)
    expected = recorder.output()  # close the document as a side-effect
    recorder.rewind()  # in order to un-close the document
    recorder.add_page()
    recorder.cell(w=recorder.epw, h=10, text="Hello again!", align="C")
    recorder.rewind()
    assert_pdf_equal(recorder, expected, tmp_path)


class _CustomContextManager:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return None


def _make_generator():
    return (x for x in ())


@contextlib.contextmanager
def _sample_context_manager():
    yield


@pytest.mark.parametrize(
    "cm_callable",
    [
        _make_generator,
        _sample_context_manager,
        _CustomContextManager,
    ],
    ids=["generator", "generator_context_manager", "custom_context_manager"],
)
def test_recorder_replay_warns_on_context_manager(cm_callable):
    pdf = init_pdf()
    recorder = FPDFRecorder(pdf)
    setattr(pdf, "trigger_cm", cm_callable)
    recorder.trigger_cm()
    with pytest.warns(
        UserWarning,
        match=r"Detected usage of a context manager inside an unbreakable\(\) section",
    ):
        recorder.replay()
