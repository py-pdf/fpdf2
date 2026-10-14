# Patterns and Gradients

_New in [:octicons-tag-24: 2.8.3](https://github.com/py-pdf/fpdf2/blob/master/CHANGELOG.md)_

## Overview

In PDF (Portable Document Format), a **pattern** is a graphical object that can be used to fill (or stroke) shapes. Patterns can include simple color fills, images, or more advanced textures and gradients. 

The **patterns** on PDF documents are grouped on 2 types:
- **Tiling patterns** for any repeating patterns.  
- **Shading patterns** for gradients.  

*fpdf2* provides a context manager `pdf.use_pattern(...)`. Within this context, all drawn shapes or text will use the specified pattern. Once the context ends, drawing reverts to the previously defined color.

## 1. Tiling patterns

Build a colored tile with `create_pattern()`, adding paths or graphics contexts
from the drawing API. The context returns a reusable pattern paint:

```python
from fpdf import FPDF
from fpdf.drawing import PaintedPath

pdf = FPDF()
with pdf.create_pattern(width=10, height=10) as tile:
    motif = PaintedPath().rectangle(0, 0, 4, 4)
    motif.style.fill_color = "#336699"
    motif.style.stroke_color = None
    tile.add_item(motif)

pdf.add_page()
with pdf.use_pattern(tile):
    pdf.rect(20, 20, 80, 50, style="F")

shape = PaintedPath().rectangle(20, 80, 80, 50)
shape.style.fill_color = tile
shape.style.stroke_color = None
with pdf.drawing_context() as drawing:
    drawing.add_item(shape)

pdf.output("tiling.pdf")
```

Tile coordinates use document units and a top-left origin. Contents are clipped
to the tile dimensions. `x_step` and `y_step` optionally change the repetition
spacing; both default to the corresponding tile dimension. `transform` accepts
a drawing `Transform` to position, scale, or rotate the pattern.

Colored tiles capture the current drawing colors and line width when the creation
context starts. Explicit styles on individual motifs override those defaults.

Creation does not require a page and does not draw on the current page. Finish
the creation context before applying the pattern. A finalized tile cannot be
modified or used in another document. Drawing styles accept the pattern as
both `fill_color` and `stroke_color`; `use_pattern()` selects nonstroking paint.
Use drawing styles for text with an explicit fill style.

Each tiling `use_pattern()` block applies to one page. Finish the block before
calling `add_page()` or using layout that triggers an automatic page break.
The same tile can be reused in separate blocks on subsequent pages.

### Uncolored tiling patterns

Use `colored=False` to define a stencil. Its paths and text describe where to
paint; the color is supplied when the pattern is applied. Cell contents must
not specify fill/stroke colors, gradients, other paints, or ordinary images.
Paint composites are currently unsupported inside an uncolored cell.

```python
with pdf.create_pattern(10, 10, colored=False) as stencil:
    dot = PaintedPath().circle(5, 5, 2)
    dot.style.stroke_color = None
    stencil.add_item(dot)

pdf.set_fill_color(40, 120, 180)
with pdf.use_pattern(stencil):  # uses the current fill color
    pdf.rect(20, 140, 80, 50, style="F")

shape = PaintedPath().rectangle(110, 140, 80, 50)
shape.style.fill_color = stencil.with_color("#C04B68")
shape.style.stroke_color = stencil.with_color("#336699")
with pdf.drawing_context() as drawing:
    drawing.add_item(shape)
```

`with_color()` returns a paint without modifying the stencil. It accepts the
same device colors as `set_fill_color()`, including RGB, grayscale, and CMYK.
Drawing styles require an explicitly bound color. A bound paint can also be
passed to `use_pattern()` to override the current fill color.

### SVG patterns

SVG `<pattern>` elements can be referenced with `fill="url(#id)"` or
`stroke="url(#id)"`, including on text. Supported attributes include:

- `patternUnits` and `patternContentUnits`, independently choosing
  `userSpaceOnUse` or `objectBoundingBox`.
- `x`, `y`, `width`, and `height`, including percentages.
- `patternTransform`, `viewBox`, and `preserveAspectRatio`.
- Local `href` and `xlink:href` template inheritance, including forward references.

SVG cells are colored tiles and can include supported drawing content such as
paths, text, raster images, and gradients. Tiles are clipped to their bounds;
`overflow="visible"` is not supported. External pattern templates are not
loaded. Cyclic references are rejected, and template chains use the existing
SVG depth and element limits. A single bounding-box definition can produce
separate PDF tiles for differently sized shapes.

## 2. Gradients

### 2.1 What is a Gradient?

A **gradient** is a progressive blend between two or more colors. In PDF terms, gradients are implemented as *shading patterns*—they allow a smooth color transition based on geometry.

### 2.2 Linear Gradients (axial shading)

A **linear gradient** blends colors along a straight line between two points. For instance, you can define a gradient that goes:

- Left to right  
- Top to bottom  
- Diagonally  

or in any arbitrary orientation by specifying coordinates.

**Example: Creating a Linear Gradient**

```python
from fpdf import FPDF
from fpdf.pattern import LinearGradient

pdf = FPDF()
pdf.add_page()

# Define a linear gradient
linear_grad = LinearGradient(
    pdf,
    from_x=10,                        # Starting x-coordinate
    from_y=0,                         # Starting y-coordinate
    to_x=100,                         # Ending x-coordinate
    to_y=0,                           # Ending y-coordinate
    colors=["#C33764", "#1D2671"]     # Start -> End color
)

with pdf.use_pattern(linear_grad):
    # Draw a rectangle that will be filled with the gradient
    pdf.rect(x=10, y=10, w=100, h=20, style="FD")

pdf.output("pattern_linear_demo.pdf")
```
Result: [pattern_linear_demo.pdf](./pattern_linear_demo.pdf)

**Key Parameters**:

- **from_x, from_y, to_x, to_y**: The coordinates defining the line along which colors will blend.  
- **colors**: A list of colors (hex strings or (R,G,B) tuples). The pattern will interpolate between these colors.  


### 2.3 Radial Gradients

A **radial gradient** blends colors in a circular or elliptical manner from an inner circle to an outer circle. This is perfect for spotlight-like effects or circular color transitions.

**Example: Creating a Radial Gradient**

```python
from fpdf import FPDF
from fpdf.pattern import RadialGradient

pdf = FPDF()
pdf.add_page()

# Define a radial gradient
radial_grad = RadialGradient(
    pdf,
    start_circle_x=30,               # Center X of inner circle
    start_circle_y=30,               # Center Y of inner circle
    start_circle_radius=0,           # Radius of inner circle
    end_circle_x=50,                 # Center X of outer circle
    end_circle_y=50,                 # Center Y of outer circle
    end_circle_radius=25,            # Radius of outer circle
    colors=["#FFFF00", "#FF0000"],   # Inner -> Outer color
)

with pdf.use_pattern(radial_grad):
    # Draw a circle filled with the radial gradient
    pdf.circle(x=50, y=50, radius=25, style="FD")

pdf.output("pattern_radial_demo.pdf")
```
Result: [pattern_radial_demo.pdf](./pattern_radial_demo.pdf)

**Key Parameters**:

- **start_circle_x, start_circle_y, start_circle_radius**: Center and radius of the inner circle.  
- **end_circle_x, end_circle_y, end_circle_radius**: Center and radius of the outer circle.  
- **colors**: A list of colors to be interpolated from inner circle to outer circle.  

## 4. Advanced Usage

### 4.1 Multiple Colors

Both linear and radial gradients support **multiple colors**. If you pass, for example, `colors=["#C33764", "#1D2671", "#FFA500"]`, the resulting pattern will interpolate color transitions through each color in that order.

### 4.2 Extending & Background for Linear Gradients

- **extend_before**: Extends the first color before the starting point (i.e., `x1,y1`).  
- **extend_after**: Extends the last color beyond the end point (i.e., `x2,y2`).  
- **background**: Ensures that if any area is uncovered by the gradient (e.g., a rectangle that is bigger than the gradient line), it’ll show the given background color.

### 4.3 Custom Bounds

For **linear gradients** or **radial gradients**, passing `bounds=[0.2, 0.4, 0.7, ...]` (values between 0 and 1) fine-tunes where each color transition occurs. For instance, if you have 5 colors, you can specify 3 boundary values that partition the color progression among them.

For example, taking a gradient with 5 colors and `bounds=[0.1, 0.8, 0.9]`:
- The transition from color 1 to color 2 starts at the beginning (0%) and ends at 10%
- The transition from color 2 to color 3 starts at 10% and ends at 80%
- The transition from color 3 to color 4 starts at 80% and ends at 90%
- The transition from color 4 to color 5 starts at 90% and goes to the end (100%)

In other words, each boundary value dictates where the color transitions will occur along the total gradient length.