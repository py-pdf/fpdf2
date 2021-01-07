## add_page ##

```python
fpdf.add_page(orientation = '', format = '', same = False)
```

### Description ###

Adds a new page to the document. If a page is already present, the 
[footer](footer.md) method is called first to output the footer. Then the page 
is added, the current position set to the top-left corner according to the left
and top margins, and [header](header.md) is called to display the header.

The font which was set before calling is automatically restored. There is no 
need to call [set_font](set_font.md) again if you want to continue with the same 
font. Colors and the line width are also preserved.

The origin of the coordinate system is at the top-left corner and increasing 
ordinates go downwards.

### Parameters ###

orientation:
> Page orientation. Possible values are (case insensitive):
>>    * P or Portrait
>>    * L or Landscape
> 
> The default value is the one passed to the constructor.

format:
> The format used for pages. It can be either one of the following values (case
insensitive):
>>    * A3
>>    * A4
>>    * A5
>>    * Letter
>>    * Legal
> 
> or a tuple containing the width and the height (expressed in the
given unit). In portrait orientation, the tuple should be in the order
(_width_, _height_), but in landscape orientation, the order should be
(_height_, _width_). In either case, the first tuple element is usually less
than the second.
> 
> The default value is the one passed to the constructor.

same:
> True if page must be same as previous. In this case other parameters are
ignored.

### See also ###

[FPDF](FPDF.md), [header](header.md), [footer](footer.md), 
[set_margins](set_margins.md).
