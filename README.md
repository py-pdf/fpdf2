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

## Contributors ✨

This library could only exist thanks to the dedication of many volunteers around the world:

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://github.com/reingart"><img src="https://avatars.githubusercontent.com/u/1041385?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Mariano Reingart</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=reingart" title="Code">💻</a></td>
    <td align="center"><a href="http://lymaconsulting.github.io/"><img src="https://avatars.githubusercontent.com/u/8921892?v=4?s=100" width="100px;" alt=""/><br /><sub><b>David Ankin</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/issues?q=author%3Aalexanderankin" title="Bug reports">🐛</a> <a href="https://github.com/PyFPDF/fpdf2/commits?author=alexanderankin" title="Code">💻</a> <a href="https://github.com/PyFPDF/fpdf2/commits?author=alexanderankin" title="Documentation">📖</a> <a href="#maintenance-alexanderankin" title="Maintenance">🚧</a> <a href="#question-alexanderankin" title="Answering Questions">💬</a> <a href="https://github.com/PyFPDF/fpdf2/pulls?q=is%3Apr+reviewed-by%3Aalexanderankin" title="Reviewed Pull Requests">👀</a> <a href="https://github.com/PyFPDF/fpdf2/commits?author=alexanderankin" title="Tests">⚠️</a></td>
    <td align="center"><a href="https://github.com/alexp1917"><img src="https://avatars.githubusercontent.com/u/66129071?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Alex Pavlovich</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/issues?q=author%3Aalexp1917" title="Bug reports">🐛</a> <a href="https://github.com/PyFPDF/fpdf2/commits?author=alexp1917" title="Code">💻</a> <a href="https://github.com/PyFPDF/fpdf2/commits?author=alexp1917" title="Documentation">📖</a> <a href="#question-alexp1917" title="Answering Questions">💬</a> <a href="https://github.com/PyFPDF/fpdf2/pulls?q=is%3Apr+reviewed-by%3Aalexp1917" title="Reviewed Pull Requests">👀</a> <a href="https://github.com/PyFPDF/fpdf2/commits?author=alexp1917" title="Tests">⚠️</a></td>
    <td align="center"><a href="https://chezsoi.org/lucas/blog/"><img src="https://avatars.githubusercontent.com/u/925560?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Lucas Cimon</b></sub></a><br /><a href="#blog-Lucas-C" title="Blogposts">📝</a> <a href="https://github.com/PyFPDF/fpdf2/commits?author=Lucas-C" title="Code">💻</a> <a href="https://github.com/PyFPDF/fpdf2/commits?author=Lucas-C" title="Documentation">📖</a> <a href="#infra-Lucas-C" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="#maintenance-Lucas-C" title="Maintenance">🚧</a> <a href="#question-Lucas-C" title="Answering Questions">💬</a></td>
    <td align="center"><a href="https://github.com/eumiro"><img src="https://avatars.githubusercontent.com/u/6774676?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Miroslav Šedivý</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=eumiro" title="Code">💻</a> <a href="https://github.com/PyFPDF/fpdf2/commits?author=eumiro" title="Tests">⚠️</a></td>
    <td align="center"><a href="https://github.com/fbernhart"><img src="https://avatars.githubusercontent.com/u/70264417?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Florian Bernhart</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=fbernhart" title="Code">💻</a> <a href="https://github.com/PyFPDF/fpdf2/commits?author=fbernhart" title="Tests">⚠️</a></td>
    <td align="center"><a href="http://pr.linkedin.com/in/edwoodocasio/"><img src="https://avatars.githubusercontent.com/u/82513?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Edwood Ocasio</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=eocasio" title="Code">💻</a> <a href="https://github.com/PyFPDF/fpdf2/commits?author=eocasio" title="Tests">⚠️</a></td>
  </tr>
  <tr>
    <td align="center"><a href="https://github.com/marcelotduarte"><img src="https://avatars.githubusercontent.com/u/12752334?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Marcelo Duarte</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=marcelotduarte" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/RomanKharin"><img src="https://avatars.githubusercontent.com/u/6203756?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Roman Kharin</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=RomanKharin" title="Code">💻</a> <a href="#ideas-RomanKharin" title="Ideas, Planning, & Feedback">🤔</a></td>
    <td align="center"><a href="https://github.com/cgfrost"><img src="https://avatars.githubusercontent.com/u/166104?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Christopher Frost</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/issues?q=author%3Acgfrost" title="Bug reports">🐛</a> <a href="https://github.com/PyFPDF/fpdf2/commits?author=cgfrost" title="Code">💻</a></td>
    <td align="center"><a href="http://www.ne.ch/sitn"><img src="https://avatars.githubusercontent.com/u/1681332?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Michael Kalbermatten</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/issues?q=author%3Akalbermattenm" title="Bug reports">🐛</a> <a href="https://github.com/PyFPDF/fpdf2/commits?author=kalbermattenm" title="Code">💻</a></td>
    <td align="center"><a href="https://yanone.de/"><img src="https://avatars.githubusercontent.com/u/175386?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Yanone</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=yanone" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/leoleozhu"><img src="https://avatars.githubusercontent.com/u/738445?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Leo Zhu</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=leoleozhu" title="Code">💻</a></td>
    <td align="center"><a href="https://www.abishekgoda.com/"><img src="https://avatars.githubusercontent.com/u/310520?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Abishek Goda</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=abishek" title="Code">💻</a></td>
  </tr>
  <tr>
    <td align="center"><a href="https://www.cd-net.net/"><img src="https://avatars.githubusercontent.com/u/1515637?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Arthur Moore</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=EmperorArthur" title="Code">💻</a> <a href="https://github.com/PyFPDF/fpdf2/commits?author=EmperorArthur" title="Tests">⚠️</a></td>
    <td align="center"><a href="https://boghison.com/"><img src="https://avatars.githubusercontent.com/u/7976283?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Bogdan Cuza</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=boghison" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/craigahobbs"><img src="https://avatars.githubusercontent.com/u/1263515?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Craig Hobbs</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=craigahobbs" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/xitrushiy"><img src="https://avatars.githubusercontent.com/u/17336659?v=4?s=100" width="100px;" alt=""/><br /><sub><b>xitrushiy</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/issues?q=author%3Axitrushiy" title="Bug reports">🐛</a> <a href="https://github.com/PyFPDF/fpdf2/commits?author=xitrushiy" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/jredrejo"><img src="https://avatars.githubusercontent.com/u/1008178?v=4?s=100" width="100px;" alt=""/><br /><sub><b>José L. Redrejo Rodríguez</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=jredrejo" title="Code">💻</a></td>
    <td align="center"><a href="https://jugmac00.github.io/"><img src="https://avatars.githubusercontent.com/u/9895620?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Jürgen Gmach</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=jugmac00" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/Larivact"><img src="https://avatars.githubusercontent.com/u/8731884?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Larivact</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=Larivact" title="Code">💻</a></td>
  </tr>
  <tr>
    <td align="center"><a href="https://github.com/leonelcamara"><img src="https://avatars.githubusercontent.com/u/1198145?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Leonel Câmara</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=leonelcamara" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/mark-steadman"><img src="https://avatars.githubusercontent.com/u/15779053?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Mark Steadman</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/issues?q=author%3Amark-steadman" title="Bug reports">🐛</a> <a href="https://github.com/PyFPDF/fpdf2/commits?author=mark-steadman" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/sergeyfitts"><img src="https://avatars.githubusercontent.com/u/40498252?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Sergey</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=sergeyfitts" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/Stan-C421"><img src="https://avatars.githubusercontent.com/u/82440217?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Stan-C421</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=Stan-C421" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/viraj-shah18"><img src="https://avatars.githubusercontent.com/u/44942391?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Viraj Shah</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=viraj-shah18" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/cornicis"><img src="https://avatars.githubusercontent.com/u/11545033?v=4?s=100" width="100px;" alt=""/><br /><sub><b>cornicis</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=cornicis" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/moe-25"><img src="https://avatars.githubusercontent.com/u/85580959?v=4?s=100" width="100px;" alt=""/><br /><sub><b>moe-25</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=moe-25" title="Code">💻</a></td>
  </tr>
  <tr>
    <td align="center"><a href="https://github.com/niphlod"><img src="https://avatars.githubusercontent.com/u/122119?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Simone Bizzotto</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/commits?author=niphlod" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/bnyw"><img src="https://avatars.githubusercontent.com/u/32655514?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Boonyawe Sirimaha</b></sub></a><br /><a href="https://github.com/PyFPDF/fpdf2/issues?q=author%3Abnyw" title="Bug reports">🐛</a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification
([emoji key](https://allcontributors.org/docs/en/emoji-key)).
Contributions of any kind welcome!

[![Contributors map](https://pyfpdf.github.io/fpdf2/contributors-map-small.png)](https://pyfpdf.github.io/fpdf2/contributors.html)

_(screenshot from June 2021, click on the map above to access an up-to-date online version)_

Other libraries
---------------

For alternatives, check out [this detailed list of PDF-related Python libs by Patrick Maupin](https://github.com/pmaupin/pdfrw#other-libraries). There is also `pikepdf`, `PyFPDF2` & `WeasyPrint`.
