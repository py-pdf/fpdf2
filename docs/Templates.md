# Introduction #

Templates are predefined documents (like invoices, tax forms, etc.), where each element (text, lines, barcodes, etc.) has a fixed position (x1, y1, x2, y2), style (font, size, etc.) and a default text.

This elements can act as placeholders, so the program can change the default text "filling" the document.

Also, the elements can be defined in a CSV file or in a database, so the user can easily adapt the form to his printing needs.

A template is used like a dict, setting its items' values.

# Details - Template definition #

A template is composed of a header and a list of elements.

The header contains the page format, title of the document and other metadata.

Elements have the following properties (columns in a CSV, fields in a database):

  * name: placeholder identification
  * type: 'T': texts, 'L': lines, 'I': images, 'B': boxes, 'BC': barcodes
  * x1, y1, x2, y2: top-left, bottom-right coordinates (in mm)
  * font: e.g. "helvetica"
  * size: text size in points, e.g. 10
  * bold, italic, underline: text style (non-empty to enable)
  * foreground, background: text and fill colors, e.g. 0xFFFFFF
  * align: text alignment, 'L': left, 'R': right, 'C': center
  * text: default string, can be replaced at runtime
  * priority: Z-order
  * multiline: None for single line (default), True to for multicells (multiple lines), False trims to exactly fit the space defined

# How to create a template #

A template can be created in 3 ways:

  * By defining everything manually in a hardcoded way
  * By using a template definition in a CSV document and parsing the CSV with Template.parse\_dict()
  * By defining the template in a database (this applies to [Web2Py] (Web2Py.md) integration)


Note the following, the definition of a template will contain the elements. The header will be given during instantiation (except for the database method).

# Example - Hardcoded #

```python

from fpdf import Template

#this will define the ELEMENTS that will compose the template. 
elements = [
    { 'name': 'company_logo', 'type': 'I', 'x1': 20.0, 'y1': 17.0, 'x2': 78.0, 'y2': 30.0, 'font': None, 'size': 0.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0, 'align': 'I', 'text': 'logo', 'priority': 2, 'multiline': 0},
    { 'name': 'company_name', 'type': 'T', 'x1': 17.0, 'y1': 32.5, 'x2': 115.0, 'y2': 37.5, 'font': 'helvetica', 'size': 12.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0, 'align': 'I', 'text': '', 'priority': 2, 'multiline': 0},
    { 'name': 'multline_text', 'type': 'T', 'x1': 20, 'y1': 100, 'x2': 40, 'y2': 105, 'font': 'helvetica', 'size': 12, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0x88ff00, 'align': 'I', 'text': 'Lorem ipsum dolor sit amet, consectetur adipisici elit', 'priority': 2, 'multiline': 1}
    { 'name': 'box', 'type': 'B', 'x1': 15.0, 'y1': 15.0, 'x2': 185.0, 'y2': 260.0, 'font': 'helvetica', 'size': 0.0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0, 'align': 'I', 'text': None, 'priority': 0, 'multiline': 0},
    { 'name': 'box_x', 'type': 'B', 'x1': 95.0, 'y1': 15.0, 'x2': 105.0, 'y2': 25.0, 'font': 'helvetica', 'size': 0.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0, 'align': 'I', 'text': None, 'priority': 2, 'multiline': 0},
    { 'name': 'line1', 'type': 'L', 'x1': 100.0, 'y1': 25.0, 'x2': 100.0, 'y2': 57.0, 'font': 'helvetica', 'size': 0, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0, 'align': 'I', 'text': None, 'priority': 3, 'multiline': 0},
    { 'name': 'barcode', 'type': 'BC', 'x1': 20.0, 'y1': 246.5, 'x2': 140.0, 'y2': 254.0, 'font': 'Interleaved 2of5 NT', 'size': 0.75, 'bold': 0, 'italic': 0, 'underline': 0, 'foreground': 0, 'background': 0, 'align': 'I', 'text': '200000000001000159053338016581200810081', 'priority': 3, 'multiline': 0},
]

#here we instantiate the template and define the HEADER
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

See template.py or [Web2Py] (Web2Py.md) for a complete example.

# Example - Elements defined in CSV file #
You define your elements in a CSV file "mycsvfile.csv"
that will look like:
```
line0;L;20.0;12.0;190.0;12.0;times;0.5;0;0;0;0;16777215;C;;0;0
line1;L;20.0;36.0;190.0;36.0;times;0.5;0;0;0;0;16777215;C;;0;0
name0;T;21.0;14.0;104.0;25.0;times;16.0;0;0;0;0;16777215;L;name;2;0
title0;T;21.0;26.0;104.0;30.0;times;10.0;0;0;0;0;16777215;L;title;2;0
multiline;T;21.0;50.0;28.0;54.0;times;10.5;0;0;0;0;16777215;L;multi line;0;1
numeric_text;T;21.0;80.0;100.0;84.0;times;10.5;0;0;0;0;16777215;R;007;0;0
```

Remember that each line represents an element and each field represents one of the properties of the element in the following order:
('name','type','x1','y1','x2','y2','font','size','bold','italic','underline','foreground','background','align','text','priority', 'multiline')

Then you can use the file like this:

```python
def test_template():
    f = Template(format="A4",
                 title="Sample Invoice")
    f.parse_csv("mycsvfile.csv", delimiter=";")
    f.add_page()
    f["name0"] = "Joe Doe"
    return f.render("./template.pdf")

```
