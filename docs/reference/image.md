## image ##

```python
fpdf.image(name, x = None, y = None, w = 0, h = 0, type = '', link = '')
```

### Description ###

Puts an image. The size it will take on the page can be specified in different 
ways:

 * explicit width and height (expressed in user units)
 * one explicit dimension, the other being calculated automatically in order to 
   keep the original proportions
 * no explicit dimension, in which case the image is put at 72 dpi.

Supported formats are JPEG, PNG and GIF.

For JPEGs, all flavors are allowed:

  * gray scales
  * true colors (24 bits)
  * CMYK (32 bits)
  
For PNGs, these are allowed:

  * gray scales of at most 8 bits (256 levels)
  * indexed colors
  * true colors (24 bits)
  * alpha channel (_version 1.7 and up_)
  
but this is not supported:

  * interlacing
  
For GIFs: in case of an animated GIF, only the first frame is used.

If a transparent color is defined, it is taken into account.

The format can be specified explicitly or inferred from the file extension.

It is possible to put a link on the image.

**Remark**: if an image is used several times, only one copy is embedded in the
file.

### Parameters ###

name:
> Path or URL of the image.

x:
> Abscissa of the upper-left corner. If not specified or equal to None, the 
> current abscissa is used (_version 1.7.1 and up_).

y:
> Ordinate of the upper-left corner. If not specified or equal to None, the 
> current ordinate is used; moreover, a page break is triggered first if 
> necessary (in case automatic page breaking is enabled) and, after the call,
> the current ordinate is moved to the bottom of the image 
> (_version 1.7.1 and up_).

w:
> Width of the image in the page. If not specified or equal to zero, it is 
> automatically calculated.

h:
> Height of the image in the page. If not specified or equal to zero, it is 
> automatically calculated.

type:
> Image format. Possible values are (case insensitive): JPG, JPEG, PNG and GIF.
> If not specified, the type is inferred from the file extension.

link:
> URL or identifier returned by [add_link](add_link.md).

### See also ###

[add_link](add_link.md), [load_resource](load_resource.md).

