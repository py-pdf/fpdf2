import binascii
from pathlib import Path

import pytest

import fpdf

from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


def test_load_text_file():
    file = HERE / "__init__.py"
    contents = '"""This package contains image tests"""\n'
    bc = contents.encode()

    resource = fpdf.image_parsing.load_image(str(file)).getvalue()
    # loaded a text file in binary mode, may contain DOS style line endings.
    resource = resource.replace(b"\r\n", b"\n")
    assert bytes(resource) == bc


def test_load_base64_data(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.image(
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAAMFBMVEU0OkArMjhobHEoPUPFEBIuO0L+AAC2FBZ2JyuNICOfGx7xAwT"
        "jCAlCNTvVDA1aLzQ3COjMAAAAVUlEQVQI12NgwAaCDSA0888GCItjn0szWGBJTVoGSCjWs8TleQCQYV95evdxkFT8Kpe0PLDi5WfKd4LUsN5zS1sKFolt8bwAZrCa"
        "GqNYJAgFDEpQAAAzmxafI4vZWwAAAABJRU5ErkJggg=="
    )
    assert_pdf_equal(pdf, HERE / "load_base64_data.pdf", tmp_path)


def test_load_invalid_base64_data():
    pdf = fpdf.FPDF()
    pdf.add_page()
    with pytest.raises(binascii.Error):
        pdf.image("data:image/png;base64,GARBAGE")
