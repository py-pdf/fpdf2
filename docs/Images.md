# Images #

When rendering an image, its size on the page can be specified in several ways:

* explicit width and height (expressed in user units)
* one explicit dimension, the other being calculated automatically in order to keep the original proportions
* no explicit dimension, in which case the image is put at 72 dpi

Note that if an image is displayed several times, only one copy is embedded in the file.


## Simple example ##

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.image("docs/fpdf2-logo.png", x=20, y=60)
pdf.output("pdf-with-image.pdf")
```


## Alternative description ##

A textual description of the image can be provided, for accessibility purposes:

```python
pdf.image("docs/fpdf2-logo.png", x=20, y=60, alt_text="Snake logo of the fpdf2 library")
```


## Usage with Pillow ##

You can perform image manipulations using the [Pillow](https://pillow.readthedocs.io/en/stable/) library,
and easily embed the result:

```python
from fpdf import FPDF
from PIL import Image

pdf = FPDF()
pdf.add_page()
img = Image.open("docs/fpdf2-logo.png")
img = img.crop((10, 10, 490, 490)).resize((96, 96), resample=Image.NEAREST)
pdf.image(img, x=80, y=100)
pdf.output("pdf-with-image.pdf")
```


## Image URLs ##

URLs to images can be directly passed to the [`image`](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) method:

```python
pdf.image("https://upload.wikimedia.org/wikipedia/commons/7/70/Example.png")
```


## Image compression ##

By default, `fpdf2` will avoid altering your images :
no image conversion from / to PNG / JPEG is performed.

However, you can easily tell `fpdf2` to convert and embed all images as JPEGs in order to reduce your PDF size:

```python
from fpdf import FPDF

pdf = FPDF()
pdf.set_image_filter("DCTDecode")
pdf.add_page()
pdf.image("docs/fpdf2-logo.png", x=20, y=60)
pdf.output("pdf-with-image.pdf")
```

Beware that "flattening" images this way will convert alpha channels to black.
