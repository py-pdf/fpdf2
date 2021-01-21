from fpdf import FPDF
from test.utilities import assert_pdf_equal, relative_path_to


class TestRotate:
    def test_rotation(self):
        pdf = FPDF()
        pdf.add_page()
        x, y = 60, 60
        img_filepath = relative_path_to(
            "image/png_images/66ac49ef3f48ac9482049e1ab57a53e9.png"
        )
        with pdf.rotation(45, x=x, y=y):
            pdf.image(img_filepath, x=x, y=y)
        pdf.image(img_filepath, x=150, y=150)
        assert_pdf_equal(pdf, "rotation.pdf")
