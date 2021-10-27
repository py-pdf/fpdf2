# fpdf2 #

<a href='https://github.com/PyFPDF/fpdf2'><img src='https://s3.amazonaws.com/github/ribbons/forkme_right_red_aa0000.png' alt='Fork me on GitHub' border='0' align='right' /></a>

`fpdf2` is a library for PDF document generation in Python, forked from the unmaintained [pyfpdf](https://github.com/reingart/pyfpdf), itself ported from the PHP [FPDF](http://www.fpdf.org/) library.

**Latest Released Version:** [![Pypi latest version](https://img.shields.io/pypi/v/fpdf2.svg)](https://pypi.python.org/pypi/fpdf2)

![fpdf2 logo](fpdf2-logo.png)

## Main features ##

* Easy to use (and easy to extend)
* Small and compact code, useful for testing new features and teaching
* Many simple examples and scripts available in many languages
* PIL Integration for images (via Pillow)
* No installation, no compilation or other libraries (DLLs) required

This repository is a fork of the library's [original port by Max Pat](http://www.fpdf.org/dl.php?id=94), with the following enhancements:

* Python 3.6+ support
* [Unicode](Unicode.md) (UTF-8) TrueType font subset embedding (Central European, Cyrillic, Greek, Baltic, Thai, Chinese, Japanese, Korean, Hindi and almost any other language in the world)
* PNG, GIF and JPG support (including transparency and alpha channel)
* Shape, Line Drawing
* Generate [Code 39](https://fr.wikipedia.org/wiki/Code_39) & [Interleaved 2 of 5](https://en.wikipedia.org/wiki/Interleaved_2_of_5) barcodes
* Cell / multi-cell / plaintext writing, automatic page breaks
* Basic conversion from HTML to PDF
* Images & links alternative descriptions
* Table of contents & [document outline](https://pyfpdf.github.io/fpdf2/DocumentOutlineAndTableOfContents.html)
* Optional basic Markdown-like styling: `**bold**, __italics__, --underlined--`
* Clean error handling through exceptions
* Only **one** dependency so far: [Pillow](https://pillow.readthedocs.io/en/stable/)
* Unit tests with `qpdf`-based PDF diffing
* PDF samples validation using 3 different checkers:

[![QPDF logo](qpdf-logo.svg)](https://github.com/qpdf/qpdf)
[![PDF Checker logo](pdfchecker-logo.png)](https://www.datalogics.com/products/pdf-tools/pdf-checker/)
[![VeraPDF logo](vera-logo.jpg)](https://verapdf.org)

FPDF original features:

* Choice of measurement unit, page format and margins
* Page header and footer management
* Automatic page break, line break and text justification
* Image, colors and links support
* Page compression

## Tutorials ##

* [English](https://pyfpdf.github.io/fpdf2/Tutorial.html)
* [Spanish](https://pyfpdf.github.io/fpdf2/Tutorial-es.html)
* [हिंदी](https://pyfpdf.github.io/fpdf2/Tutorial-हिंदी.html)
* [Русский](https://pyfpdf.github.io/fpdf2/Tutorial-ru.html)

## Installation ##

* From [PyPI](https://pypi.python.org/pypi/fpdf2): `pip install fpdf2`
* From source:
    * Clone the repository: `git clone https://github.com/PyFPDF/fpdf2.git`
    * On ubuntu the following packages are required: `sudo apt-get install libjpeg-dev libpython-dev zlib1g-dev`
    * Run `python setup.py install`

## Support ##

For community support, please feel free to file an [issue](https://github.com/PyFPDF/fpdf2/issues)
or [open a discussion](https://github.com/PyFPDF/fpdf2/discussions).

## Misc ##

* Release notes: [CHANGELOG.md](https://github.com/PyFPDF/fpdf2/blob/master/CHANGELOG.md)
* This library could only exist thanks to the dedication of many volunteers around the world:
  [list & map of contributors](https://github.com/PyFPDF/fpdf2/blob/master/README.md#contributors-)
* Looking for alternatives? Check out [this detailed list of PDF-related Python libs by Patrick Maupin](https://github.com/pmaupin/pdfrw#other-libraries). There is also `pikepdf`, `PyFPDF2` & `WeasyPrint`.
