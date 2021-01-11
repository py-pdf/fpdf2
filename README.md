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

![fpdf2 logo](docs/fpdf2-logo.png)

`fpdf2` is a minimalist PDF creation library for Python:

```python
from fpdf import FPDF

document = FPDF()
document.add_page()
document.set_font('Arial', size=12)
document.cell(w=0, txt="hello world")
document.output("hello_world.pdf")
```

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
 * Generate [Code 39](https://fr.wikipedia.org/wiki/Code_39) & [Interleaved 2 of 5](https://en.wikipedia.org/wiki/Interleaved_2_of_5) barcodes
 * Cell/Multi-cell/Plaintext writing, Automatic page breaks
 * Basic conversion from HTML to PDF
 * Clean error handling through exceptions
 * Only **one** dependency so far: [Pillow](https://pillow.readthedocs.io/en/stable/)
 * Unit tests with `qpdf`-based PDF diffing

Release notes: [CHANGELOG.md](https://github.com/PyFPDF/fpdf2/blob/master/CHANGELOG.md)

Documentation:
--------------

- [Documentation Home](https://pyfpdf.github.io/fpdf2/)
- [FAQ](https://pyfpdf.github.io/fpdf2/FAQ/index.html)
- [Tutorial](https://pyfpdf.github.io/fpdf2/Tutorial.html) (Spanish translation available)
- [Reference Manual](https://pyfpdf.github.io/fpdf2/ReferenceManual.html)

Also read the design-spec/tests, they're great.

Developers:
-----------

Please check [the docs page dedicated to developpement](https://pyfpdf.github.io/fpdf2/Development.html).

Lets try to improve the Code Coverage statistic so that we can safely
transition to external font and image libraries, and more...
