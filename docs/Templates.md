# Templates
Templates are a `fpdf2` feature that define predefined documents (like invoices, tax forms, etc.), or parts of such documents, where each element (text, lines, barcodes, etc.) has a fixed position (`x1`, `y1`, `x2`, `y2`), style (`font`, `size`, etc.) and a default text.

These elements can act as placeholders, so the program can change the default text "filling in" the document.

Besides being defined in code, the elements can also be defined in a CSV file, a JSON file, or in a database, so the user can easily adapt the form to his printing needs.

A template is used like a dict, setting its items' values.

There are two approaches to using templates:


## Using Template
The traditional approach is to use the [`Template`](https://py-pdf.github.io/fpdf2/fpdf/template.html#fpdf.template.Template) class.
This class accepts one template definition, and can apply it to each page of a document.
The usage pattern here is:

```python
tmpl = Template(elements=elements)
# first page and content
tmpl.add_page()
tmpl[item_key_01] = "Text 01"
tmpl[item_key_02] = "Text 02"
...

# second page and content
tmpl.add_page()
tmpl[item_key_01] = "Text 11"
tmpl[item_key_02] = "Text 12"
...

# possibly more pages
...

# finalize document and write to file
tmpl.render(outfile="example.pdf")
```

The `Template` class will create and manage its own `FPDF` instance, so you don't need to worry about how it all works together. It also allows to set the page format, title of the document, measuring unit, and other metadata for the PDF file.

Check the dedicated page for the full method signatures: [`Template`](https://py-pdf.github.io/fpdf2/fpdf/template.html#fpdf.template.Template).

You can also check the unit tests in [test_template.py](https://github.com/py-pdf/fpdf2/blob/master/test/template/test_template.py) for more usage examples of `Template`.

Setting text values for specific template items is done by treating the class as a dict, with the name of the item as the key:

```python
Template["company_name"] = "Sample Company"
```


## Using FlexTemplate
When more flexibility is desired, then the [`FlexTemplate`](https://py-pdf.github.io/fpdf2/fpdf/template.html#fpdf.template.FlexTemplate) class comes into play.
In this case, you first need to create your own [`FPDF`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF) instance. You can then pass this to the constructor of one or several `FlexTemplate` instances, and have each of them load a template definition. For any page of the document, you can set text values on a template, and then render it on that page. After rendering, the template will be reset to its default values.
 
```python
from fpdf import FlexTemplate, FPDF

pdf = FPDF()
pdf.add_page()
# One template for the first page
fp_tmpl = FlexTemplate(pdf, elements=fp_elements)
fp_tmpl["item_key_01"] = "Text 01"
fp_tmpl["item_key_02"] = "Text 02"
...
fp_tmpl.render() # add template items to first page

# add some more non-template content to the first page
pdf.polyline(point_list, fill=False, polygon=False)

# second page
pdf.add_page()
# header for the second page
h_tmpl = FlexTemplate(pdf, elements=h_elements)
h_tmpl["item_key_HA"] = "Text 2A"
h_tmpl["item_key_HB"] = "Text 2B"
...
h_tmpl.render() # add header items to second page

# footer for the second page
f_tmpl = FlexTemplate(pdf, elements=f_elements)
f_tmpl["item_key_FC"] = "Text 2C"
f_tmpl["item_key_FD"] = "Text 2D"
...
f_tmpl.render() # add footer items to second page

# other content on the second page
pdf.set_dash_pattern(dash=1, gap=1)
pdf.line(x1, y1, x2, y2):
pdf.set_dash_pattern()

# third page
pdf.add_page()
# header for the third page, just reuse the same template instance after render()
h_tmpl["item_key_HA"] = "Text 3A"
h_tmpl["item_key_HB"] = "Text 3B"
...
h_tmpl.render() # add header items to third page

# footer for the third page
f_tmpl["item_key_FC"] = "Text 3C"
f_tmpl["item_key_FD"] = "Text 3D"
...
f_tmpl.render() # add footer items to third page

# other content on the third page
pdf.rect(x, y, w, h, style=None)

# possibly more pages
pdf.add_page()
...
...

# finally write everything to a file
pdf.output("example.pdf")
```

Evidently, this can end up quite a bit more involved, but there are hardly any limits on how you can combine templated and non-templated content on each page. Just think of the different templates as of building blocks, like configurable rubber stamps, which you can apply in any combination on any page you like.

Of course, you can just as well use a set of full-page templates, possibly differentiating between cover page, table of contents, normal content pages, and an index page, or something along those lines. 

And here's how you can use a template several times on one page (and by extension, several times on several pages). When rendering with an `offsetx` and/or `offsety` argument, the contents of the template will end up in a different place on the page. A `rotate` argument will change its orientation, rotated around the origin of the template. The pivot of the rotation is the offset location. And finally, a `scale` argument allows you to insert the template larger or smaller than it was defined.

```python
from fpdf import FlexTemplate, FPDF

pdf = FPDF()
pdf.add_page()
templ = FlexTemplate(pdf, [
    {"name":"box", "type":"B", "x1":0, "y1":0, "x2":50, "y2":50,},
    {"name":"d1", "type":"L", "x1":0, "y1":0, "x2":50, "y2":50,},
    {"name":"d2", "type":"L", "x1":0, "y1":50, "x2":50, "y2":0,},
    {"name":"label", "type":"T", "x1":0, "y1":52, "x2":50, "y2":57, "text":"Label",},
])
templ["label"] = "Offset: 50 / 50 mm"
templ.render(offsetx=50, offsety=50)
templ["label"] = "Offset: 50 / 120 mm"
templ.render(offsetx=50, offsety=120)
templ["label"] = "Offset: 120 / 50 mm, Scale: 0.5"
templ.render(offsetx=120, offsety=50, scale=0.5)
templ["label"] = "Offset: 120 / 120 mm, Rotate: 30°, Scale=0.5"
templ.render(offsetx=120, offsety=120, rotate=30.0, scale=0.5)
pdf.output("example.pdf")
```

Check the dedicated page for the full method signatures: [`FlexTemplate`](https://py-pdf.github.io/fpdf2/fpdf/template.html#fpdf.template.FlexTemplate).

You can also check the unit tests in [test_flextemplate.py](https://github.com/py-pdf/fpdf2/blob/master/test/template/test_flextemplate.py) for more usage examples of `FlexTemplate`.

The dict syntax for setting text values is the same as above:

```python
FlexTemplate["company_name"] = "Sample Company"
```


## Details - Template definition
A template definition consists of a number of elements, which have the following properties
(columns in a CSV, items in a dict, name/value pairs in a JSON object, fields in a database).
Dimensions (except font size, which always uses points) are given in user defined units (default: mm).
Those are the units that can be specified when creating a [`Template`](https://py-pdf.github.io/fpdf2/fpdf/template.html#fpdf.template.Template)
or a [`FPDF`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF) instance.

* **`name`**: placeholder identification (unique text string)
    * _mandatory_
* **`type`**:
    * **`T`**: Text - places one or several lines of text on the page
    * **`L`**: Line - draws a line from `x1`/`y1` to `x2`/`y2`
    * **`I`**: Image - positions and scales an image into the bounding box
    * **`B`**: Box - draws a rectangle around the bounding box
    * **`E`**: Ellipse - draws an ellipse inside the bounding box
    * **`BC`**: Barcode - inserts an [Interleaved 2 of 5](http://127.0.0.1:8000/fpdf2/Barcodes.html#interleaved-2-of-5) type barcode
    * **`C39`**: Code 39 - inserts a [Code 39](http://127.0.0.1:8000/fpdf2/Barcodes.html#code-39) type barcode
    * **`W`**: "Write" - uses the [`FPDF.write()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write) method to add text to the page
    * _mandatory_
* **`x1, y1, x2, y2`**: top-left, bottom-right coordinates, defining a bounding box in most cases
    * for multiline text, this is the bounding box of just the first line, not the complete box
    * for the barcodes types, the height of the barcode is `y2 - y1`, `x2` is ignored.
    * _mandatory_ (`x2` _optional_ for the barcode types)
* **`font`**: the name of a font type for the text types
    * _optional_
    * default: `helvetica`
* **`size`**: the size property of the element (float value)
    * for text, the font size (in points!)
    * for line, box, and ellipse, the line width
    * for the barcode types, the width of one bar 
    * _optional_
    * default: `10` for text, `2` for `BC`, `1.5` for `C39`
* **`__dash_pattern__(__dash__, __gap__, __phase__)`**: a dict of the line dash pattern for the element
    * _optional_
    * for line, box, ellipse follows the parameters of [set_dash_pattern()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_dash_pattern) 
    * Only supported in dict/JSON
    * `__dash__`,`__gap__`, and `__phase__` keys are possible, at least dash must be present. 
    * default: dash=0 (solid lines)
* **`bold, italic, underline`**: text style properties
    * in dict/JSON, enabled with True/true or equivalent value
    * in CSV, only int values, 0 as false, non-0 as true
    * _optional_
    * default: `false`
* **`foreground, background`**: text and fill colors (int value, commonly given in hex as `0xRRGGBB`)
    * in JSON, a decimal value or a HTML style `#RRGGBB` string (6 digits) can be given.
    * _optional_
    * default: foreground `0x000000` = black; background None/empty = transparent
* **`align`**: text alignment, `L`: left, `R`: right, `C`: center
    * _optional_
    * default: 'L'
* **`text`**: default string, can be replaced at runtime
    * displayed text for `T` and `W`
    * data to encode for barcode types
    * _optional_ (if missing for text/write, the element is ignored)
    * default: empty
* **`priority`**: Z-order (int value)
    * _optional_
    * default: 0
* **`multiline`**: configure text wrapping
    * in dicts/JSON, None/null for single line, True/true for multicells (multiple lines), False/false trims to exactly fit the space defined
    * in CSV, 0 for single line, >0 for multiple lines, <0 for exact fit
    * _optional_
    * default: single line
* **`rotation`**: rotate the element in degrees around the top left corner `x1`/`y1` (float)
    * _optional_
    * default: 0.0 - no rotation
* **`wrapmode`**: optionally set wrapmode to `'CHAR'` to support multiline line wrapping on characters instead of words
    * _optional_
    * default: `'WORD'`

Fields that are not relevant to a specific element type will be ignored there,
but if not left empty, they must still adhere to the specified data type (in dicts, string fields may be None).


## How to create a template
A template can be created in several ways:

* By defining everything directly as a Python dictionary - [example 1](#example-python-dict)
* By reading the template definition from a JSON document with `.parse_json()` - [example 2](#example-elements-defined-in-json-file)
* By reading the template definition from a CSV document with `.parse_csv()` - [example 3](#example-elements-defined-in-csv-file)


### Example - Python dict
```python
from fpdf import Template

#this will define the ELEMENTS that will compose the template. 
elements = [
    { 'name': 'company_logo', 'type': 'I', 'x1': 20.0, 'y1': 17.0, 'x2': 78.0, 'y2': 30.0, 'font': None, 'size': 0.0, 'bold': 0, 'italic': 0, 'underline': 0, 'align': 'C', 'text': 'logo', 'priority': 2, 'multiline': False},
    { 'name': 'company_name', 'type': 'T', 'x1': 17.0, 'y1': 32.5, 'x2': 115.0, 'y2': 37.5, 'font': 'helvetica', 'size': 12.0, 'bold': 1, 'italic': 0, 'underline': 0,'align': 'C', 'text': '', 'priority': 2, 'multiline': False},
    { 'name': 'multiline_text', 'type': 'T', 'x1': 20, 'y1': 100, 'x2': 40, 'y2': 105, 'font': 'helvetica', 'size': 12, 'bold': 0, 'italic': 0, 'underline': 0, 'background': 0x88ff00, 'align': 'C', 'text': 'Lorem ipsum dolor sit amet, consectetur adipisici elit', 'priority': 2, 'multiline': True, 'wrapmode': 'WORD'},
    { 'name': 'box', 'type': 'B', 'x1': 15.0, 'y1': 15.0, 'x2': 185.0, 'y2': 260.0, 'font': 'helvetica', 'size': 0.0, 'bold': 0, 'italic': 0, 'underline': 0, 'align': 'C', 'text': None, 'priority': 0, 'multiline': False},
    { 'name': 'box_x', 'type': 'B', 'x1': 95.0, 'y1': 15.0, 'x2': 105.0, 'y2': 25.0, 'font': 'helvetica', 'size': 0.0, 'bold': 1, 'italic': 0, 'underline': 0, 'align': 'C', 'text': None, 'priority': 2, 'multiline': False},
    { 'name': 'line1', 'type': 'L', 'x1': 100.0, 'y1': 25.0, 'x2': 100.0, 'y2': 57.0, 'font': 'helvetica', 'size': 0, 'bold': 0, 'italic': 0, 'underline': 0, 'align': 'C', 'text': None, 'priority': 3, 'multiline': False},
    { 'name': 'barcode', 'type': 'BC', 'x1': 20.0, 'y1': 246.5, 'x2': 140.0, 'y2': 254.0, 'font': 'Interleaved 2of5 NT', 'size': 0.75, 'bold': 0, 'italic': 0, 'underline': 0, 'align': 'C', 'text': '200000000001000159053338016581200810081', 'priority': 3, 'multiline': False},
]

#here we instantiate the template
f = Template(format="A4", elements=elements,
             title="Sample Invoice")
f.add_page()

#we FILL some of the fields of the template with the information we want
#note we access the elements treating the template instance as a "dict"
f["company_name"] = "Sample Company"
f["company_logo"] = "docs/fpdf2-logo.png"

#and now we render the page
f.render("./template.pdf")
```

### Example - Elements defined in JSON file
_New in [:octicons-tag-24: 2.8.0](https://github.com/py-pdf/fpdf2/blob/master/CHANGELOG.md)_

The JSON file must consist of an array of objects.
Each object with its name/value pairs define a template element:

```json
[
    {
        "name": "employee_name",
        "type": "T",
        "x1": 20,
        "y1": 75,
        "x2": 118,
        "y2": 90,
        "font": "helvetica",
        "size": 12,
        "bold": true,
        "underline": true,
        "text": ""
    }
]
```

Then you import and use that template as follows:

```python
def test_template():
    f = Template(format="A4", title="Template Demo")
    f.parse_json("myjsonfile.json")
    f.add_page()
    f["employee_name"] = "Joe Doe"
    return f.render("./template.pdf")
```

### Example - Elements defined in CSV file
You can define template elements in a CSV file `template_definition.csv`.
It can look like this:
```
line0;L;20.0;12.0;190.0;12.0;times;0.5;0;0;0;0;16777215;C;;0;0;0.0
line1;L;20.0;36.0;190.0;36.0;times;0.5;0;0;0;0;16777215;C;;0;0;0.0
name0;T;21.0;14.0;104.0;25.0;times;16.0;0;0;0;0;16777215;L;name;2;0;0.0
title0;T;21.0;26.0;104.0;30.0;times;10.0;0;0;0;0;16777215;L;title;2;0;0.0
multiline;T;21.0;50.0;28.0;54.0;times;10.5;0;0;0;0;0xffff00;L;multi line;0;1;0.0
numeric_text;T;21.0;80.0;100.0;84.0;times;10.5;0;0;0;0;;R;007;0;0;0.0
empty_fields;T;21.0;100.0;100.0;104.0
rotated;T;21.0;80.0;100.0;84.0;times;10.5;0;0;0;0;;R;ROTATED;0;0;30.0
```

Remember that each line represents an element and each field represents one of the properties of the element in the following order:
`('name','type','x1','y1','x2','y2','font','size','bold','italic','underline','foreground','background','align','text','priority', 'multiline', 'rotate', 'wrapmode')`
As noted above, most fields may be left empty, so a line is valid with only 6 items.
The `empty_fields` line of the example demonstrates all that can be left away.
In addition, for the barcode types, `x2` may be empty.

Then you can use the file like this:

```python
def test_template():
    f = Template(format="A4",
                 title="Sample Invoice")
    f.parse_csv("template_definition.csv", delimiter=";")
    f.add_page()
    f["name0"] = "Joe Doe"
    return f.render("./template.pdf")
```
