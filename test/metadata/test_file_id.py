from pathlib import Path

from fpdf import FPDF
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_custom_file_id(tmp_path):
    class PDF(FPDF):
        def file_id(self):
            return "<DEADBEEF><DEADBEEF>"

    pdf = PDF()
    assert_pdf_equal(pdf, HERE / "custom_file_id.pdf", tmp_path)


def test_no_file_id(tmp_path):
    class PDF(FPDF):
        def file_id(self):
            return None

    pdf = PDF()
    assert_pdf_equal(pdf, HERE / "no_file_id.pdf", tmp_path)
