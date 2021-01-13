## set_stretching ##

```python
fpdf.set_stretching(stretching: float)
```

### Description ###

Sets horizontal font stretching. By default, if this method is not called, no stretching is set (equivalent to a value of 100).

### Version ###

Since 1.7.3

### Parameters ###

stretching:
> Define horizontal stretching (scaling) in percents.

### Example ###

```python
# helvetica regular 14
pdf.set_font('helvetica')
# Set stretching to 50%, narrow text
pdf.set_stretching(50.0)
```

### See also ###

[set_font](set_font.md), [set_font_size](set_font_size.md), [get_string_width](get_string_width.md).
