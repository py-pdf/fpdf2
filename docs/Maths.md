# Charts & graphs #

## Charts ##

### Using Matplotlib ###
Before running this example, please install the required dependencies using the command below:
```
pip install fpdf2 matplotlib
```
Example taken from [Matplotlib artist tutorial](https://matplotlib.org/stable/tutorials/intermediate/artists.html):

```python
from fpdf import FPDF
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from PIL import Image

fig = Figure(figsize=(6, 4), dpi=300)
fig.subplots_adjust(top=0.8)
ax1 = fig.add_subplot(211)
ax1.set_ylabel("volts")
ax1.set_title("a sine wave")

t = np.arange(0.0, 1.0, 0.01)
s = np.sin(2 * np.pi * t)
(line,) = ax1.plot(t, s, color="blue", lw=2)

# Fixing random state for reproducibility
np.random.seed(19680801)

ax2 = fig.add_axes([0.15, 0.1, 0.7, 0.3])
n, bins, patches = ax2.hist(
    np.random.randn(1000), 50, facecolor="yellow", edgecolor="yellow"
)
ax2.set_xlabel("time (s)")

# Converting Figure to an image:
canvas = FigureCanvas(fig)
canvas.draw()
img = Image.fromarray(np.asarray(canvas.buffer_rgba()))

pdf = FPDF()
pdf.add_page()
pdf.image(img, w=pdf.epw)  # Make the image full width
pdf.output("matplotlib.pdf")
```

Result:

![](matplotlib.png)

You can also embed a figure as [SVG](SVG.md):

```python
from fpdf import FPDF
import matplotlib.pyplot as plt
import numpy as np

plt.figure(figsize=[2, 2])
x = np.arange(0, 10, 0.00001)
y = x*np.sin(2* np.pi * x)
plt.plot(y)
plt.savefig("figure.svg", format="svg")

pdf = FPDF()
pdf.add_page()
pdf.image("figure.svg")
pdf.output("doc-with-figure.pdf")
```

### Using Pandas ###
The dependencies required for the following examples can be installed using this command:
```
pip install fpdf2 matplotlib pandas
```

Create a plot using [pandas.DataFrame.plot](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.plot.html):
```python
from io import BytesIO
from fpdf import FPDF
import pandas as pd
import matplotlib.pyplot as plt
import io

data = {
    "Unemployment_Rate": [6.1, 5.8, 5.7, 5.7, 5.8, 5.6, 5.5, 5.3, 5.2, 5.2],
    "Stock_Index_Price": [1500, 1520, 1525, 1523, 1515, 1540, 1545, 1560, 1555, 1565],
}

plt.figure()  # Create a new figure object
df = pd.DataFrame(data, columns=["Unemployment_Rate", "Stock_Index_Price"])
df.plot(x="Unemployment_Rate", y="Stock_Index_Price", kind="scatter")

# Converting Figure to an image:
img_buf = BytesIO()  # Create image object
plt.savefig(img_buf, dpi=200)  # Save the image

pdf = FPDF()
pdf.add_page()
pdf.image(img_buf, w=pdf.epw) # Make the image full width
pdf.output("pandas.pdf")
img_buf.close()
```
Result:

![](chart-pandas.png)


Create a table with pandas [DataFrame](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html):
```python
from fpdf import FPDF
import pandas as pd

df = pd.DataFrame(
    {
        "First name": ["Jules", "Mary", "Carlson", "Lucas"],
        "Last name": ["Smith", "Ramos", "Banks", "Cimon"],
        "Age": [34, 45, 19, 31],
        "City": ["San Juan", "Orlando", "Los Angeles", "Saint-Mahturin-sur-Loire"],
    }
)

df = df.applymap(str)  # Convert all data inside dataframe into string type

columns = [list(df)]  # Get list of dataframe columns
rows = df.values.tolist()  # Get list of dataframe rows
data = columns + rows  # Combine columns and rows in one list

pdf = FPDF()
pdf.add_page()
pdf.set_font("Times", size=10)
with pdf.table(borders_layout="MINIMAL",
               cell_fill_color=200,  # grey
               cell_fill_mode="ROWS",
               line_height=pdf.font_size * 2.5,
               text_align="CENTER",
               width=160) as table:
    for data_row in data:
        row = table.row()
        for datum in data_row:
            row.cell(datum)
pdf.output("table_from_pandas.pdf")
```

Result:
![](table-pandas.png)

### Using Plotly ###

Before running this example, please install the required dependencies using the command below:

```
pip install fpdf2 plotly kaleido numpy
```

[kaleido](https://pypi.org/project/kaleido/) is a cross-platform library for generating static images that is used by plotly.

Example taken from [Plotly static image export tutorial](https://plotly.com/python/static-image-export/):

```python
import io
import plotly.graph_objects as go
import numpy as np
from fpdf import FPDF

np.random.seed(1)

N = 100
x = np.random.rand(N)
y = np.random.rand(N)
colors = np.random.rand(N)
sz = np.random.rand(N) * 30

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=x,
    y=y,
    mode="markers",
    marker=go.scatter.Marker(
        size=sz,
        color=colors,
        opacity=0.6,
        colorscale="Viridis"
    )
))
# Convert the figure to png using kaleido
image_data=fig.to_image(format="png", engine="kaleido")
# Create an io.BytesIO object which can be used by FPDF2
image = io.BytesIO(image_data)
pdf = FPDF()
pdf.add_page()
pdf.image(image,w=pdf.epw)  # Width of the image is equal to the width of the page
pdf.output("plotly.pdf")

```

Result:

![](plotly_png.png)

You can also embed a figure as [SVG](SVG.md) but this is not recommended because the text data such as the x and y axis bars might not show as illustrated in the result image because plotly places this data in a svg text tag which is currently [not supported](https://github.com/PyFPDF/fpdf2/issues/537) by FPDF2.

Before running this example, please install the required dependencies:

```
pip install fpdf2 plotly kaleido pandas
```

```python
from fpdf import FPDF
import plotly.express as px

fig = px.bar(x=["a", "b", "c"], y=[1, 3, 2])
fig.write_image("figure.svg")

pdf = FPDF()
pdf.add_page()
pdf.image("figure.svg",w=pdf.epw)
pdf.output("plotly.pdf")
```

Result:

![](plotly_svg.png)


### Using Pygal ###
[Pygal](https://www.pygal.org/en/stable/) is a Python graph plotting library.
You can install it using: `pip install pygal`

`fpdf2` can embed graphs and charts generated using `Pygal` library. However, they cannot be embedded as SVG directly, because `Pygal` inserts `<style>` & `<script>` tags in the images it produces (_cf._ [`pygal/svg.py`](https://github.com/Kozea/pygal/blob/3.0.0/pygal/svg.py#L449)), which is currently not supported by `fpdf2`.
The full list of supported & unsupported SVG features can be found there: [SVG page](SVG.md#supported-svg-features).

You can find documentation on how to convert vector images (SVG) to raster images (PNG, JPG), with a practical example of embedding PyGal charts, there:
[SVG page](SVG.md#converting-vector-graphics-to-raster-graphics).


## Mathematical formulas ##
`fpdf2` can only insert mathematical formula in the form of **images**.
The following sections will explaing how to generate and embed such images.

### Using Google Charts API ###
Official documentation: [Google Charts Infographics - Mathematical Formulas](https://developers.google.com/chart/infographics/docs/formulas).

Example:

```python
from io import BytesIO
from urllib.parse import quote
from urllib.request import urlopen
from fpdf import FPDF

formula = "x^n + y^n = a/b"
height = 170
url = f"https://chart.googleapis.com/chart?cht=tx&chs={height}&chl={quote(formula)}"
with urlopen(url) as img_file:
    img = BytesIO(img_file.read())

pdf = FPDF()
pdf.add_page()
pdf.image(img, w=30)
pdf.output("equation-with-gcharts.pdf")
```

Result:

![](equation-with-gcharts.png)


### Using LaTeX & Matplotlib ###
Matplotlib can render **LaTeX**: [Text rendering With LaTeX](https://matplotlib.org/stable/tutorials/text/usetex.html).

Example:

```python
from io import BytesIO
from fpdf import FPDF
from matplotlib.figure import Figure

fig = Figure(figsize=(6, 2))
gca = fig.gca()
gca.text(0, 0.5, r"$x^n + y^n = \frac{a}{b}$", fontsize=60)
gca.axis("off")

# Converting Figure to a SVG image:
img = BytesIO()
fig.savefig(img, format="svg")

pdf = FPDF()
pdf.add_page()
pdf.image(img, w=100)
pdf.output("equation-with-matplotlib.pdf")
```

Result:

![](equation-with-matplotlib.png)

If you have trouble with the SVG export, you can also render the matplotlib figure as pixels:
```python
from fpdf import FPDF
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from PIL import Image

fig = Figure(figsize=(6, 2), dpi=300)
gca = fig.gca()
gca.text(0, 0.5, r"$x^n + y^n = \frac{a}{b}$", fontsize=60)
gca.axis("off")

canvas = FigureCanvas(fig)
canvas.draw()
img = Image.fromarray(np.asarray(canvas.buffer_rgba()))

...
```
