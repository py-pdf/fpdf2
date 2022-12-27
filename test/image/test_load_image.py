import binascii
from glob import glob
from pathlib import Path

import memunit, pytest

import fpdf

from test.conftest import assert_pdf_equal, time_execution


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


# ensure memory usage does not get too high - this value depends on Python version:
@memunit.assert_lt_mb(141)
def test_share_images_cache(tmp_path):
    images_cache = {}

    def build_pdf_with_big_images():
        pdf = fpdf.FPDF()
        pdf.images = images_cache
        pdf.add_page()
        for img_path in glob(f"{HERE}/png_images/*.png"):
            pdf.image(img_path, h=pdf.eph)
        with (tmp_path / "out.pdf").open("wb") as pdf_file:
            pdf.output(pdf_file)
        # Reset the "usages" count:
        for img in images_cache.values():
            img["usages"] = 0

    with time_execution() as duration:
        build_pdf_with_big_images()
    assert duration.seconds > 0.3

    with time_execution() as duration:
        build_pdf_with_big_images()
    assert duration.seconds < 0.3
