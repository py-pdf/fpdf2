## dashed_line ##

```python
fpdf.dashed_line(x1, y1, x2, y2, dash_length = 1, space_length = 1)
```

### Description ###

Draw a dashed line between two points. Same interface as [line](line.md) except the two parameters dash\_length and space\_length.

### Parameters ###

x1:
> Abscissa of first point

y1:
> Ordinate of first point

x2:
> Abscissa of second point

y2:
> Ordinate of second point

dash\_length:
> Length of the dash

space\_length:
> Length of the space between dashes

### Example ###

```python
# Adds a dashed line beginning at point (10,30), 
#  ending at point (110,30) with a 
#  dash length of 1 and a space length of 10.
pdf.dashed_line(10, 30, 110, 30, 1, 10)
```

### See also ###

[line](line.md).
