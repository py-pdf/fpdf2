
# Introduction #

If you use [web2py](http://www.web2py.com), you can make complex reports that can be viewed in a browser, or downloaded as PDF (taking advantage of web2py HTML helper objects to easily diagram a report). See [write_html](HTML.md) for more information, supported tags and attributes, etc.

Also, using web2py DAL, you can easily set up a templating engine for PDF documents. See [Templates](Templates.md) for more information.

The following examples are packaged in a ready to run application:
[web2py.app.fpdf.w2p](http://pyfpdf.googlecode.com/files/web2py.app.fpdf.w2p).

PyFPDF is included in [web2py](http://www.web2py.com/) since release [1.85.2](http://www.web2py.com/examples/default/download).

Also, you can put the content of the `fpdf/` directory in this repository into the `web2py/gluon/contrib` folder.

**Note about images**: these sample images are small so they may look like low quality ones. For better results, use bigger images: more DPI (screen is often 72/96DPI, printers are often 300/600DPI). As a rule of thumb, use at least half of the image size when rendering to PDF, ie. if an image is 500x200px, use 250x100px as width and height attributes of the IMG tag.


# Sample Report #

You could make a "professional looking" bussiness report just using web2py HTML helpers, mixin headers, logos, charts, text and tables.

The main advantage of this method is that the same report can be rendered in a HTML view, or can be downloaded as PDF, with a minimal effort:

Sample: [report.pdf](http://pyfpdf.googlecode.com/files/report.pdf)

Updated Live Demo (HTML and PDF version):

  * <http://www.web2py.com.ar/fpdf/default/report>
  * <http://www.web2py.com.ar/fpdf/default/report.pdf>

```python
def report():
    response.title = "web2py sample report"
    
    # include a google chart (download it dynamically!)
    url = "http://chart.apis.google.com/chart?cht=p3&chd=t:60,40&chs=500x200&chl=Hello|World&.png"
    chart = IMG(_src=url, _width="250", _height="100")

    # create a small table with some data:
    rows = [THEAD(TR(TH("Key", _width="70%"), TH("Value", _width="30%"))),
            TBODY(TR(TD("Hello"), TD("60")), 
                  TR(TD("World"), TD("40")))]
    table = TABLE(*rows, _border="0", _align="center", _width="50%")

    if request.extension == "pdf":
        from gluon.contrib.fpdf import FPDF, HTMLMixin

        # create a custom class with the required functionality 
        class MyFPDF(FPDF, HTMLMixin):
            def header(self): 
                """hook to draw custom page header (logo and title)"""
                logo = os.path.join(request.env.web2py_path, "gluon", "contrib", "pyfpdf", "tutorial", "logo_pb.png")
                self.image(logo, 10, 8, 33)
                self.set_font('helvetica', 'B', 15)
                self.cell(65) # padding
                self.cell(60, 10, response.title, 1, 0, 'C')
                self.ln(20)
                
            def footer(self):
                """hook to draw custom page footer (printing page numbers)"""
                self.set_y(-15)
                self.set_font('helvetica', 'I', 8)
                txt = f'Page {self.page_no()} of {self.alias_nb_pages()}'
                self.cell(0, 10, txt, 0, 0, 'C')
                    
        pdf = MyFPDF()
        # create a page and serialize/render HTML objects
        pdf.add_page()
        pdf.write_html(str(XML(table, sanitize=False)))
        pdf.write_html(str(XML(CENTER(chart), sanitize=False)))
        # prepare PDF to download:
        response.headers['Content-Type'] = 'application/pdf'
        return pdf.output()
    else:
        # normal html view:
        return dict(chart=chart, table=table)

```

# Sample Table Listing #

Also, you can make nice tables that automatically spreads over several pages, with headers and footers, column and row highlighting, etc., in a very pythonic way:

Sample: [listing.pdf](http://pyfpdf.googlecode.com/files/listing.pdf)

Updated Live Demo (HTML and PDF version):

  * <http://www.web2py.com.ar/fpdf/default/listing>
  * <http://www.web2py.com.ar/fpdf/default/listing.pdf>

```python
def listing():
    response.title = "web2py sample listing"
    
    # define header and footers:
    head = THEAD(TR(TH("Header 1", _width="50%"), 
                    TH("Header 2", _width="30%"),
                    TH("Header 3", _width="20%"), 
                    _bgcolor="#A0A0A0"))
    foot = TFOOT(TR(TH("Footer 1", _width="50%"), 
                    TH("Footer 2", _width="30%"),
                    TH("Footer 3", _width="20%"),
                    _bgcolor="#E0E0E0"))
    
    # create several rows:
    rows = []
    for i in range(1000):
        col = i % 2 and "#F0F0F0" or "#FFFFFF"
        rows.append(TR(TD("Row %s" %i),
                       TD("something", _align="center"),
                       TD("%s" % i, _align="right"),
                       _bgcolor=col)) 

    # make the table object
    body = TBODY(*rows)
    table = TABLE(*[head, foot, body], 
                  _border="1", _align="center", _width="100%")

    if request.extension == "pdf":
        from gluon.contrib.fpdf import FPDF, HTMLMixin

        # define our FPDF class (move to modules if it is reused frequently)
        class MyFPDF(FPDF, HTMLMixin):
            def header(self):
                self.set_font('helvetica', 'B', 15)
                self.cell(0, 10, response.title, 1, 0, 'C')
                self.ln(20)
                
            def footer(self):
                self.set_y(-15)
                self.set_font('helvetica', 'I', 8)
                txt = 'Page %s of %s' % (self.page_no(), self.alias_nb_pages())
                self.cell(0, 10, txt, 0, 0, 'C')
                    
        pdf = MyFPDF()
        # first page:
        pdf.add_page()
        pdf.write_html(str(XML(table, sanitize=False)))
        response.headers['Content-Type'] = 'application/pdf'
        return pdf.output()
    else:
        # normal html view:
        return dict(table=table)}}}
```


# Samples Template Definitions #

As stated in the [Templates](Templates.md) page, there are 3 ways of putting your templates in place.
As in that page there are samples for the manually hardcoded way and CSV document loading.
Here we will only show a sample of the template engine.



# Sample Templating Engine #

PyFPDF and web2py can be used to make PDF documents using templates like invoices, badges, certificates, etc.:

Sample: [invoice.pdf](http://pyfpdf.googlecode.com/files/invoice.pdf)

Updated Live Demo: <http://www.web2py.com.ar/fpdf/default/invoice.pdf>

To handle multiple templates, we can define two tables in web2py:

  * pdf\_template: general document information (name, paper size, etc.)
  * pdf\_element: several rows for each document, describing graphics primitives and placeholders.

In `db.py` write:
```python
db.define_table("pdf_template",
    Field("pdf_template_id", "id"),
    Field("title"),
    Field("format", requires=IS_IN_SET(["A4", "legal", "letter"])),
)

db.define_table("pdf_element",
    Field("pdf_template_id", db.pdf_template, requires=IS_IN_DB(db, 'pdf_template.pdf_template_id', 'pdf_template.title')),
    Field("name", requires=IS_NOT_EMPTY()),
    Field("type", length=2, requires=IS_IN_SET(['T', 'L', 'I', 'B', 'BC'])),
    Field("x1", "double", requires=IS_NOT_EMPTY()),
    Field("y1", "double", requires=IS_NOT_EMPTY()),
    Field("x2", "double", requires=IS_NOT_EMPTY()),
    Field("y2", "double", requires=IS_NOT_EMPTY()),
    Field("font", default="helvetica", requires=IS_IN_SET(['Courier', 'helvetica', 'Times', 'Symbol', 'Zapfdingbats'])),
    Field("size", "double", default="10", requires=IS_NOT_EMPTY()),
    Field("bold", "boolean"),
    Field("italic", "boolean"),
    Field("underline", "boolean"),
    Field("foreground", "integer", default=0x000000, comment="Color text"),
    Field("background", "integer", default=0xFFFFFF, comment="Fill color"),
    Field("align", "string", length=1, default="L", requires=IS_IN_SET(['L', 'R', 'C', 'J'])),
    Field("text", "text", comment="Default text"),
    Field("priority", "integer", default=0, comment="Z-Order"),
    )
```

**Warning**: the fields "type", "size" and "text" are reserved words for some DB engines, so validation:

```python
db = DAL('sqlite://storage.sqlite', pool_size=1, check_reserved=['ALL'])
```
will fail. sqlite, MySQL and postgres work OK. Proposals for new naming ideas are welcome.

At this point you could go to web2py AppAdmin and start to define your document templates, or use import/export functions to reuse your already defined formats!

Note: if you used designer.py to create the templates, and you want to import the templates with the Web2Py database admin, you will have to modify the file.

So, designer.py outputs a file like this:
```
line0;T;20.0;13.0;190.0;13.0;times;10.0;0;0;0;0;65535;C;;0
line1;T;20.0;67.0;190.0;67.0;times;10.0;0;0;0;0;65535;C;;0
name0;T;21;14;104;25;times;16.0;0;0;0;0;0;C;;2
title0;T;64;26;104;30;times;10.0;0;0;0;0;0;C;;2
```

You will have to make it look lke this:

```
pdf_element.pdf_template_id, pdf_element.name, pdf_element.type, pdf_element.x1, pdf_element.y1, pdf_element.x2, pdf_element.y2, pdf_element.font, pdf_element.size, pdf_element.bold, pdf_element.italic, pdf_element.underline, pdf_element.foreground, pdf_element.background, pdf_element.align, pdf_element.text, pdf_element.priority
1,line0,T,20.0,283.0,190.0,283.0,times,10.0,0,0,0,0,65535,C,,0
1,line1,T,20.0,337.0,190.0,337.0,times,10.0,0,0,0,0,65535,C,,0
1,name0,T,21,14,104,25,times,16.0,0,0,0,0,0,C,,2
1,title0,T,64,26,104,30,times,10.0,0,0,0,0,0,C,,2
```
Where the first number indicates the template ID (important for the database system), and the first line indicates the database fields to fill.

A simple Python script should do the trick.

After defining and filling your database, you can use PyFPDF [Templates](Templates.md) directly reading row elements from the web2py database:

For example, for an invoice, in a controller you could write:
```python
def invoice():
    from gluon.contrib.fpdf import Template
    import os.path
    
    # generate sample invoice (according Argentina's regulations)

    import random
    from decimal import Decimal

    # read elements from db 
    
    elements = db(db.pdf_element.pdf_template_id == 1).select(orderby=db.pdf_element.priority)

    f = Template(format="A4",
                 elements = elements,
                 title="Sample Invoice", author="Sample Company",
                 subject="Sample Customer", keywords="Electronic TAX Invoice")
    
    # create some random invoice line items and detail data
    detail = "Lorem ipsum dolor sit amet, consectetur. " * 5
    items = []
    for i in range(1, 30):
        ds = "Sample product %s" % i
        qty = random.randint(1, 10)
        price = round(random.random() * 100, 3)
        code = "%s%s%02d" % (chr(random.randint(65, 90)), chr(random.randint(65, 90)), i)
        items.append(dict(code=code, unit='u',
                          qty=qty, price=price, 
                          amount=qty * price,
                          ds="%s: %s" % (i, ds)))

    # divide and count lines
    lines = 0
    li_items = []
    for it in items:
        qty = it['qty']
        code = it['code']
        unit = it['unit']
        for ds in f.split_multicell(it['ds'], 'item_description01'):
            # add item description line (without price nor amount)
            li_items.append(dict(code=code, ds=ds, qty=qty, unit=unit, price=None, amount=None))
            # clean qty and code (show only at first)
            unit = qty = code = None
        # set last item line price and amount
        li_items[-1].update(amount = it['amount'],
                            price = it['price'])

    # split detail into each line description
    obs="\n<U>Detail:</U>\n\n" + detail
    for ds in f.split_multicell(obs, 'item_description01'):
        li_items.append(dict(code=code, ds=ds, qty=qty, unit=unit, price=None, amount=None))

    # calculate pages:
    lines = len(li_items)
    max_lines_per_page = 24
    pages = lines / (max_lines_per_page - 1)
    if lines % (max_lines_per_page - 1): pages = pages + 1

    # fill placeholders for each page
    for page in range(1, pages + 1):
        f.add_page()
        f['page'] = 'Page %s of %s' % (page, pages)
        if pages > 1 and page < pages:
            s = 'Continues on page %s' % (page + 1)
        else:
            s = ''
        f['item_description%02d' % (max_lines_per_page + 1)] = s

        f["company_name"] = "Sample Company"
        f["company_logo"] = os.path.join(request.env.web2py_path, "gluon", "contrib", "pyfpdf", "tutorial", "logo.png")
        f["company_header1"] = "Some Address - somewhere -"
        f["company_header2"] = "http://www.example.com"        
        f["company_footer1"] = "Tax Code ..."
        f["company_footer2"] = "Tax/VAT ID ..."
        f['number'] = '0001-00001234'
        f['issue_date'] = '2010-09-10'
        f['due_date'] = '2099-09-10'
        f['customer_name'] = "Sample Client"
        f['customer_address'] = "Siempreviva 1234"
       
        # print line item...
        li = 0 
        k = 0
        total = Decimal("0.00")
        for it in li_items:
            k = k + 1
            if k > page * (max_lines_per_page - 1):
                break
            if it['amount']:
                total += Decimal("%.6f" % it['amount'])
            if k > (page - 1) * (max_lines_per_page - 1):
                li += 1
                if it['qty'] is not None:
                    f['item_quantity%02d' % li] = it['qty']
                if it['code'] is not None:
                    f['item_code%02d' % li] = it['code']
                if it['unit'] is not None:
                    f['item_unit%02d' % li] = it['unit']
                f['item_description%02d' % li] = it['ds']
                if it['price'] is not None:
                    f['item_price%02d' % li] = "%0.3f" % it['price']
                if it['amount'] is not None:
                    f['item_amount%02d' % li] = "%0.2f" % it['amount']

        # last page? print totals:
        if pages == page:
            f['net'] = "%0.2f" % (total / Decimal("1.21"))
            f['vat'] = "%0.2f" % (total * (1 - 1 / Decimal("1.21")))
            f['total_label'] = 'Total:'
        else:
            f['total_label'] = 'SubTotal:'
        f['total'] = "%0.2f" % total

    response.headers['Content-Type'] = 'application/pdf'
    return f.render('invoice.pdf')
```

Of course, this is a hardcoded example. You can use the database to store invoices or any other data;
there is no rigid class hierachy to follow, just fill your template like a dict!
