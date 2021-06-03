[![build status](https://github.com/PyFPDF/fpdf2/workflows/build/badge.svg)](https://github.com/PyFPDF/fpdf2/actions?query=branch%3Amaster)
[![Pypi latest version](https://img.shields.io/pypi/v/fpdf2.svg)](https://pypi.python.org/pypi/fpdf2)
[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![codecov](https://codecov.io/gh/PyFPDF/fpdf2/branch/master/graph/badge.svg)](https://codecov.io/gh/PyFPDF/fpdf2)

[![](https://img.shields.io/github/contributors/PyFPDF/fpdf2.svg)](https://github.com/PyFPDF/fpdf2/graphs/contributors)
[![Pull Requests Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat)](http://makeapullrequest.com)
[![first-timers-only Friendly](https://img.shields.io/badge/first--timers--only-friendly-blue.svg)](http://www.firsttimersonly.com/)
-> come look at our [good first issues](https://github.com/PyFPDF/fpdf2/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)

fpdf2
=====

![fpdf2 logo](https://pyfpdf.github.io/fpdf2/fpdf2-logo.png)

`fpdf2` is a minimalist PDF creation library for Python:

```python
from fpdf import FPDF

document = FPDF()
document.add_page()
document.set_font('helvetica', size=12)
document.cell(txt="hello world")
document.output("hello_world.pdf")
```

It is a fork and the successor of `PyFPDF`.
Compared with other PDF libraries, `fpdf2` is simple, small and versatile, with
advanced capabilities, and is easy to learn, extend and maintain.

Looking for Developer Help!

Installation Instructions:
--------------------------
```bash
pip install fpdf2
```

To get the latest development version:

```bash
# Linux only:
sudo apt-get install libjpeg-dev libpython-dev zlib1g-dev # libpython3.3-dev #(if necessary)

# Linux and Windows:
git clone https://github.com/PyFPDF/fpdf2.git
cd fpdf2
python setup.py install
```

Features:
---------

 * Python 3.6+ support
 * Unicode (UTF-8) TrueType font subset embedding
 * Internal/External Links
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

We validate all our PDF samples using 3 different checkers:

[![QPDF logo](https://pyfpdf.github.io/fpdf2/qpdf-logo.svg)](https://github.com/qpdf/qpdf)
[![PDF Checker logo](https://pyfpdf.github.io/fpdf2/pdfchecker-logo.png)](https://www.datalogics.com/products/pdf-tools/pdf-checker/)
[![VeraPDF logo](https://pyfpdf.github.io/fpdf2/vera-logo.jpg)](https://verapdf.org)

Documentation:
--------------

- [Documentation Home](https://pyfpdf.github.io/fpdf2/)
- [Tutorial](https://pyfpdf.github.io/fpdf2/Tutorial.html) (Spanish translation available)
- Release notes: [CHANGELOG.md](https://github.com/PyFPDF/fpdf2/blob/master/CHANGELOG.md)

You can also have a look at the `tests/`, they're great usage examples!

Developers:
-----------

Please check [the documentation page dedicated to development](https://pyfpdf.github.io/fpdf2/Development.html).

This library was only possible thanks to the dedication of the following people: [CONTRIBUTORS.md](CONTRIBUTORS.md).

Other libraries
---------------

For alternatives, check out [this detailed list of PDF-related Python libs by Patrick Maupin](https://github.com/pmaupin/pdfrw#other-libraries). There is also `pikepdf`, `PyFPDF2` & `WeasyPrint`.
