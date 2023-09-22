# fpdf2 #

`fpdf2` is a library for simple & fast PDF document generation in Python.
It is a fork and the successor of `PyFPDF` (_cf._ [history](https://py-pdf.github.io/fpdf2/History.html)).

**Latest Released Version:** [![Pypi latest version](https://img.shields.io/pypi/v/fpdf2.svg)](https://pypi.python.org/pypi/fpdf2)

![fpdf2 logo](fpdf2-logo.png)

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font('helvetica', size=12)
pdf.cell(txt="hello world")
pdf.output("hello_world.pdf")
```

Go try it **now** online in a Jupyter notebook: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/py-pdf/fpdf2/blob/master/tutorial/notebook.ipynb) or [![Open In nbviewer](https://img.shields.io/badge/Open_In-nbviewer-blue?logo=jupyter)](https://nbviewer.org/github/py-pdf/fpdf2/blob/master/tutorial/notebook.ipynb)

## Main features ##

* Easy to use, with a user-friendly [API](https://py-pdf.github.io/fpdf2/fpdf/), and easy to extend
* Python 3.7+ support
* [Unicode](Unicode.md) (UTF-8) TrueType font subset embedding (Central European, Cyrillic, Greek, Baltic, Thai, Chinese, Japanese, Korean, Hindi and almost any other language in the world)
* Internal / external [links](Links.md)
* Embedding images, including transparency and alpha channel, using [Pillow (Python Imaging Library)](https://pillow.readthedocs.io/en/stable/)
* Arbitrary path drawing and basic [SVG](SVG.md) import
* Embedding [barcodes](Barcodes.md), [charts & graphs](Maths.md), [emojis, symbols & dingbats](EmojisSymbolsDingbats.md)
* [Tables](Tables.md), and also [cell / multi-cell / plaintext writing](Text.md), with [automatic page breaks](PageBreaks.md), line break and text justification
* Choice of measurement unit, page format & margins. Optional page header and footer
* Basic [conversion from HTML to PDF](HTML.md)
* A [templating system](Templates.md) to render PDFs in batchs
* Images & links alternative descriptions, for accessibility
* Table of contents & [document outline](DocumentOutlineAndTableOfContents.md)
* [Document encryption](Encryption.md) & [document signing](Signing.md)
* [Annotations](Annotations.md), including text highlights, and [file attachments](FileAttachments.md)
* [Presentation mode](Presentations.md) with control over page display duration & transitions
* Optional basic Markdown-like styling: `**bold**, __italics__`
* It has very few dependencies: [Pillow](https://pillow.readthedocs.io/en/stable/), [defusedxml](https://pypi.org/project/defusedxml/), & [fonttools](https://pypi.org/project/fonttools/)
* Can render [mathematical equations & charts](https://py-pdf.github.io/fpdf2/Maths.html)
* Many example scripts available throughout this documentation, including usage examples with [Django](https://www.djangoproject.com/), [Flask](https://flask.palletsprojects.com), [FastAPI](https://fastapi.tiangolo.com/), [streamlit](https://streamlit.io/), AWS lambdas... : [Usage in web APIs](UsageInWebAPI.md)
* Unit tests with `qpdf`-based PDF diffing, and PDF samples validation using 3 different checkers:

[![QPDF logo](qpdf-logo.svg)](https://github.com/qpdf/qpdf)
[![PDF Checker logo](pdfchecker-logo.png)](https://www.datalogics.com/products/pdf-tools/pdf-checker/)
[![VeraPDF logo](vera-logo.jpg)](https://verapdf.org)

## Tutorials ##

* [English](Tutorial.md)
* [Deutsch](Tutorial-de.md)
* [Italian](Tutorial-it.md)
* [español](Tutorial-es.md)
* [français](Tutorial-fr.md)
* [हिंदी](Tutorial-hi.md)
* [português](Tutorial-pt.md)
* [Русский](Tutorial-ru.md)
* [Ελληνικά](Tutorial-gr.md)
* [עברית](Tutorial-he.md)
* [简体中文](Tutorial-zh.md)
* [বাংলা](Tutorial-bn.md)
* [ភាសខ្មែរ](Tutorial-km.md)
* [日本語](Tutorial-ja.md)

## Installation ##

From [PyPI](https://pypi.python.org/pypi/fpdf2):
```bash
pip install fpdf2
```

To get the latest, unreleased, development version straight from the development branch of this repository:

```bash
pip install git+https://github.com/py-pdf/fpdf2.git@master
```

**Developement**: check the [dedicated documentation page](Development.md).

### Displaying deprecation warnings
`DeprecationWarning`s are not displayed by Python by default.

Hence, every time you use a newer version of `fpdf2`, we strongly encourage you to execute your scripts
with the `-Wd` option (_cf._ [documentation](https://docs.python.org/3/using/cmdline.html#cmdoption-W)) 
in order to get warned about deprecated features used in your code.

This can also be enabled programmatically with `warnings.simplefilter('default', DeprecationWarning)`.

## Community ##

### Support ###

For community support, please feel free to file an [issue](https://github.com/py-pdf/fpdf2/issues)
or [open a discussion](https://github.com/py-pdf/fpdf2/discussions).

### They use fpdf2 ###
<!-- cf. Watchman Pypi & DavHau/pypi-deps-db -->
* **Harvard University** uses `fpdf2` in their [CS50 introductory class](https://cs50.harvard.edu/python/2022/psets/8/shirtificate/)
* [Undying Dusk](https://lucas-c.itch.io/undying-dusk) : a **video game in PDF format**, with a gameplay based on exploration and logic puzzles, in the tradition of dungeon crawlers
* [OpenDroneMap](https://github.com/OpenDroneMap/ODM) : a command line toolkit for processing aerial drone imagery
* [OpenSfM](https://github.com/mapillary/OpenSfM) : a Structure from Motion library, serving as a processing pipeline for reconstructing camera poses and 3D scenes from multiple images
* [RPA Framework](https://github.com/robocorp/rpaframework) : libraries and tools for Robotic Process Automation (RPA), designed to be used with both [Robot Framework](https://robotframework.org)
* [Concordia](https://github.com/LibraryOfCongress/concordia) : a platform developed by the US Library of Congress for crowdsourcing transcription and tagging of text in digitized images
* [wudududu/extract-video-ppt](https://github.com/wudududu/extract-video-ppt) : create a one-page-per-frame PDF from a video or PPT file.
  `fpdf2` also has a demo script to convert a GIF into a one-page-per-frame PDF: [gif2pdf.py](https://github.com/py-pdf/fpdf2/blob/master/tutorial/gif2pdf.py)
* [csv2pdf](https://github.com/TECH-SAVVY-GUY/csv2pdf) : convert CSV files to PDF files easily
* [Planet-Matriarchy-RPG-CharGen](https://github.com/ShawnDriscoll/Planet-Matriarchy-RPG-CharGen) : a PyQt based desktop application (= `.exe` under Windows) that provides a RPG character sheet generator

### Usage statistics

- [PyPI download stats](https://pypistats.org/packages/fpdf2) - Downloads per release on [Pepy](https://pepy.tech/project/fpdf2)
  - [pip trends: fpdf2 VS other PDF rendering libs](https://piptrends.com/compare/fpdf2-vs-fpdf-vs-pypdf-vs-borb-vs-reportlab)
- packages using `fpdf2` can be listed using [GitHub Dependency graph: Dependents](https://github.com/py-pdf/fpdf2/network/dependents),
[Wheelodex](https://www.wheelodex.org/projects/fpdf2/rdepends/) or [Watchman Pypi](http://www.watchman-pypi.com).
Some are also listed on [its libraries.io page](https://libraries.io/pypi/fpdf2).

### Related ###

* Looking for alternative libraries? Check out [pypdf](https://github.com/py-pdf/pypdf), [borb](https://github.com/jorisschellekens/borb), [pikepdf](https://github.com/pikepdf/pikepdf), [WeasyPrint](https://github.com/Kozea/WeasyPrint), [pydyf](https://pypi.org/project/pydyf/) and [PyMuPDF](https://pymupdf.readthedocs.io/en/latest/index.html): [features comparison](https://pymupdf.readthedocs.io/en/latest/about.html), [examples](https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/examples#examples), [Jupyter notebooks](https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/jupyter-notebooks).
  We have some documentations about combining `fpdf2` with [`borb`](CombineWithBorb.md) & [`pypdf`](CombineWithPypdf.md).
* [Create PDFs with Python](https://www.youtube.com/playlist?list=PLjNQtX45f0dR9K2sMJ5ad9wVjqslNBIC0) : a series of tutorial videos by bvalgard
* [digidigital/Extensions-and-Scripts-for-pyFPDF-fpdf2](https://github.com/digidigital/Extensions-and-Scripts-for-pyFPDF-fpdf2) : scripts ported from PHP to add transpareny to elements of the page or part of an image, allow to write circular text,
   draw pie charts and bar diagrams, embed JavaScript, draw rectangles with rounded corners, draw a star shape,
   restrict the rendering of some elements to screen or printout, paint linear / radial / multi-color gradients gradients, add stamps & watermarks, write sheared text...

## Misc ##

* Release notes: [CHANGELOG.md](https://github.com/py-pdf/fpdf2/blob/master/CHANGELOG.md)
* This library could only exist thanks to the dedication of many volunteers around the world:
  [list & map of contributors](https://github.com/py-pdf/fpdf2/blob/master/README.md#contributors-)
* You can download an offline PDF version of this manual: [fpdf2-manual.pdf](fpdf2-manual.pdf)
