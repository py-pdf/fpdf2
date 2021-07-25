# FAQ #

See [Project Home](index.md) for an overall introduction.

[TOC]

## What is fpdf2? ##

`fpdf2` is a library with low-level primitives to easily generate PDF documents.

This is similar to [ReportLab](https://www.reportlab.com)'s graphics canvas,
but with some methods to output "fluid" cells
("flowables" that can span multiple rows, pages, tables, columns, etc).

It has methods ("hooks") that can be implemented in a subclass: `headers` and `footers`.

Originally developed in PHP several years ago (as a free alternative to proprietary C libraries),
it has been ported to many programming languages,
including ASP, C++, Java, Pl/SQL, Ruby, Visual Basic, and of course, Python.

For more information see: <http://www.fpdf.org/en/links.php>

## What is this library **not**? ##

This library is not a:

  * charts or widgets library.
    But you can import PNG or JPG images, use PIL or any other library, or draw the figures yourself.

  * "flexible page layout engine" like [Reportlab](http://www.reportlab.com/opensource/) PLATYPUS.
    But it can do columns, chapters, etc.; see the [Tutorial](Tutorial.md).

  * XML or object definition language like [Geraldo Reports](http://www.geraldoreports.org/), Jasper Reports, or similar.
    But look at [write_html](HTML.md) for simple HTML reports and [Templates](Templates.md) for fill-in-the-blank documents.

  * PDF text extractor, converter, splitter or similar.

## How does this library compare to ...? ##

The API is geared toward giving the user access to features of the Portable
Document Format as they are described in the Adobe PDF Reference Manual, this
bypasses needless complexities for simpler use cases.

It is small:
```
$ du -sh fpdf
272K    fpdf

$ scc fpdf
───────────────────────────────────────────────────────────────────────────────
Language                 Files     Lines   Blanks  Comments     Code Complexity
───────────────────────────────────────────────────────────────────────────────
Python                      14      8204      142       232     7830        192
```

It includes `cell` and `multi_cell` primitives to draw fluid document like
invoices, listings and reports, and includes basic support for HTML rendering.

> Compared to other solutions, this library should be easier to use and adapt
> for most common documents (no need to use a page layout engine, style
> sheets, templates, or stories...), with full control over the generated PDF
> document (including advanced features and extensions).

Check also the list of features on the [home page](index.md).

## What does the code look like? ##

Following is an example similar to the Reportlab one in the book of web2py. Note
the simplified import and usage:
(<http://www.web2py.com/book/default/chapter/09?search=pdf#ReportLab-and-PDF>)

```python
from fpdf import FPDF

def get_me_a_pdf():
    title = "This The Doc Title"
    heading = "First Paragraph"
    text = 'bla ' * 10000

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Times', 'B', 15)
    pdf.cell(w=210, h=9, txt=title, border=0, ln=1, align='C', fill=False)
    pdf.set_font('Times', 'B', 15)
    pdf.cell(w=0, h=6, txt=heading, border=0, ln=1, align='L', fill=False)
    pdf.set_font('Times', '', 12)
    pdf.multi_cell(w=0, h=5, txt=text)
    response.headers['Content-Type'] = 'application/pdf'
    return pdf.output()
```

With Reportlab:
```python
from reportlab.platypus import *
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from uuid import uuid4
from cgi import escape
import os

def get_me_a_pdf():
    title = "This The Doc Title"
    heading = "First Paragraph"
    text = 'bla ' * 10000

    styles = getSampleStyleSheet()
    tmpfilename = os.path.join(request.folder, 'private', str(uuid4()))
    doc = SimpleDocTemplate(tmpfilename)
    story = []
    story.append(Paragraph(escape(title), styles["Title"]))
    story.append(Paragraph(escape(heading), styles["Heading2"]))
    story.append(Paragraph(escape(text), styles["Normal"]))
    story.append(Spacer(1, 2 * inch))
    doc.build(story)
    data = open(tmpfilename, "rb").read()
    os.unlink(tmpfilename)
    response.headers['Content-Type'] = 'application/pdf'
    return data
```

## Does this library have any framework integration? ##

Yes, if you use web2py, you can make simple HTML reports that can be viewed in a browser,
or downloaded as PDF.

Also, using web2py DAL, you can easily set up a templating engine for PDF  documents.

Look at [Web2Py](Web2Py.md) for examples.

## What is the development status of this library? ##

This library was improved over the years since the initial port from PHP.
As of 2021, it is **stable** and actively maintained, with bug fixes and new features developped regularly.

In contrast, `write_html` support is not complete, so it must be considered in beta state.

## What is the license of this library (fpdf2)? ##

LGPL v3.0.

Original FPDF uses a permissive license:
<http://www.fpdf.org/en/FAQ.php#q1>

> "FPDF is released under a permissive license: there is no usage
> restriction. You may embed it freely in your application (commercial
> or not), with or without modifications."

FPDF version 1.6's license.txt says:
<http://www.fpdf.org/es/dl.php?v=16&f=zip>

> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software to use, copy, modify, distribute, sublicense, and/or sell
> copies of the software, and to permit persons to whom the software is furnished
> to do so.

> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.

The fpdf.py library is a revision of a port by Max Pat. The original source uses the same
licence: <http://www.fpdf.org/dl.php?id=94>

```python
# * Software: FPDF
# * Version:  1.53
# * Date:     2004-12-31
# * Author:   Olivier PLATHEY
# * License:  Freeware
# *
# * You may use and modify this software as you wish.
# * Ported to Python 2.4 by Max (maxpat78@yahoo.it) on 2006-05
```

To avoid ambiguity (and to be compatible with other free software, open source 
licenses), LGPL was chosen for the Google Code project (as freeware isn't 
listed).

Some FPDF ports had chosen similar licences (wxWindows Licence for C++ port, 
MIT licence for Java port, etc.): <http://www.fpdf.org/en/links.php>

Other FPDF derivatives also choose LGPL, such as 
[sFPDF](http://www.fpdf.org/en/script/script91.php) by 
[Ian Back](mailto:ian@bpm1.com?subject=sFPDF).
