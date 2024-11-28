from pathlib import Path

from test.conftest import ensure_exec_time_below, ensure_rss_memory_below

from fpdf import FPDF

HERE = Path(__file__).resolve().parent
PNG_FILE_PATHS = list((HERE / "image/png_images/").glob("*.png"))
PNG_FILE_PATHS.extend(
    file_path
    for file_path in (HERE / "image/png_test_suite/").glob("*.png")
    if not file_path.name.startswith("x")
)


@ensure_exec_time_below(seconds=9)
@ensure_rss_memory_below(mib=15)
def test_intense_image_rendering(tmp_path):
    pdf = FPDF()
    for _ in range(2000):
        pdf.add_page()
        for i, png_file_path in enumerate(PNG_FILE_PATHS):
            x = (i % 13) * 16
            y = (i // 13) * 16
            pdf.image(png_file_path, x=x, y=y)
    pdf.output(tmp_path / "out.pdf")
