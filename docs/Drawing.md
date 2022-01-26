# Drawing #

The `fpdf.drawing` module provides an API for composing paths out of an
arbitrary sequence of straight lines and curves. This allows fairly low-level
control over the graphics primitives that PDF provides, giving the user the
ability to draw pretty much any vector shape on the page.

The drawing API makes use of features (notably transparency and blending modes)
that were introduced in PDF 1.4. Therefore, use of the features of this module
will automatically set the output version to 1.4 (fpdf normally defaults to
version 1.3. Because the PDF 1.4 specification was originally published in
2001, this version should be compatible with all viewers currently in general
use).

## Getting Started

The easiest way to add a drawing to the document is via `fpdf.FPDF.new_path`.
This is a context manager that takes care of serializing the path to the
document once the context is exited.

Drawings follow the fpdf convention that the origin (that is, coordinate(0, 0)),
is at the top-left corner of the page. The numbers specified to the various
path commands are interpreted in the document units.

```python
import fpdf

pdf = fpdf.FPDF(unit='mm', format=(10, 10))
pdf.add_page()

with pdf.new_path() as path:
    path.move_to(2, 2)
    path.line_to(8, 8)
    path.horizontal_line_relative(-6)
    path.line_relative(6, -6)
    path.close()

pdf.output("drawing-demo.pdf")
```
This example draws an hourglass shape centered on the page:

<p align="center"><img src="drawing/demo-1.webp"/></p>
<p align="center"><a href="drawing/demo-1.pdf">view as PDF</a></p>


## Adding Some Style

Drawings can be styled, changing how they look and blend with other drawings.
Styling can change the color, opacity, stroke shape, and other attributes of a
drawing.

Let's add some color to the above example:

```python
import fpdf

pdf = fpdf.FPDF(unit='mm', format=(10, 10))
pdf.add_page()

with pdf.new_path() as path:
    path.style.fill_color = '#A070D0'
    path.style.stroke_color = fpdf.drawing.gray8(210)
    path.style.stroke_width = 1
    path.style.stroke_opacity = 0.75
    path.style.stroke_join_style = 'round'

    path.move_to(2, 2)
    path.line_to(8, 8)
    path.horizontal_line_relative(-6)
    path.line_relative(6, -6)
    path.close()

pdf.output("drawing-demo.pdf")
```

If you make color choices like these, it's probably not a good idea to quit your
day job to become a graphic designer. Here's what the output should look like:

<p align="center"><img src="drawing/demo-2.webp"/></p>
<p align="center"><a href="drawing/demo-2.pdf">view as PDF</a></p>

## Transforms And You

Transforms provide the ability to manipulate the placement of points within a
path without having to do any pesky math yourself. Transforms are composable
using python's matrix multiplication operator (`@`), so, for example, a
transform that both rotates and scales an object can be create by matrix
multiplying a rotation transform with a scaling transform.

An important thing to note about transforms is that the result is order
dependent, which is to say that something like performing a rotation followed
by scaling will not, in the general case, result in the same output as
performing the same scaling followed by the same rotation.

Additionally, it's not generally possible to deconstruct a composed
transformation (representing an ordered sequence of translations, scaling,
rotations, shearing) back into the sequence of individual transformation
functions that produced it. That's okay, because this isn't important unless
you're trying to do something like animate transforms after they've been
composed, which you can't do in a PDF anyway.

All that said, let's take the example we've been working with for a spin (the
pun is intended, you see, because we're going to rotate the drawing).
Explaining the joke does make it better.

An easy way to apply a transform to a path is through the `path.transform`
property.

```python
import fpdf

pdf = fpdf.FPDF(unit="mm", format=(10, 10))
pdf.add_page()

with pdf.new_path() as path:
    path.style.fill_color = "#A070D0"
    path.style.stroke_color = fpdf.drawing.gray8(210)
    path.style.stroke_width = 1
    path.style.stroke_opacity = 0.75
    path.style.stroke_join_style = "round"
    path.transform = fpdf.drawing.Transform.rotation_d(45).scale(0.707).about(5, 5)

    path.move_to(2, 2)
    path.line_to(8, 8)
    path.horizontal_line_relative(-6)
    path.line_relative(6, -6)

    path.close()

pdf.output("drawing-demo.pdf")
```

<p align="center"><img src="drawing/demo-3.webp"/></p>
<p align="center"><a href="drawing/demo-3.pdf">view as PDF</a></p>

The transform in the above example rotates the path 45 degrees clockwise
and scales it by `1/sqrt(2)` around its center point. This transform could be
equivalently written as:

```python
import fpdf
T = fpdf.drawing.Transform

T.translation(-5, -5) @ T.rotation_d(45) @ T.scaling(0.707) @ T.translation(5, 5)
```

Because all transforms operate on points relative to the origin, if we had
rotated the path without first centering it on the origin, we would have
rotated it partway off of the page. Similarly, the size-reduction from the
scaling would have moved it closer to the origin. By bracketing the transforms
with the two translations, the placement of the drawing on the page is
preserved.

## Clipping Paths

The clipping path is used to define the region that the normal path is actually
painted. This can be used to create drawings that would otherwise be difficult
to produce.

```python
import fpdf

pdf = fpdf.FPDF(unit="mm", format=(10, 10))
pdf.add_page()

clipping_path = fpdf.drawing.ClippingPath()
clipping_path.rectangle(x=2.5, y=2.5, w=5, h=5, rx=1, ry=1)

with pdf.new_path() as path:
    path.style.fill_color = "#A070D0"
    path.style.stroke_color = fpdf.drawing.gray8(210)
    path.style.stroke_width = 1
    path.style.stroke_opacity = 0.75
    path.style.stroke_join_style = "round"

    path.clipping_path = clipping_path

    path.move_to(2, 2)
    path.line_to(8, 8)
    path.horizontal_line_relative(-6)
    path.line_relative(6, -6)

    path.close()

pdf.output("drawing-demo.pdf")
```
<p align="center"><img src="drawing/demo-4.webp"/></p>
<p align="center"><a href="drawing/demo-4.pdf">view as PDF</a></p>

## Next Steps

The presented API style is designed to make it simple to produce shapes
declaratively in your Python scripts. However, paths can just as easily be
created programmatically by creating instances of the
`fpdf.drawing.PaintedPath` for paths and `fpdf.drawing.GraphicsContext` for
groups of paths.

Storing paths in intermediate objects allows reusing them and can open up more
advanced use-cases. The [`fpdf.svg`](SVG.html) SVG converter, for example, is
implemented using the `fpdf.drawing` interface.
