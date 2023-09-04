from pathlib import Path

from test.conftest import ensure_exec_time_below, ensure_rss_memory_below

from fpdf import FPDF

HERE = Path(__file__).resolve().parent


@ensure_exec_time_below(seconds=8)
@ensure_rss_memory_below(mib=8)
def test_intense_image_rendering():
    png_file_paths = []
    for png_file_path in (HERE / "image/png_images/").glob("*.png"):
        png_file_paths.append(str(png_file_path))
    for png_file_path in (HERE / "image/png_test_suite/").glob("*.png"):
        if not png_file_path.name.startswith("x"):
            png_file_paths.append(str(png_file_path))
    pdf = FPDF()
    for _ in range(2000):
        pdf.add_page()
        for i, png_file_path in enumerate(png_file_paths):
            x = (i % 13) * 16
            y = (i // 13) * 16
            pdf.image(png_file_path, x=x, y=y)
