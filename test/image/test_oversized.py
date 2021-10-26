import logging
from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent
IMAGE_PATH = HERE / "png_images/6c853ed9dacd5716bc54eb59cec30889.png"


def test_oversized_images_warn(caplog):
    pdf = fpdf.FPDF()
    pdf.oversized_images = "WARN"
    pdf.add_page()
    pdf.image(IMAGE_PATH, w=50)
    assert "OVERSIZED" in caplog.text


def test_oversized_images_downscale_simple(caplog, tmp_path):
    caplog.set_level(logging.DEBUG)
    pdf = fpdf.FPDF()
    pdf.oversized_images = "DOWNSCALE"
    pdf.add_page()
    pdf.image(IMAGE_PATH, w=50)
    assert "OVERSIZED: Generated new low-res image" in caplog.text
    assert len(pdf.images) == 2, pdf.images.keys()
    in_use_img_names = _in_use_img_names(pdf)
    assert len(in_use_img_names) == 1, pdf.images.keys()
    assert_pdf_equal(pdf, HERE / "oversized_images_downscale_simple.pdf", tmp_path)


def test_oversized_images_downscale_twice(tmp_path):
    pdf = fpdf.FPDF()
    pdf.oversized_images = "DOWNSCALE"
    pdf.add_page()
    pdf.image(IMAGE_PATH, w=50)
    pdf.image(IMAGE_PATH, w=50)
    assert len(pdf.images) == 2, pdf.images.keys()
    in_use_img_names = _in_use_img_names(pdf)
    assert len(in_use_img_names) == 1, pdf.images.keys()
    assert_pdf_equal(pdf, HERE / "oversized_images_downscale_twice.pdf", tmp_path)


def test_oversized_images_downscaled_and_highres():
    pdf = fpdf.FPDF()
    pdf.oversized_images = "DOWNSCALE"
    pdf.add_page()
    pdf.image(IMAGE_PATH, w=50)
    pdf.image(IMAGE_PATH, w=pdf.epw)
    assert len(pdf.images) == 1, pdf.images.keys()
    # Not calling assert_pdf_equal to avoid storing a large binary (1.4M) in this git repo


def test_oversized_images_highres_and_downscaled():
    pdf = fpdf.FPDF()
    pdf.oversized_images = "DOWNSCALE"
    pdf.add_page()
    pdf.image(IMAGE_PATH, w=pdf.epw)
    pdf.image(IMAGE_PATH, w=50)
    assert len(pdf.images) == 1, pdf.images.keys()
    # Not calling assert_pdf_equal to avoid storing a large binary (1.4M) in this git repo


def test_oversized_images_downscale_biggest_1st(tmp_path):
    pdf = fpdf.FPDF()
    pdf.oversized_images = "DOWNSCALE"
    pdf.add_page()
    pdf.image(IMAGE_PATH, w=50)
    pdf.image(IMAGE_PATH, w=30)
    assert len(pdf.images) == 2, pdf.images.keys()
    in_use_img_names = _in_use_img_names(pdf)
    assert len(in_use_img_names) == 1, pdf.images.keys()
    assert_pdf_equal(pdf, HERE / "oversized_images_downscale_biggest_1st.pdf", tmp_path)


def test_oversized_images_downscale_biggest_2nd(caplog, tmp_path):
    caplog.set_level(logging.DEBUG)
    pdf = fpdf.FPDF()
    pdf.oversized_images = "DOWNSCALE"
    pdf.add_page()
    pdf.image(IMAGE_PATH, w=30)
    pdf.image(IMAGE_PATH, w=50)
    assert "OVERSIZED: Updated low-res image" in caplog.text
    assert len(pdf.images) == 2, pdf.images.keys()
    in_use_img_names = _in_use_img_names(pdf)
    assert len(in_use_img_names) == 1, pdf.images.keys()
    assert_pdf_equal(pdf, HERE / "oversized_images_downscale_biggest_2nd.pdf", tmp_path)


def _in_use_img_names(pdf):
    return [name for name, img in pdf.images.items() if img["usages"]]
