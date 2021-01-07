[![Pull Requests Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat)](http://makeapullrequest.com)
[![build status](https://github.com/alexanderankin/pyfpdf/workflows/build/badge.svg)](https://github.com/alexanderankin/pyfpdf/actions?query=workflow%3Abuild)
[![Pypi latest version](https://img.shields.io/pypi/v/fpdf2.svg)](https://pypi.python.org/pypi/fpdf2)
[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![codecov](https://codecov.io/gh/alexanderankin/pyfpdf/branch/master/graph/badge.svg)](https://codecov.io/gh/alexanderankin/pyfpdf)

pyfpdf: FPDF for Python
=======================

Minimalist PDF creation library for Python

```python
from fpdf import FPDF

document = FPDF()
document.add_page()
document.set_font('Arial', size=12)
document.cell(w=0, txt="hello world")
document.output("hello_world.pdf")
```

PyFPDF is a library for PDF document generation under Python, ported from PHP
(see [FPDF](http://www.fpdf.org/): "Free"-PDF, a well-known PDFlib-extension
replacement with many examples, scripts and derivatives).

Compared with other PDF libraries, PyFPDF is simple, small and versatile, with
advanced capabilities, and is easy to learn, extend and maintain.

Looking for Developer Help!

Installation Instructions:
--------------------------

You can [install PyFPDF from PyPI][1], with easyinstall or from Windows 
installers. For example, using pip:

```bash
pip install fpdf2
```

To get the latest development version you can download the source code
running, you will need Pillow (`pip install pillow`)

```
# Linux only:
sudo apt-get install libjpeg-dev libpython-dev zlib1g-dev # libpython3.3-dev #(if necessary)

# Linux and Windows:
git clone https://github.com/alexanderankin/pyfpdf.git
cd pyfpdf
python setup.py install
```

Features:
---------

 * Python 3.6+ support (2.7 not supported since version 2.1)
 * Unicode (UTF-8) TrueType font subset embedding
 * Internal/External Links
 * PNG, GIF and JPG support (including transparency and alpha channel)
 * Shape, Line Drawing
 * Cell/Multi-cell/Plaintext writing, Automatic page breaks
 * Basic html2pdf (Templates with a visual designer in the works)
 * Exceptions support, other minor fixes, improvements and PEP8 code cleanups
 * Unit tests with `qpdf`-based PDF diffing

Release notes: [CHANGELOG.md](https://github.com/alexanderankin/pyfpdf/blob/master/CHANGELOG.md)

Documentation:
--------------

[Documentation Home](https://alexanderankin.github.io/pyfpdf/).

Also read the design-spec/tests, they're great.

Developers:
-----------

Please check [the docs page dedicated to developpement](https://alexanderankin.github.io/pyfpdf/Development.html).

Lets try to improve the Code Coverage statistic so that we can safely
transition to external font and image libraries, and more...

[1]: https://pypi.org/project/fpdf2/
[2]: https://pypi.org/project/fpdf2/2.0.2/
[3]: https://pypi.org/project/fpdf2/2.1.0rc1/
