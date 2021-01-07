"""issue65_test.py"""

import unittest
import sys
import os

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.join("..", "..")),
)

import fpdf
import test
from test.utilities import relative_path_to, set_doc_date_0, calculate_hash_of_file


def next_row(pdf):
    pdf.ln()
    pdf.set_y(pdf.get_y() + size + margin)


size = 50
margin = 10


class EllipseTest(unittest.TestCase):
    """ShapeWriterTest"""

    PDFClass = fpdf.FPDF

    def test_ellipse_not_circle(self):
        pdf = self.PDFClass(unit="mm")
        set_doc_date_0(pdf)
        pdf.add_page()

        # Styles
        counter = 0
        for style in ["", "F", "FD", "DF", None]:
            counter += 1
            pdf.ellipse(x=pdf.get_x(), y=pdf.get_y(), w=size / 2, h=size, style=style)
            pdf.set_x(pdf.get_x() + (size / 2) + margin)

            if counter % 3 == 0:
                next_row(pdf)

        outfile = relative_path_to("output.pdf")
        pdf.output(outfile)

        known_good_hash = "169345cb25b662b236d35aa0b473092f"
        self.assertEqual(known_good_hash, calculate_hash_of_file(outfile))
        os.unlink(outfile)

    def test_ellipse_style(self):
        pdf = self.PDFClass(unit="mm")
        set_doc_date_0(pdf)
        pdf.add_page()

        # Styles
        counter = 0
        for style in ["", "F", "FD", "DF", None]:
            counter += 1
            pdf.ellipse(x=pdf.get_x(), y=pdf.get_y(), w=size, h=size, style=style)
            pdf.set_x(pdf.get_x() + size + margin)

            if counter % 3 == 0:
                next_row(pdf)

        outfile = relative_path_to("output1.pdf")
        pdf.output(outfile)

        known_good_hash = "2f08ed8338d7d421fe2a286ef6c00daf"
        self.assertEqual(known_good_hash, calculate_hash_of_file(outfile))
        os.unlink(outfile)

    def test_ellipse_line_width(self):
        pdf = self.PDFClass(unit="mm")
        set_doc_date_0(pdf)
        pdf.add_page()

        # Line Width
        for line_width in [1, 2, 3]:
            pdf.set_line_width(line_width)
            pdf.ellipse(x=pdf.get_x(), y=pdf.get_y(), w=size, h=size, style=None)
            pdf.set_x(pdf.get_x() + size + margin)
        next_row(pdf)
        for line_width in [4, 5, 6]:
            pdf.set_line_width(line_width)
            pdf.ellipse(x=pdf.get_x(), y=pdf.get_y(), w=size, h=size, style=None)
            pdf.set_x(pdf.get_x() + size + margin)
        pdf.set_line_width(0.2)  # reset

        outfile = relative_path_to("output2.pdf")
        pdf.output(outfile)

        known_good_hash = "9151e507484e32ca1577c6002ccafada"
        self.assertEqual(known_good_hash, calculate_hash_of_file(outfile))
        os.unlink(outfile)

    def test_ellipse_draw_color(self):
        pdf = self.PDFClass(unit="mm")
        set_doc_date_0(pdf)
        pdf.add_page()

        # Colors
        pdf.set_line_width(0.5)
        for gray in [70, 140, 210]:
            pdf.set_draw_color(gray)
            pdf.ellipse(x=pdf.get_x(), y=pdf.get_y(), w=size, h=size, style=None)
            pdf.set_x(pdf.get_x() + size + margin)

        outfile = relative_path_to("output3.pdf")
        pdf.output(outfile)

        known_good_hash = "ad08d121648ee2b6e38982cdcce01688"
        self.assertEqual(known_good_hash, calculate_hash_of_file(outfile))
        os.unlink(outfile)

    def test_ellipse_fill_color(self):
        pdf = self.PDFClass(unit="mm")
        set_doc_date_0(pdf)
        pdf.add_page()

        pdf.set_fill_color(240)
        for color in [[230, 30, 180], [30, 180, 30], [30, 30, 70]]:
            pdf.set_draw_color(*color)
            pdf.ellipse(x=pdf.get_x(), y=pdf.get_y(), w=size, h=size, style="FD")
            pdf.set_x(pdf.get_x() + size + margin)

        next_row(pdf)

        outfile = relative_path_to("output4.pdf")
        pdf.output(outfile)

        known_good_hash = "2719bf0278757bb684d5d8e6e9cea5f5"
        self.assertEqual(known_good_hash, calculate_hash_of_file(outfile))
        os.unlink(outfile)


