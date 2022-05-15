# Shapes #

The following code snippets show examples of rendering various shapes.

## Lines ##

Using [`line()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.line) to draw a thin plain orange line:
```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_line_width(0.5)
pdf.set_draw_color(r=255, g=128, b=0)
pdf.line(x1=50, y1=50, x2=150, y2=100)
pdf.output("orange_plain_line.pdf")
```

Drawing a dashed light blue line:
```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_line_width(0.5)
pdf.set_draw_color(r=0, g=128, b=255)
pdf.set_dash_pattern(dash=2, gap=3)
pdf.line(x1=50, y1=50, x2=150, y2=100)
pdf.output("blue_dashed_line.pdf")
```

## Circle ##

Using [`circle()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.circle) to draw a disc filled in pink with a grey outline:
```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_line_width(2)
pdf.set_draw_color(240)
pdf.set_fill_color(r=230, g=30, b=180)
pdf.circle(x=50, y=50, r=50, style="FD")
pdf.output("circle.pdf")
```

## Ellipse ##

Using [`ellipse()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.ellipse), filled in grey with a pink outline:
```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_line_width(2)
pdf.set_draw_color(r=230, g=30, b=180)
pdf.set_fill_color(240)
pdf.ellipse(x=50, y=50, w=100, h=50, style="FD")
pdf.output("ellipse.pdf")
```

## Rectangle ##

Using [`rect()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.rect) to draw nested squares:
```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
for i in range(15):
    pdf.set_fill_color(255 - 15*i)
    pdf.rect(x=5+5*i, y=5+5*i, w=200-10*i, h=200-10*i, style="FD")
pdf.output("squares.pdf")
```

## Polygon ##

Using [`polygon()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.polygon):

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_line_width(2)
pdf.set_fill_color(r=255, g=0, b=0)
coords = ((100, 0), (5, 69), (41, 181), (159, 181), (195, 69))
pdf.polygon(coords, style="DF")
pdf.output("polygon.pdf")
```

## Arc ##

Using [`arc()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.arc):

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_line_width(2)
pdf.set_fill_color(r=255, g=0, b=0)
pdf.arc(x=75, y=75, a=25, b=25, start_angle=30, end_angle=130, style="FD")
pdf.output("arc.pdf")
```

## Solid arc ##

Using [`solid_arc()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.solid_arc):

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_line_width(2)
pdf.set_fill_color(r=255, g=0, b=0)
pdf.solid_arc(x=75, y=75, a=25, b=25, start_angle=30, end_angle=130, style="FD")
pdf.output("solid_arc.pdf")
```
## Regular Star ##

Using [`star()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.star):

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_line_width(0.5)

pdf.set_fill_color(r=255, g=0, b=0)
pdf.star(x=40, y=80, r_in=5, r_out=15, rotateDegrees=0, corners=3, style="FD")

pdf.set_fill_color(r=0, g=255, b=255)
pdf.star(x=80, y=80, r_in=5, r_out=15, rotateDegrees=90, corners=4, style="FD")

pdf.set_fill_color(r=255, g=255, b=0)
pdf.star(x=120, y=80, r_in=5, r_out=15, rotateDegrees=180, corners=5, style="FD")

pdf.set_fill_color(r=255, g=0, b=255)
pdf.star(x=160, y=80, r_in=5, r_out=15, rotateDegrees=270, corners=6, style="FD")
pdf.output("star.pdf")
```
![](star.png)
