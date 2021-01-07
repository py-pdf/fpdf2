## link ##

```python
fpdf.link(x: float, y: float, w: float, h: float, link, alt_text = '')
```

### Description ###

Puts a link on a rectangular area of the page. Text or image links are generally put via [cell](cell.md), [write](write.md) or [image](image.md), but this method can be useful for instance to define a clickable area inside an image.

### Parameters ###

x:
> Abscissa of the upper-left corner of the rectangle.

y:
> Ordinate of the upper-left corner of the rectangle.

w:
> Width of the rectangle.

h:
> Height of the rectangle.

link:
> URL or identifier returned by [add_link](add_link.md).

alt_text:
> An optional string defining the link alternative text `Contents`

### See also ###

[add_link](add_link.md), [cell](cell.md), [write](write.md), [image](image.md).
