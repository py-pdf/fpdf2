## rect ##

```python
fpdf.rect(x: float, y: float, w: float, h: float, style = '')
```

### Description ###

Outputs a rectangle. It can be drawn (border only), filled (with no border) or 
both.

### Parameters ###

x:
> Abscissa of upper-left corner.

y:
> Ordinate of upper-left corner.

w:
> Width.

h:
> Height.

style:
> Style of rendering. Possible values are:
>>  * `D` or empty string: draw. This is the default value.
>>  * `F`: fill
>>  * `DF` or `FD`: draw and fill

### See also ###

[cell](cell.md), [ellipse](ellipse.md).
