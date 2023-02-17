# Images #

When rendering an image, its size on the page can be specified in several ways:

* explicit width and height (expressed in user units).
  The image is scaled to those dimensions, unless `keep_aspect_ratio=True` is specified.
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

By default an image is rendered with a resolution of 72 dpi,
but you can control its dimension on the page using the `w=` & `h=` parameters of the [`image()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) method.


## Alpha / transparency ##

`fpdf2` allows to embed images with alpha pixels.

Technically, it is implemented by extracting an `/SMask` from images with transparency,
and inserting it along with the image data in the PDF document. Related code is in the [image_parsing]( https://github.com/PyFPDF/fpdf2/blob/master/fpdf/image_parsing.py) module.


## Assembling images ##
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

### Fitting an image inside a rectangle ###

When you want to scale an image to fill a rectangle, while keeping its aspect ratio,
and ensuring it does **not** overflow the rectangle width nor height in the process,
you can set `w` / `h` and also provide `keep_aspect_ratio=True` to the [`image()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) method.

The following unit test illustrates that:

* [test_image_fit.py](https://github.com/PyFPDF/fpdf2/blob/master/test/image/test_image_fit.py)
* resulting document: [image_fit_in_rect.pdf](https://github.com/PyFPDF/fpdf2/blob/master/test/image/image_fit_in_rect.pdf)

### Blending images ###

You can control the color blending mode of overlapping images.
Valid values for `blend_mode` are `Normal`, `Multiply`, `Screen`, `Overlay`, `Darken`, `Lighten`, `ColorDodge`,
`ColorBurn`, `HardLight`, `SoftLight`, `Difference`, `Exclusion`, `Hue`, `Saturation`, `Color` and `Luminosity`.

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.image("imgA.png", ...)
with pdf.local_context(blend_mode="ColorBurn"):
    pdf.image("imgB.jpg", ...)
pdf.output("blended-images.pdf")
```

Demo of all color blend modes: [blending_images.pdf](https://github.com/PyFPDF/fpdf2/blob/master/test/drawing/generated_pdf/blending_images.pdf)


## Image clipping ##

![](image-clipping.png)

You can select only a portion of the image to render using clipping methods:

* [`rect_clip()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.rect_clip):
    - [example code](https://github.com/PyFPDF/fpdf2/blob/master/test/image/test_image_clipping.py#L10)
    - [resulting PDF](https://github.com/PyFPDF/fpdf2/blob/master/test/image/rect_clip.pdf)
* [`round_clip()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.round_clip):
    - [example code](https://github.com/PyFPDF/fpdf2/blob/master/test/image/test_image_clipping.py#L33)
    - [resulting PDF](https://github.com/PyFPDF/fpdf2/blob/master/test/image/round_clip.pdf)
* [`elliptic_clip()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.elliptic_clip):
    - [example code](https://github.com/PyFPDF/fpdf2/blob/master/test/image/test_image_clipping.py#L56)
    - [resulting PDF](https://github.com/PyFPDF/fpdf2/blob/master/test/image/elliptic_clip.pdf)


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

However, you can easily tell `fpdf2` to embed all images as JPEGs in order to reduce your PDF size,
using [`set_image_filter()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_image_filter):

```python
from fpdf import FPDF

pdf = FPDF()
pdf.set_image_filter("DCTDecode")
pdf.add_page()
pdf.image("docs/fpdf2-logo.png", x=20, y=60)
pdf.output("pdf-with-image.pdf")
```

Beware that "flattening" images into JPEGs this way will fill transparent areas of your images with color (usually black).

The allowed `image_filter` values are listed in the [image_parsing]( https://github.com/PyFPDF/fpdf2/blob/master/fpdf/image_parsing.py) module and are currently:
`FlateDecode` (lossless zlib/deflate compression), `DCTDecode` (lossy compression with JPEG) and `JPXDecode` (lossy compression with JPEG2000).


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

This will fill transparent areas of your images with color (usually black).

_cf._ also documentation on [controlling transparency](Transparency.md).


## Page background ##

_cf._ [Per-page format, orientation and background](PageFormatAndOrientation.md#per-page-format-orientation-and-background)


## Sharing the image cache among FPDF instances ##

Image parsing is often the most CPU & memory intensive step when inserting pictures in a PDF.

If you create several PDF files that use the same illustrations,
you can share the images cache among FPDF instances:

```python
images_cache = {}

for ... # loop
    pdf = FPDF()
    pdf.images = images_cache
    ... # build the PDF
    pdf.output(...)
    # Reset the "usages" count, to avoid ALL images to be inserted in subsequent PDFs:
    for img in images_cache.values():
        img["usages"] = 0
```

This recipe is valid for `fpdf2` v2.5.7+.
For previous versions of `fpdf2`, a _deepcopy_ of `.images` must be made,
(_cf._ [issue #501](https://github.com/PyFPDF/fpdf2/issues/501#issuecomment-1224310277)).
