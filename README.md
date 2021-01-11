[![Pull Requests Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat)](http://makeapullrequest.com)
[![build status](https://github.com/PyFPDF/fpdf2/workflows/build/badge.svg)](https://github.com/PyFPDF/fpdf2/actions?query=branch%3Amaster)
[![Pypi latest version](https://img.shields.io/pypi/v/fpdf2.svg)](https://pypi.python.org/pypi/fpdf2)
[![License: LGPL v3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![codecov](https://codecov.io/gh/PyFPDF/fpdf2/branch/master/graph/badge.svg)](https://codecov.io/gh/PyFPDF/fpdf2)

fpdf2
=====

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
 * Cell/Multi-cell/Plaintext writing, Automatic page breaks
 * Basic html2pdf (Templates with a visual designer in the works)
 * Exceptions support, other minor fixes, improvements and PEP8 code cleanups
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
