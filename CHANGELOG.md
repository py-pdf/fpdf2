Changelog:
--------

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/),
and [PEP 440](https://www.python.org/dev/peps/pep-0440/).

## [2.3.1] - not released yet
### Added
- `FPDF.set_margin` : new method to set the document right, left, top & bottom margins to the same value at once
- `FPDF.image` now accepts new optional `title` & `alt_text` parameters defining the image title
  and alternative text describing it, for accessibility purposes
- `FPDF.link` now honor its `alt_text` optional parameter and this alternative text describing links
  is now properly included in the resulting PDF document
- the document language can be set using `FPDF.set_lang`
### Fixed
- `FPDF.unbreakable` so that no extra page jump is performed when `FPDF.multi_cell` is called inside this context
### Deprecated
- `fpdf.FPDF_CACHE_MODE` & `fpdf.FPDF_CACHE_DIR` in favor of a configurable new `font_cache_dir` optional argument of the `fpdf.FPDF` constructor

## [2.3.0] - 2021-01-29
Many thanks to [@eumiro](https://github.com/PyFPDF/fpdf2/pulls?q=is%3Apr+author%3Aeumiro) & [@fbernhart](https://github.com/PyFPDF/fpdf2/pulls?q=is%3Apr+author%3Aeumiro) for their contributions to make `fpdf2` code cleaner!
### Added
- `FPDF.unbreakable` : a new method providing a context-manager in which automatic page breaks are disabled.
  _cf._ https://pyfpdf.github.io/fpdf2/PageBreaks.html
- `FPDF.epw` & `FPDF.eph` : new `@property` methods to retrieve the **effective page width / height**, that is the page width / height minus its horizontal / vertical margins.
- `FPDF.image` now accepts also a `Pillow.Image.Image` as input
- `FPDF.multi_cell` parameters evolve in order to generate tables with multiline text in cells:
  * its `ln` parameter now accepts a value of `3` that sets the new position to the right without altering vertical offset
  * a new optional `max_line_height` parameter sets a maximum height of each sub-cell generated
- new documentation pages : how to add content to existing PDFs, HTML, links, tables, text styling & page breaks
- all PDF samples are now validated using 3 different PDF checkers
### Fixed
- `FPDF.alias_nb_pages`: fixed this feature that was broken since v2.0.6
- `FPDF.set_font`: fixed a bug where calling it several times, with & without the same parameters,
prevented strings passed first to the text-rendering methods to be displayed.
### Deprecated
- the `dest` parameter of `FPDF.output` method

## [2.2.0] - 2021-01-11
### Added
- new unit tests, a code formatter (`black`) and a linter (`pylint`) to improve code quality
- new boolean parameter `table_line_separators` for `HTMLMixin.write_html` & underlying `HTML2FPDF` constructor
### Changed
- the documentation URL is now simply https://pyfpdf.github.io/fpdf2/
### Removed
- dropped support for external font definitions in `.font` Python files, that relied on a call to `exec`
### Deprecated
- the `type` parameter of `FPDF.image` method
- the `infile` parameter of `Template` constructor
- the `dest` parameter of `Template.render` method

## [2.1.0] - 2020-12-07
### Added
* [Introducing a rect_clip() function](https://github.com/reingart/pyfpdf/pull/158)
* [Adding support for Contents alt text on Links](https://github.com/reingart/pyfpdf/pull/163)
### Modified
* [Making FPDF.output() x100 time faster by using a bytearray buffer](https://github.com/reingart/pyfpdf/pull/164)
* Fix user's font path ([issue](https://github.com/reingart/pyfpdf/issues/166) [PR](https://github.com/PyFPDF/fpdf2/pull/14))
### Deprecated
* [Deprecating .rotate() and introducing .rotation() context manager](https://github.com/reingart/pyfpdf/pull/161)
### Fixed
* [Fixing #159 issue with set_link + adding GitHub Actions pipeline & badges](https://github.com/reingart/pyfpdf/pull/160)
* `User defined path to font is ignored`
### Removed
* non-necessary dependency on `numpy`
* support for Python 2
 
## [2.0.6] - 2020-10-26
### Added
* Python 3.9 is now supported

## [2.0.5] - 2020-04-01
### Added
* new specific exceptions: `FPDFException` & `FPDFPageFormatException`
* tests to increase line coverage in `image_parsing` module
* a test which uses most of the HTML features
### Fixed
* handling of fonts by the HTML mixin (weight and style) - thanks `cgfrost`!

## [2.0.4] - 2020-03-26
### Fixed
* images centering - thanks `cgfrost`!
* added missing import statment for `urlopen` in `image_parsing` module
* changed urlopen import from `six` library to maintain python2 compatibility

## [2.0.3] - 2020-01-03
### Added
* Ability to use a `BytesIO` buffer directly. This can simplify loading `matplotlib` plots into the PDF.
### Modified
* `load_resource` now return argument if type is `BytesIO`, else load.

## [2.0.1] - 2018-11-15
### Modified
* introduced a dependency to `numpy` to improve performances by replacing pixel regexes in image parsing (s/o @pennersr)

## [2.0.0] - 2017-05-04
### Added
* support for more recent Python versions
* more documentation
### Fixed
* PDF syntax error when version is > 1.3 due to an invalid `/Transparency` dict
### Modified
* turned `accept_page_break` into a property
* unit tests now use the standard `unittest` lib
* massive code cleanup using `flake8`
