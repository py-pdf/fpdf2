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

  * Python 2.7 to 3.5+ support
  * [Unicode](Unicode.md) (UTF-8) TrueType font subset embedding (Central European, Cyrillic, Greek, Baltic, Thai, Chinese, Japanese, Korean, Hindi and almost any other language in the world) **New!*  * based on [sFPDF](http://www.fpdf.org/en/script/script91.php) LGPL3 PHP version from [Ian Back](mailto:ian@bpm1.com?subject=sFPDF)
  * Improved installers (Python wheel) support
  * Barcode I2of5 and code39, QR code coming soon ...
  * PNG, GIF and JPG support (including transparency and alpha channel) **New!**
  * Exceptions support, other minor fixes, improvements and PEP8 code cleanups
  * Port of the [Tutorial](Tutorial.md) and [ReferenceManual](reference)  (Spanish translation available)

FPDF original features:

  * Choice of measurement unit, page format and margins
  * Page header and footer management
  * Automatic page break
  * Automatic line break and text justification
  * Image, colors and links support
  * Page compression
  * Extensive [Tutorial](http://www.fpdf.org/en/tutorial/index.php) and complete online [documentation](http://www.fpdf.org/en/doc/index.php)

## Installation ##

  * Using [PyPI](https://pypi.python.org/pypi/fpdf2)
    * Become super user if necessary: `sudo su`
    * `pip install fpdf2`
  * From source:
    * Clone the repository: `git clone --depth 1 --branch master https://github.com/PyFPDF/fpdf2.git`
    * Optional: Check out the version you want, `git tag -n`
    * This will require Pillow and other dependencies to be satisfied, or it will download the sources of those and compile those. On ubuntu this requires the following header packages: `sudo apt-get install libjpeg-dev libpython-dev zlib1g-dev # libpython3.3-dev #(if necessary)`
    * Run `python setup.py install`

## Support ##

For community support, please feel free to file an [issue](https://github.com/PyFPDF/fpdf2/issues).