class RectangleTest(unittest.TestCase):
    """RectangleTest"""

    PDFClass = fpdf.FPDF

    def test_rect_not_square(self):
        pdf = self.PDFClass(unit="mm")
        set_doc_date_0(pdf)
        pdf.add_page()

        # Styles
        counter = 0
        for style in ["", "F", "FD", "DF", None]:
            counter += 1
            pdf.rect(x=pdf.get_x(), y=pdf.get_y(), w=size / 2, h=size, style=style)
            pdf.set_x(pdf.get_x() + (size / 2) + margin)

            if counter % 3 == 0:
                next_row(pdf)

        outfile = relative_path_to("output.pdf")
        pdf.output(outfile)
        # print(calculate_hash_of_file(outfile))
        known_good_hash = "462a76e02de625f3b3c70a1f8eef9ebc"
        self.assertEqual(known_good_hash, calculate_hash_of_file(outfile))
        os.unlink(outfile)

    def test_rect_style(self):
        pdf = self.PDFClass(unit="mm")
        set_doc_date_0(pdf)
        pdf.add_page()

        # Styles
        counter = 0
        for style in ["", "F", "FD", "DF", None]:
            counter += 1
            pdf.rect(x=pdf.get_x(), y=pdf.get_y(), w=size, h=size, style=style)
            pdf.set_x(pdf.get_x() + size + margin)

            if counter % 3 == 0:
                next_row(pdf)

        outfile = relative_path_to("output1.pdf")
        pdf.output(outfile)
        # print(calculate_hash_of_file(outfile))
        known_good_hash = "be8e25fb5f4d3b1822c969d1478cef86"
        self.assertEqual(known_good_hash, calculate_hash_of_file(outfile))
        os.unlink(outfile)

    def test_rect_line_width(self):
        pdf = self.PDFClass(unit="mm")
        set_doc_date_0(pdf)
        pdf.add_page()

        # Line Width
        for line_width in [1, 2, 3]:
            pdf.set_line_width(line_width)
            pdf.rect(x=pdf.get_x(), y=pdf.get_y(), w=size, h=size, style=None)
            pdf.set_x(pdf.get_x() + size + margin)
        next_row(pdf)
        for line_width in [4, 5, 6]:
            pdf.set_line_width(line_width)
            pdf.rect(x=pdf.get_x(), y=pdf.get_y(), w=size, h=size, style=None)
            pdf.set_x(pdf.get_x() + size + margin)
        pdf.set_line_width(0.2)  # reset

        outfile = relative_path_to("output2.pdf")
        pdf.output(outfile)
        # print(calculate_hash_of_file(outfile))
        known_good_hash = "b5b9d94230af38f7429ccd73d3e342bb"
        self.assertEqual(known_good_hash, calculate_hash_of_file(outfile))
        os.unlink(outfile)

    def test_rect_draw_color(self):
        pdf = self.PDFClass(unit="mm")
        set_doc_date_0(pdf)
        pdf.add_page()

        # Colors
        pdf.set_line_width(0.5)
        for gray in [70, 140, 210]:
            pdf.set_draw_color(gray)
            pdf.rect(x=pdf.get_x(), y=pdf.get_y(), w=size, h=size, style=None)
            pdf.set_x(pdf.get_x() + size + margin)

        outfile = relative_path_to("output3.pdf")
        pdf.output(outfile)
        # print(calculate_hash_of_file(outfile))
        known_good_hash = "ab22c2b23e19e09387da55fd534d4f4c"
        self.assertEqual(known_good_hash, calculate_hash_of_file(outfile))
        os.unlink(outfile)

    def test_rect_fill_color(self):
        pdf = self.PDFClass(unit="mm")
        set_doc_date_0(pdf)
        pdf.add_page()

        pdf.set_fill_color(240)
        for color in [[230, 30, 180], [30, 180, 30], [30, 30, 70]]:
            pdf.set_draw_color(*color)
            pdf.rect(x=pdf.get_x(), y=pdf.get_y(), w=size, h=size, style="FD")
            pdf.set_x(pdf.get_x() + size + margin)

        next_row(pdf)

        outfile = relative_path_to("output4.pdf")
        pdf.output(outfile)
        # print(calculate_hash_of_file(outfile))
        known_good_hash = "b3a94f3b3c0282dcbbb5f6127b3dfaab"
        self.assertEqual(known_good_hash, calculate_hash_of_file(outfile))
        os.unlink(outfile)


