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


## Assembling images ##
`fpdf2` can be an easy solution to assemble images into a PDF.

The following code snippets provide examples of some basic layouts for assembling images into PDF files.

### Side by side images, full height, landscape page ###

```python
from fpdf import FPDF

pdf = FPDF(orientation="landscape")
pdf.set_margin(0)
pdf.add_page()
pdf.image("imgA.png", h=pdf.eph, w=pdf.epw/2)               # full page height, half page width
pdf.set_y(0)
pdf.image("imgB.jpg", h=pdf.eph, w=pdf.epw/2, x=pdf.epw/2)  # full page height, half page width, right half of the page
pdf.output("side-by-side.pdf")
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


## SVG images ##

SVG images passed to the [`image()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) method
will be embedded as [PDF paths](SVG.md):
```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.image("SVG_logo.svg", w=100)
pdf.output("pdf-with-vector-image.pdf")
```


## Retrieve images from URLs ##

URLs to images can be directly passed to the [`image()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) method:

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


## Oversized images detection & downscaling ##

If the resulting PDF size is a concern,
you may want to check if some inserted images are _oversized_,
meaning their resolution is unnecessarily high given the size they are displayed.

There is how to enable this detection mechanism with `fpdf2`:

```python
pdf.oversized_images = "WARN"
```

After setting this property, a `WARNING` log will be displayed whenever an oversized image is inserted.

`fpdf2` is also able to automatically downscale such oversized images:

```python
pdf.oversized_images = "DOWNSCALE"
```

After this, oversized images will be automatically resized, generating `DEBUG` logs like this:
```
OVERSIZED: Generated new low-res image with name=lowres-test.png dims=(319, 451) id=2
```

For finer control, you can set `pdf.oversized_images_ratio` to set the threshold determining if an image is oversized.

If the concepts of "image compression" or "image resolution" are a bit obscure for you,
this article is a recommended reading:
[The 5 minute guide to image quality](https://medium.com/unsplash/the-5-minute-guide-to-image-quality-ad7c3503c845)


## Disabling transparency ##

By default images transparency is preserved:
alpha channels are extracted and converted to an embedded `SMask`.
This can be disabled by setting `.allow_images_transparency`,
_e.g._ to allow compliance with [PDF/A-1](https://en.wikipedia.org/wiki/PDF/A#Description):

```python
from fpdf import FPDF

pdf = FPDF()
pdf.allow_images_transparency = False
pdf.set_font("Helvetica", size=15)
pdf.cell(w=pdf.epw, h=30, txt="Text behind. " * 6)
pdf.image("docs/fpdf2-logo.png", x=0)
pdf.output("pdf-including-image-without-transparency.pdf")
```
