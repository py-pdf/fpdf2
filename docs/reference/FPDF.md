## FPDF ##

```python
fpdf = FPDF(orientation = 'P', unit = 'mm', format='A4')
```

### Description ###

This is the class constructor. It allows setting up the page format, the orientation and the unit of measurement used in all methods (except for font sizes).

### Parameters ###

orientation:
> Default page orientation. Possible values are (case insensitive):
>>    * P or Portrait
>>    * L or Landscape
> 
> The default value is P.

unit:
> User unit. Possible values are:
>>    * pt: point
>>    * mm: millimeter
>>    * cm: centimeter
>>    * in: inch

> A point equals 1/72 of an inch, that is to say about 0.35 mm (an inch being 2.54 cm). This is a very common unit in typography; font sizes are expressed in this unit.
> The default value is mm.

format:
> The format used for pages. It can be any one of the following values (case insensitive):
>>    * A3
>>    * A4
>>    * A5
>>    * Letter
>>    * Legal
> 
> or a tuple containing the width and the height (expressed in the given unit). In portrait orientation, the tuple should be in the order (_width_, _height_), but in landscape orientation, the order should be (_height_, _width_). In either case, the first tuple element is usually less than the second.

> The default value is A4.

### Example ###

Example with a custom 100x150 mm page format:
```python
pdf = FPDF('P', 'mm', (100, 150))
```
