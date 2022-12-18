#!/usr/bin/env python3
"""Speed benchmark: how much time each lib takes to generate a 10 thousands pages PDF with ~180 distinct images?
  (disclaimer: the author of this benchmark is fpdf2 current maintainer)"""
# Script used in this article: https://chezsoi.org/lucas/blog/fpdf2-5-2-svg-support-and-borb.html
import resource
from decimal import Decimal
from os.path import getsize
from pathlib import Path
from time import perf_counter

from fpdf import FPDF, __version__ as fpdf2_version
from borb.io.write import ascii_art
from borb.pdf.canvas.layout.image.image import Image
from borb.pdf.canvas.layout.page_layout.multi_column_layout import MultiColumnLayout
from borb.pdf.document.document import Document
from borb.pdf.page.page import Page
from borb.pdf.pdf import PDF
from PIL import Image as PILImage


class CustomMultiColumnLayoutWith(MultiColumnLayout):
    """
    Custom subclass allowing us to specify a custom inter-column margin width.
    Suggested as a feature in this PR: https://github.com/jorisschellekens/borb/pull/96
    """

    def __init__(self, *args, gutter_width, **kwargs):
        super().__init__(*args, **kwargs)
        if gutter_width is None:
            gutter_width = 0.05
        self._inter_column_margin = self._page_width * Decimal(gutter_width)
        self._column_width = (
            self._page_width
            - Decimal(2) * self._horizontal_margin
            - (self._number_of_columns - 1) * self._inter_column_margin
        ) / self._number_of_columns


PAGES_COUNT = 1000
HERE = Path(__file__).resolve().parent
if not (HERE / "../test/image/").is_dir():
    raise EnvironmentError(
        "This script depends on PNG files present in fpdf2 repository: it cannot be executed as standalone"
    )
PNG_FILE_PATHS = []
for img_path in (HERE / "../test/image/png_images/").glob("*.png"):
    # We skip the images that make borb crashes:
    if img_path.name != "51a4d21670dc8dfa8ffc9e54afd62f5f.png":
        PNG_FILE_PATHS.append(img_path)
for img_path in (HERE / "../test/image/png_test_suite/").glob("*.png"):
    # We skip the images that make borb crashes:
    if not img_path.name.startswith("x") and not img_path.name.endswith("4a08.png"):
        PNG_FILE_PATHS.append(img_path)


def fpdf2_intense_image_rendering(images):
    pdf = FPDF()
    pdf.set_margin(0)
    width, height = pdf.epw / 13, pdf.eph / 14
    for _ in range(PAGES_COUNT):
        pdf.add_page()
        for i, image in enumerate(images):
            x = (i // 14) * width
            y = (i % 14) * height
            pdf.image(image, x=x, y=y, w=width, h=height)

    memory_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f"Memory usage peak (resource.ru_maxrss): {memory_peak // 1000}MB")
    pdf.output("fpdf2-10000-pages.pdf")
    print(
        f"Generated PDF file size: {getsize('fpdf2-10000-pages.pdf')/1000/1000:.2f}MB"
    )


def borb_intense_image_rendering(images):
    doc = Document()
    width, height = Decimal(595) / 13, Decimal(842) / 14
    for _ in range(PAGES_COUNT):
        page = Page()
        doc.append_page(page)
        layout = CustomMultiColumnLayoutWith(
            page,
            number_of_columns=13,
            gutter_width=0,
            horizontal_margin=0,
            vertical_margin=0,
        )
        for _, image in enumerate(images):
            layout.add(
                Image(
                    image,
                    width=width,
                    height=height,
                    # Zero-margins are currently ignored, resulting in page breaks: https://github.com/jorisschellekens/borb/pull/95
                    margin_bottom=0,
                    margin_left=0,
                    margin_right=0,
                    margin_top=0,
                )
            )

    memory_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f"Memory usage peak (resource.ru_maxrss): {memory_peak // 1000}MB")
    with open("borb-10000-pages.pdf", "wb") as pdf_file:
        PDF.dumps(pdf_file, doc)
    print(f"Generated PDF file size: {getsize('borb-10000-pages.pdf')/1000/1000:.2f}MB")


if __name__ == "__main__":
    print(__doc__)

    ascii_logo_path = Path(ascii_art.__file__).resolve().parent / "ascii_logo.txt"
    with ascii_logo_path.open(encoding="utf8") as text_file:
        borb_version = text_file.readline().strip()
    print(f"Versions tested: {borb_version} VS fpdf2 v{fpdf2_version}")

    print("\nBenchmarking fpdf2...")
    start = perf_counter()
    fpdf2_intense_image_rendering(PNG_FILE_PATHS)
    duration = perf_counter() - start
    print(f"Duration: {duration:.2f}s")

    print("\nBenchmarking borb...")
    start = perf_counter()
    # borb_intense_image_rendering(PNG_FILE_PATHS)  # This crashes:
    # We preload Pillow images to avoid borb raising an OSError: [Errno 24] Too many open files
    pillow_images = [PILImage.open(png_file_path) for png_file_path in PNG_FILE_PATHS]
    borb_intense_image_rendering(pillow_images)
    duration = perf_counter() - start
    print(f"Duration: {duration:.2f}s")
