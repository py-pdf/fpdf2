# Patterns and Gradients

## Overview

In PDF (Portable Document Format), a **pattern** is a graphical object that can be used to fill (or stroke) shapes. Patterns can include simple color fills, images, or more advanced textures and gradients. 

The **patterns** on PDF documents are grouped on 2 types:
- **Tiling patterns** for any repeating patters.  
- **Shading patterns** for gradients.  

*fpdf2* provides a context manager `pdf.use_pattern(...)`. Within this context, all drawn shapes or text will use the specified pattern. Once the context ends, drawing reverts to the previously defined color.

**At this moment, tiling patterns are not yet supported by `fpdf2`**.

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

pdf.output("linear_gradient_example.pdf")
```

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
    start_circle_x=50,               # Center X of inner circle
    start_circle_y=50,               # Center Y of inner circle
    start_circle_radius=0,           # Radius of inner circle
    end_circle_x=50,                 # Center X of outer circle
    end_circle_y=50,                 # Center Y of outer circle
    end_circle_radius=25,            # Radius of outer circle
    colors=["#FFFF00", "#FF0000"],   # Inner -> Outer color
)

with pdf.use_pattern(radial_grad):
    # Draw a circle filled with the radial gradient
    pdf.circle(x=50, y=50, radius=25, style="FD")

pdf.output("radial_gradient_example.pdf")
```

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
- The transition from color 1 to color 2 start at the beggining (0%) and ends at 10%
- The transition from color 2 to color 3 start at 10% and ends at 80%
- The transition from color 3 to color 4 start at 80% and ends at 90%
- The transition from color 4 to color 5 start at 90% and goes to the end (100%)

In other words, each boundary value dictates where the color transitions will occur along the total gradient length.