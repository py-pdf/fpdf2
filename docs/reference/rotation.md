## rotation ##

```python
with rotation(angle: float, x: float = None, y: float = None):
    ...
```

### Description ###

This method allows to perform a rotation around a given center.

The rotation affects all elements which are printed inside the indented context
(with the exception of clickable areas).

Remarks:

Only the rendering is altered. The `get_x()` and `get_y()` methods are not affected,
nor the automatic page break mechanism.

### Parameters ###

angle:
> Angle in degrees.

x:
> Abscissa of the rotation center. Default value: current position.

y:
> Ordinate of the rotation center. Default value: current position.

### Example ###
```python
pdf.set_font('Arial', '', 14)
pdf.add_page()
# Rotate all consequenced operations
with rotation(-30):
    pdf.write(5, "Rotated text")
pdf.write(5, "Horizontal text")
```

### See also ###

[set_x](set_x.md), [set_y](set_y.md), [write](write.md)
