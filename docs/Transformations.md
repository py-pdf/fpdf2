## skew ##

`skew` creates a skewing transformation of magnitude `ax` in the horizontal axis and `ay` in the vertical axis. The transformation originates from `x`, `y` and will use a default origin unless specified otherwise:

```python
with pdf.skew(ax=0, ay=10):
    pdf.cell(txt="text skewed on the y-axis")
```
![](y_axis_skewed_text.png)

```python
with pdf.skew(ax=10, ay=0):
    pdf.cell(txt="text skewed on the x-axis")
```
![](x_axis_skewed_text.png)

```python
pdf.set_line_width(2)
pdf.set_draw_color(240)
pdf.set_fill_color(r=230, g=30, b=180)
with pdf.skew(ax=-45, ay=0, x=100, y=170):
    pdf.circle(x=100, y=170, r=10, style="FD")
```
![](slanted_circle.png)