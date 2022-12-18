from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal
from PIL import Image


HERE = Path(__file__).resolve().parent


def test_png_indexed_no_transparency(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()

    # P images
    assert Image.open(HERE / "flower1.png").mode == "P", "img.mode is not P"

    pdf.set_image_filter("FlateDecode")
    pdf.image(HERE / "flower1.png", x=10, y=10, w=50, h=50)

    pdf.set_image_filter("JPXDecode")
    pdf.image(HERE / "flower1.png", x=80, y=10, w=50, h=50)

    pdf.set_image_filter("DCTDecode")
    pdf.image(HERE / "flower1.png", x=150, y=10, w=50, h=50)

    # PA images
    img = Image.open(HERE / "flower1.png").convert("PA")
    assert img.mode == "PA", "img.mode is not PA"

    pdf.set_image_filter("FlateDecode")
    pdf.image(img, x=10, y=80, w=50, h=50)

    pdf.set_image_filter("DCTDecode")
    pdf.image(img, x=80, y=80, w=50, h=50)

    pdf.set_image_filter("JPXDecode")
    pdf.image(img, x=150, y=80, w=50, h=50)

    assert_pdf_equal(pdf, HERE / "image_png_indexed_no_transparency.pdf", tmp_path)


def test_png_indexed_transparency(tmp_path):
    def insert_alpha_channel_from_RGBA(img, path_png):
        # open the image as RGBA
        img_RGBA = Image.open(path_png).convert("RGBA")

        # extract the alpha channel
        alpha = img_RGBA.tobytes()[slice(3, None, 4)]

        # create an image that represent the alpha layer
        alpha_layer = Image.frombytes(mode="L", size=img_RGBA.size, data=alpha)

        # put the alpha layer into the original image
        img.putalpha(alpha_layer)

        return img

    pdf = fpdf.FPDF()
    pdf.add_page()

    # P images - info[transparency]: int
    assert isinstance(
        Image.open(HERE / "flower2.png").info["transparency"], int
    ), "info['transparency]' is not int"

    pdf.set_image_filter("FlateDecode")
    pdf.image(HERE / "flower2.png", x=10, y=10, w=50, h=90)

    pdf.set_image_filter("JPXDecode")
    pdf.image(HERE / "flower2.png", x=80, y=10, w=50, h=90)

    pdf.set_image_filter("DCTDecode")
    pdf.image(HERE / "flower2.png", x=150, y=10, w=50, h=90)

    # P images - info[transparency]: bytes
    assert isinstance(
        Image.open(HERE / "flower3.png").info["transparency"], bytes
    ), "info['transparency]' is not bytes"

    pdf.set_image_filter("FlateDecode")
    pdf.image(HERE / "flower3.png", x=10, y=110, w=50, h=90)

    pdf.set_image_filter("JPXDecode")
    pdf.image(HERE / "flower3.png", x=80, y=110, w=50, h=90)

    pdf.set_image_filter("DCTDecode")
    pdf.image(HERE / "flower3.png", x=150, y=110, w=50, h=90)

    # PA images
    img = Image.open(HERE / "flower2.png").convert("PA")
    img = insert_alpha_channel_from_RGBA(img, HERE / "flower2.png")

    pdf.set_image_filter("FlateDecode")
    pdf.image(img, x=10, y=210, w=50, h=90)

    pdf.set_image_filter("DCTDecode")
    pdf.image(img, x=80, y=210, w=50, h=90)

    pdf.set_image_filter("JPXDecode")
    pdf.image(img, x=150, y=210, w=50, h=90)

    assert_pdf_equal(pdf, HERE / "image_png_indexed_transparency.pdf", tmp_path)
