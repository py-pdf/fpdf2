# Charts & graphs #

## Charts ##

### Using Matplotlib ###
Before running this example, please install the required dependencies using the command below:
```
pip install fpdf2 matplotlib
```
Example taken from [Matplotlib artist tutorial](https://matplotlib.org/stable/tutorials/intermediate/artists.html):

```python
{% include "../tutorial/matplotlib_demo.py" %}
```

Result:

![](matplotlib.png)

You can also embed a figure as [SVG](SVG.md) ([but there may be some limitations](https://py-pdf.github.io/fpdf2/SVG.html#currently-unsupported-notable-svg-features)):

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
{% include "../tutorial/matplotlib_pandas.py" %}
```

Result:

![](chart-pandas.png)


Create a table with pandas [DataFrame](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html):

```python
{% include "../tutorial/matplotlib_pandas_df.py" %}
```

Result:
![](table-pandas.png)

### Using Ibis ###
The [Ibis](https://ibis-project.org/) library provides a unified interface for analytical workflows across different backends (such as DuckDB, BigQuery, pandas, and more). Ibis table expressions are *lazy* and backend-agnostic; to retrieve the actual data, you need to execute the expression, which typically returns a pandas DataFrame.

This makes it straightforward to use Ibis with `fpdf2`: simply execute your Ibis table expression to get a DataFrame, then render it as a table in your PDF using the same approach as with pandas.

Before running the following example, please install the required dependencies:
```
pip install "ibis-framework[duckdb]" fpdf2 pandas
```

Example: Render an Ibis table as [a table in a PDF document](Tables.md):

```python
from fpdf import FPDF
import ibis
import pandas as pd

# Connect to a DuckDB in-memory database (as an example backend)
con = ibis.duckdb.connect()

# Create a sample table in DuckDB with a SQL INSERT command:
con.raw_sql("""
CREATE TABLE people (
    first_name VARCHAR,
    last_name VARCHAR,
    age INTEGER,
    city VARCHAR
);
INSERT INTO people VALUES
    ('Jules', 'Smith', 34, 'San Juan'),
    ('Mary', 'Ramos', 45, 'Orlando'),
    ('Carlson', 'Banks', 19, 'Los Angeles'),
    ('Lucas', 'Cimon', 31, 'Angers');
""")

# Get an Ibis table expression
t = con.table("people")

# (Optional) Apply Ibis expressions, e.g., filtering or selecting columns
expr = t  # or: t.filter(t.age > 30)

# Execute the Ibis expression to get a pandas DataFrame
df = expr.execute()

# Extract column headers and row data for PDF rendering
COLUMNS = [list(df)]  # column headers
ROWS = df.values.tolist()  # data rows
DATA = COLUMNS + ROWS

pdf = FPDF()
pdf.add_page()
pdf.set_font("Times", size=10)
with pdf.table(
    borders_layout="MINIMAL",
    cell_fill_color=200,  # grey
    cell_fill_mode="ROWS",
    line_height=pdf.font_size * 2.5,
    text_align="CENTER",
    width=160,
) as table:
    for data_row in DATA:
        row = table.row()
        for datum in data_row:
            row.cell(datum)
pdf.output("table_from_ibis.pdf")
```

This approach works with any Ibis backend (DuckDB, pandas, BigQuery, etc.)—just use `.execute()` to get a DataFrame, then render as shown above.

**References:**
- [Ibis documentation](https://ibis-project.org/docs/)
- [fpdf2 documentation: Using Pandas](Maths.md#using-pandas)

### Using Plotly ###

Before running this example, please install the required dependencies using the command below:

```
pip install fpdf2 plotly kaleido numpy
```

[kaleido](https://pypi.org/project/kaleido/) is a cross-platform library for generating static images that is used by plotly.

Example taken from [Plotly static image export tutorial](https://plotly.com/python/static-image-export/):

```python
{% include "../tutorial/plotly_demo.py" %}
```

Result:

![](plotly_png.png)

While you can also embed a figure as [SVG](SVG.md), this is not recommended as text data - such as the x and y axis bars - might not be displayed, because `plotly` places this data in a SVG text tag which is currently [not supported by `fpdf2`](https://github.com/py-pdf/fpdf2/issues/537).

Before running this example, please install the required dependencies:

```
pip install fpdf2 plotly kaleido pandas
```

```python
{% include "../tutorial/plotly_svg.py" %}
```

Result:

![](plotly_svg.png)


### Using Pygal ###
[Pygal](https://www.pygal.org/en/stable/) is a Python graph plotting library.
You can install it using: `pip install pygal`

`fpdf2` can embed graphs and charts generated using `Pygal` library. However, they cannot be embedded as SVG directly, because `Pygal` inserts `<style>` & `<script>` tags in the images it produces (_cf._ [`pygal/svg.py`](https://github.com/Kozea/pygal/blob/3.0.0/pygal/svg.py#L449)), which is currently not supported by `fpdf2`.
The full list of supported & unsupported SVG features can be found there: [SVG page](SVG.md#supported-svg-features).

You can find documentation on how to convert vector images (SVG) to raster images (PNG, JPG), with a practical example of embedding PyGal charts, there:
[SVG page > Converting vector graphics to raster graphics](SVG.md#converting-vector-graphics-to-raster-graphics).


## Mathematical formulas ##
`fpdf2` can only insert mathematical formula in the form of **images**.
The following sections will explain how to generate and embed such images.

### Using Google Charts API ###
Official documentation: [Google Charts Infographics - Mathematical Formulas](https://developers.google.com/chart/infographics/docs/formulas).

Example:

```python
{% include "../tutorial/equation_google_charts.py" %}
```

Result:

![](equation-with-gcharts.png)


### Using LaTeX & Matplotlib ###
Matplotlib can render **LaTeX**: [Text rendering With LaTeX](https://matplotlib.org/stable/tutorials/text/usetex.html).

Example:

```python
{% include "../tutorial/equation_matplotlib.py" %}
```

Result:

![](equation-with-matplotlib.png)

If you have trouble with the SVG export, you can also render the matplotlib figure as pixels:

```python
{% include "../tutorial/equation_matplotlib_raster.py" %}
```