class LineTest(unittest.TestCase):
    """LineTest"""

    PDFClass = fpdf.FPDF

    def test_line(self):
        pdf = self.PDFClass(unit="mm")
        set_doc_date_0(pdf)
        pdf.add_page()

        def draw_diagonal_line(pdf, x, y):
            pdf.line(x, y, x + size, y + (size / 2.0))

        for width in [0.71, 1, 2]:
            pdf.set_line_width(width)
            draw_diagonal_line(pdf, pdf.get_x(), pdf.get_y())
            pdf.set_x(pdf.get_x() + size + margin)
        next_row(pdf)

        for color in [70, 140, 200]:
            pdf.set_draw_color(color)
            draw_diagonal_line(pdf, pdf.get_x(), pdf.get_y())
            pdf.set_x(pdf.get_x() + size + margin)
        next_row(pdf)

        outfile = relative_path_to("line_output.pdf")
        pdf.output(outfile)
        # print(calculate_hash_of_file(outfile))
        known_good_hash = "684bb1210caf57a77021124e1b8a81ef"
        self.assertEqual(known_good_hash, calculate_hash_of_file(outfile))
        os.unlink(outfile)

    def test_dash(self):
        pdf = self.PDFClass(unit="mm")
        set_doc_date_0(pdf)
        pdf.add_page()

        def draw_diagonal_dash(pdf, x, y, *a, **k):
            pdf.dashed_line(x, y, x + size, y + (size / 2.0), *a, **k)

        for width in [0.71, 1, 2]:
            pdf.set_line_width(width)
            draw_diagonal_dash(pdf, pdf.get_x(), pdf.get_y(), margin, margin / 2.0)
            pdf.set_x(pdf.get_x() + size + margin)
        next_row(pdf)

        for color in [70, 140, 200]:
            pdf.set_draw_color(color)
            draw_diagonal_dash(pdf, pdf.get_x(), pdf.get_y(), margin, margin / 2.0)
            pdf.set_x(pdf.get_x() + size + margin)
        next_row(pdf)

        pdf.set_draw_color(0)
        pdf.set_line_width(0.2)
        draw_diagonal_dash(pdf, pdf.get_x(), pdf.get_y(), margin, margin)

        pdf.set_x(pdf.get_x() + size + margin)
        draw_diagonal_dash(pdf, pdf.get_x(), pdf.get_y(), margin / 2.0, margin)

        next_row(pdf)
        pdf.set_line_width(1)
        x, y = pdf.get_x(), pdf.get_y()
        pdf.dashed_line(x, y, x + 100, y + 80, 10, 3)
        pdf.set_x(pdf.get_x() + 20)
        x, y = pdf.get_x(), pdf.get_y()
        pdf.dashed_line(x, y, x + 100, y + 80, 3, 20)
        pdf.set_x(pdf.get_x() + 20)
        x, y = pdf.get_x(), pdf.get_y()
        pdf.dashed_line(x, y, x + 100, y + 80, 6, 17)

        outfile = relative_path_to("line_output1.pdf")
        pdf.output(outfile)
        # print(calculate_hash_of_file(outfile))
        known_good_hash = "4cf8faa9baf3f1835c03fa4ac1e6eb29"
        self.assertEqual(known_good_hash, calculate_hash_of_file(outfile))
        os.unlink(outfile)


if __name__ == "__main__":
    unittest.main()

## Development of demo mostly done as written above.
