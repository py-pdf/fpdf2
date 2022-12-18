from fpdf import FPDF
from fpdf.recorder import FPDFRecorder

from test.conftest import assert_pdf_equal, EPOCH


def init_pdf():
    pdf = FPDF()
    pdf.set_creation_date(EPOCH)
    pdf.set_font("helvetica", size=24)
    pdf.add_page()
    pdf.cell(w=pdf.epw, h=10, txt="Hello fpdf2!", align="C")
    return pdf


def test_recorder_rewind_ok(tmp_path):
    pdf = init_pdf()
    recorder = FPDFRecorder(pdf)
    expected = recorder.output()  # close the document as a side-effect
    recorder.rewind()  # in order to un-close the document
    recorder.add_page()
    recorder.cell(w=recorder.epw, h=10, txt="Hello again!", align="C")
    recorder.rewind()
    assert_pdf_equal(recorder, expected, tmp_path)


def test_recorder_rewind_twice_ok(tmp_path):
    pdf = init_pdf()
    recorder = FPDFRecorder(pdf)
    expected = recorder.output()  # close the document as a side-effect
    recorder.rewind()  # in order to un-close the document
    recorder.add_page()
    recorder.cell(w=recorder.epw, h=10, txt="Hello again!", align="C")
    recorder.rewind()
    assert_pdf_equal(recorder, expected, tmp_path)


def test_recorder_replay_ok(tmp_path):
    recorder = FPDFRecorder(init_pdf())
    recorder.add_page()
    recorder.cell(w=recorder.epw, h=10, txt="Hello again!", align="C")
    expected = recorder.output()
    recorder.rewind()
    recorder.replay()
    assert_pdf_equal(recorder, expected, tmp_path)


def test_recorder_override_accept_page_break_ok():
    recorder = FPDFRecorder(init_pdf(), accept_page_break=False)
    assert recorder.accept_page_break is False
