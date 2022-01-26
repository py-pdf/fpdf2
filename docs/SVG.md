# Scalable Vector Graphics (SVG) #

`fpdf2` supports basic conversion of SVG paths into PDF paths, which can be
inserted into an existing PDF document or used as the contents of a new PDF
document.

Not all SVGs will convert correctly. Please see
[the list of unsupported features](#currently-unsupported-notable-svg-features)
for more information about what to look out for.

## A simple example ##

The following script will create a PDF that consists only of the graphics
contents of the provided SVG file:

```python
import fpdf

svg = fpdf.svg.SVGObject.from_file("my_file.svg")

pdf = fpdf.FPDF(unit="pt", format=(svg.width, svg.height))
pdf.add_page()
svg.draw_to_page(pdf)

pdf.output("my_file.pdf")
```

Because this takes the PDF document size from the source SVG, it does assume
that the width/height of the SVG are specified in absolute units rather than
relative ones (i.e. the top-level `<svg>` tag has something like `width="5cm"`
and not `width=50%`). In this case, if the values are percentages, they will be
interpreted as their literal numeric value (i.e. `100%` would be treated as
`100 pt`). The next example uses `transform_to_page_viewport`, which will scale
an SVG with a percentage based `width` to the pre-defined PDF page size.

The converted SVG object can be returned as an fpdf.drawing.GraphicsContext
collection of drawing directives for more control over how it is rendered:

```python
import fpdf

svg = fpdf.svg.SVGObject.from_file("my_file.svg")

pdf = FPDF(unit="in", format=(8.5, 11))
pdf.add_page()

# We pass align_viewbox=False because we want to perform positioning manually
# after the size transform has been computed.
width, height, paths = svg.transform_to_page_viewport(pdf, align_viewbox=False)
# note: transformation order is important! This centers the svg drawing at the
# origin, rotates it 90 degrees clockwise, and then repositions it to the
# middle of the output page.
paths.transform = paths.transform @ fpdf.drawing.Transform.translation(
    -width / 2, -height / 2
).rotate_d(90).translate(pdf.w / 2, pdf.h / 2)

pdf.draw_path(paths)

pdf.output("my_file.pdf")
```

## Supported SVG Features ##

- groups
- paths
- basic shapes (rect, circle, ellipse, line, polyline, polygon)
- basic cross-references
- stroke & fill coloring and opacity
- basic stroke styling

## Currently Unsupported Notable SVG Features ##

Everything not listed as supported is unsupported, which is a lot. SVG is a
ridiculously complex format that has become increasingly complex as it absorbs
more of the entire browser rendering stack into its specification. However,
there are some pretty commonly used features that are unsupported that may
cause unexpected results (up to and including a normal-looking SVG rendering as
a completely blank PDF). It is very likely that off-the-shelf SVGs will not be
converted fully correctly without some preprocessing.

The biggest unsupported feature is probably:

- CSS styling of SVG elements

In addition to that:

- text/tspan/textPath
- symbols
- markers
- patterns
- gradients
- embedded images or other content (including nested SVGs)
- a lot of attributes
