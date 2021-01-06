Changelog:
--------

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [2.2.0] - not released yet
### Added
- new unit tests, a code formatter (`black`) and a linter (`pylint`) to improve code quality
### Changed
- the documentation URL is now simply https://alexanderankin.github.io/pyfpdf/
### Removed
- dropped support for external font definitions in `.font` Python files, that relied on a call to `exec`
### Deprecated
- the `type` parameter of `FPDF.image` method
- the `infile` parameter of `Template` constructor

## [2.1.0] - 2020-12-07
### Added
* [Introducing a rect_clip() function](https://github.com/reingart/pyfpdf/pull/158)
* [Adding support for Contents alt text on Links](https://github.com/reingart/pyfpdf/pull/163)
### Modified
* [Making FPDF.output() x100 time faster by using a bytearray buffer](https://github.com/reingart/pyfpdf/pull/164)
* Fix user's font path ([issue](https://github.com/reingart/pyfpdf/issues/166) [pr](https://github.com/alexanderankin/pyfpdf/pull/14))
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
