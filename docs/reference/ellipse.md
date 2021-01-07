## ellipse ##

```python
fpdf.ellipse(x: float, y: float, w: float, h: float, style = '')
```

### Description ###

Outputs an ellipse. It can be drawn (border only), filled (with no border) or 
both. Unlike the PHP version, this function uses the top-left position and 
width and height of the ellipse, like [rect](rect.md), not the center point and 
radius.

### Parameters ###

x:
> Abscissa of upper-left bounging box.

y:
> Ordinate of upper-left bounging box.

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

[cell](cell.md), [rect](rect.md).
