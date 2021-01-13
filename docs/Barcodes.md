# Barcodes #

## Code 39 ##

Here is an example on how to generate a [Code 39](https://fr.wikipedia.org/wiki/Code_39) barcode:

```python
pdf = FPDF()
pdf.add_page()
pdf.code39("fpdf2", x=50, y=50, w=4, h=20)
pdf.output("code39.pdf")
```

Output preview:

![](code39.png)


## Interleaved 2 of 5 ##

Here is an example on how to generate an [Interleaved 2 of 5](https://en.wikipedia.org/wiki/Interleaved_2_of_5) barcode:

```python
pdf = FPDF()
pdf.add_page()
pdf.interleaved2of5("1337", x=50, y=50, w=4, h=20)
pdf.output("interleaved2of5.pdf")
```

Output preview:

![](interleaved2of5.png)


## PDF-417 ##

Here is an example on how to generate a [PDF-417](https://fr.wikipedia.org/wiki/PDF-417) barcode
using the `pdf417` lib:

```python
from pdf417 import encode, render_image

pdf = FPDF()
pdf.add_page()
img = render_image(encode("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed non risus. Suspendisse lectus tortor, dignissim sit amet, adipiscing nec, ultricies sed, dolor. Cras elementum ultrices diam."))
pdf.image(img, x=10, y=50)
pdf.output("pdf417.pdf")
```

Output preview:

![](pdf417.png)

## QRCode ##

Here is an example on how to generate a [QR Code](https://en.wikipedia.org/wiki/QR_code)
using the `python-qrcode` lib:

```python
import qrcode

pdf = FPDF()
pdf.add_page()
img = qrcode.make("fpdf2")
pdf.image(img.get_image(), x=50, y=50)
pdf.output("qrcode.pdf")
```

Output preview:

![](qrcode.png)
