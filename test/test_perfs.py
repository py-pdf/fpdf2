from pathlib import Path

import pytest
from test.conftest import ensure_rss_memory_below

from fpdf import FPDF

HERE = Path(__file__).resolve().parent


@ensure_rss_memory_below(max_in_mib=7)
@pytest.mark.timeout(40)
def test_intense_image_rendering():
    png_file_paths = []
    for png_file_path in (HERE / "image/png_images/").glob("*.png"):
        png_file_paths.append(str(png_file_path))
    for png_file_path in (HERE / "image/png_test_suite/").glob("*.png"):
        if not png_file_path.name.startswith("x"):
            png_file_paths.append(str(png_file_path))
    # Rendering 10 thousands pages in less than 40 seconds:
    pdf = FPDF()
    for _ in range(10000):
        pdf.add_page()
        for i, png_file_path in enumerate(png_file_paths):
            x = (i % 13) * 16
            y = (i // 13) * 16
            pdf.image(png_file_path, x=x, y=y)
