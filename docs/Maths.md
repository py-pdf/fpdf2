# Metadata #

`fpdf2` can only insert mathematical formula in the form of **images**.
The following sections will explaing how to generate and embed such images.


## Using Google Charts API ##

Official documentation: [Google Charts Infographics - Mathematical Formulas](https://developers.google.com/chart/infographics/docs/formulas).
Example:

```python
from io import BytesIO
from urllib.parse import quote
from urllib.request import urlopen
from fpdf import FPDF

formula = 'x^n + y^n = a/b'
height = 170
url = f"https://chart.googleapis.com/chart?cht=tx&chs={height}&chl={quote(formula)}"
with urlopen(url) as img_file:
    img = BytesIO(img_file.read())

pdf = FPDF()
pdf.add_page()
pdf.image(img, w=30)
pdf.output("equation-with-gcharts.pdf")
```


## Using Matplotlib ##

Example:

```python
from fpdf import FPDF
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy
from PIL import Image


fig = Figure(figsize=(6, 2), dpi=100)
canvas = FigureCanvas(fig)
axes = fig.gca()
axes.text(0, .5, r"$x^n + y^n = \frac{a}{b}$", fontsize=60)  # LaTeX syntax
axes.axis("off")
canvas.draw()
img = Image.fromarray(numpy.asarray(canvas.buffer_rgba()))

pdf = FPDF()
pdf.add_page()
pdf.image(img, w=30)
pdf.output("equation-with-matplotlib.pdf")
```
