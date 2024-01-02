Changelog
---------

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/),
and [PEP 440](https://www.python.org/dev/peps/pep-0440/).

## Displaying deprecation warnings
`DeprecationWarning` messages are not displayed by Python by default.

Hence, every time you use a newer version of `fpdf2`, we strongly encourage you to execute your scripts
with the `-Wd` option (_cf._ [documentation](https://docs.python.org/3/using/cmdline.html#cmdoption-W)) 
in order to get warned about deprecated features used in your code.

This can also be enabled programmatically with `warnings.simplefilter('default', DeprecationWarning)`.

## [2.7.8] - Not released yet
### Added
* support for `<path>` elements in SVG `<clipPath>` elements
### Fixed
* when adding a link on a table cell, an extra link was added erroneously on the left. Moreover, now `FPDF._disable_writing()` properly disable link writing.
* non-bold `TitleStyle` is now rendered as non-bold even when the current font is bold
* calling `.table()` inside the `render_toc_function`

## [2.7.7] - 2023-12-10
### Added
* Basic support for `<image>` elements in SVG vector graphics inserted
* SVG importing now supports clipping paths, and `<defs>` tags anywhere in the SVG file - thanks to @afriedman412 - cf. [#968](https://github.com/py-pdf/fpdf2/pull/968)
* [`FPDF.fonts.FontFace`](https://py-pdf.github.io/fpdf2/fpdf/fonts.html#fpdf.fonts.FontFace): Now has a static `combine` method that allows overriding a default FontFace (e.g. for specific cells in a table). Unspecified properties of the override FontFace retain the values of the default - thanks to @TedBrookings - cf. [#979](https://github.com/py-pdf/fpdf2/pull/979)
* [`TextColumns()`](https://py-pdf.github.io/fpdf2/TextColumns.html) can now have images inserted (both raster and vector) - thanks to @gmischler
* [`TextColumns()`](https://py-pdf.github.io/fpdf2/TextColumns.html) can now advance to the next column with the new `new_column()` method or a FORM_FEED character (`\u000c`) in the text - thanks to @gmischler
* Added support for Free Text annotations: [documentation](https://py-pdf.github.io/fpdf2/Annotations.html#free-text-annotations) - thanks to @MarekT0v - cf. [#1039](https://github.com/py-pdf/fpdf2/pull/1039)
* Tutorial in Dutch: [Handleiding](https://py-pdf.github.io/fpdf2/Tutorial-nl.md) - thanks to @Polderrider
* Python 3.12 is now officially supported
### Fixed
* Links over text in tables were broken in release 2.7.6, this is now fixed
* `FPDF.set_font_color()` raised a `TypeError` when used in tables
* `FPDF.image(x=Align.C)` used to fail for SVG images - fixed thanks to @gmischler - cf. [#1003](https://github.com/py-pdf/fpdf2/pull/1003)
* Previously set dash patterns were not transferred correctly to new pages - fixed thanks to @gmischler - cf. [#993](https://github.com/py-pdf/fpdf2/pull/993)
* Inserted Vector images used to ignore the `keep_aspect_ratio` argument.
* [`FPDF.write_html()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write_html) now properly honor the current text font color when styling table cells
* [`FPDF.write_html()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write_html) delays unescaping data so as not to confuse entity names as nested tags
* [`FPDF.multi_cell()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) has improved handling of `new_x` and `new_y` when `padding` is non-zero.
* [`FPDF.multi_cell(fill=True)`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) now avoids overlapping multiline strings when `padding` is non-zero.
### Changed
* the public `.images`, `.icc_profiles` & `.image_filter` attributes of `FPDF` instances have been moved inside a nested `FPDF.image_cache` attribute. Similarly, the `FPDF.preload_image()` is now a function in the `fpdf.image_parsing` module: [documentation](https://py-pdf.github.io/fpdf2/fpdf/image_parsing.html#fpdf.image_parsing.preload_image)
* the `fpdf.svg` module now produces `WARNING` log messages for unsupported SVG tags & attributes.
  If those logs annoy you, you can suppress them: `logging.getLogger("fpdf.svg").propagate = False`
* [`FPDF.table()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.table): If cell styles are provided for cells in heading rows, combine the cell style as an override with the overall heading style.

## [2.7.6] - 2023-10-11
This release is the first performed from the [@py-pdf GitHub org](https://github.com/py-pdf), where `fpdf2` migrated.
This release also marks the arrival of two new maintainers: Georg Mischler ([@gmischler](https://github.com/gmischler)) and Anderson Herzogenrath da Costa ([@andersonhc](https://github.com/andersonhc)).
### Added
* The new experimental method `text_columns()` allows to render text within a single or multiple columns, including height balancing: [documentation](https://py-pdf.github.io/fpdf2/TextColumns.html) - thanks to @gmischler
* [`FPDF.table()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.table): Now supports padding in cells : [documentation](https://py-pdf.github.io/fpdf2/Tables.html#table-with-multiple-heading-rows) - thanks to @RubendeBruin
* [`FPDF.table()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.table): Now supports vertical alignment in cells : [documentation](https://py-pdf.github.io/fpdf2/Tables.html#setting-vertical-alignment-of-text-in-cells) - thanks to @RubendeBruin
* [`FPDF.table()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.table): Now supports outer border width for rendering the outer border of the table with a different line-width - thanks to @RubendeBruin
* [`FPDF.table()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.table): Now supports multiple heading rows : [documentation](https://py-pdf.github.io/fpdf2/Tables.html#table-with-multiple-heading-rows) - thanks to @SandraFer
* [`FPDF.write_html()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write_html) now supports heading colors defined as attributes (_e.g._ `<h2 color="#00ff00">...`) - thanks to @Lucas-C
* documentation on how to use `livereload` to enable a "watch" mode with PDF generation: [Combine with livereload](https://py-pdf.github.io/fpdf2/CombineWithLivereload.html) - thanks to @Lucas-C
### Changed
* [`FPDF.write_html()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write_html): the formatting output has changed in some aspects. Vertical spacing around headings and paragraphs may be slightly different, and elements at the top of the page don't have any extra spacing above anymore.
* [`FPDF.table()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.table): If the height of a row is governed by an image, then the default vertical alignment of the other cells is "center". This was "top". 
* variable-width non-breaking space (NBSP) support [issue #834](https://github.com/PyFPDF/fpdf2/issues/834)
This change was made for consistency between row-height governed by text or images. The old behaviour can be enforced using the new vertical alignment parameter.
### Fixed
* [`FPDF.table()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.table) & [`FPDF.multi_cell()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell): when some horizontal padding was set, the text was not given quite enough space - thanks to @gmischler
* [`FPDF.write_html()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write_html) can now handle formatting tags within paragraphs without adding extra line breaks (except in table cells for now) - thanks to @gmischler
* [`FPDF.write_html()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write_html): the font size in HTML `<pre>` and `<code>` tags is not fixed to 11 pica anymore, but adapts to the preceding text - thanks to @gmischler
* [`FPDF.ln()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.ln), when called before any text has been written, will now use the current font height instead of doing nothing - thanks to @gmischler -  _cf._ issue [#937](https://github.com/py-pdf/fpdf2/issues/937)
* [`FPDF.image()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image), when provided a `BytesIO` instance, does not close it anymore - _cf._ issue [#881](https://github.com/py-pdf/fpdf2/issues/881) - thanks to @Lucas-C
* Invalid characters were being generated when a string contains parentheses - thanks to @andersonhc - _cf._ issue [#884](https://github.com/py-pdf/fpdf2/issues/884)
* Frozen Glyph dataclass was causing problems for FPDFRecorder with TTF fonts - thanks to @andersonhc - _cf._ issue [#890](https://github.com/py-pdf/fpdf2/issues/890)
* Edge case when parsing a Markdown link followed by a newline - _cf._ issue [#916](https://github.com/py-pdf/fpdf2/issues/916), and when bold/italics/underline markers are repeated
* Zoom not set correctly when a numeric value was set in [`set_display_mode()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_display_mode) - _cf._ issue [#926](https://github.com/py-pdf/fpdf2/issues/926)
* [`FPDF.table()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.table): images no longer overlap with cell borders - thanks to @RubendeBruin - _cf._ issue [#892](https://github.com/py-pdf/fpdf2/issues/892)
* Encryption of strings containing non-latin characters - thanks to @andersonhc - _cf._ issue [#933](https://github.com/py-pdf/fpdf2/issues/933)
* Handling of fragments with zero-length - thanks to @SaiHarshaK - _cf._ issue [#902](https://github.com/py-pdf/fpdf2/issues/902)
### Deprecated
* to improve naming consistency, the `txt` parameters of `FPDF.cell()`, `FPDF.multi_cell()`, `FPDF.text()` & `FPDF.write()` have been renamed to `text`

## [2.7.5] - 2023-08-04
### Added
- [`FPDF.set_text_shaping()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_shaping): new method to perform text shaping using **Harfbuzz** - [documentation](https://py-pdf.github.io/fpdf2/TextShaping.html) - thanks to @andersonhc in [PR #820](https://github.com/py-pdf/fpdf2/pull/820)
- [`FPDF.mirror()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.mirror) - New method: [documentation page](https://py-pdf.github.io/fpdf2/Transformations.html) - Contributed by @sebastiantia
- [`FPDF.table()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.table): new optional parameters `gutter_height`, `gutter_width` and `wrapmode`. Links can also be added to cells by passing a `link` parameter to [`Row.cell()`](https://py-pdf.github.io/fpdf2/fpdf/table.html#fpdf.table.Row.cell)
- [`FPDF.multi_cell()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell): has a new optional `center` parameter to position the cell horizontally at the center of the page
- New AES-256 encryption: [documentation](https://py-pdf.github.io/fpdf2/Encryption.html#encryption-method) - thanks to @andersonhc in [PR #872](https://github.com/py-pdf/fpdf2/pull/872)
- Added tutorial in Khmer language: [ភាសខ្មែរ](https://py-pdf.github.io/fpdf2/Tutorial-km.html) - thanks to @kuth-chi
- Added tutorial in [日本語](https://py-pdf.github.io/fpdf2/Tutorial-ja.html) - thanks to @alcnaka
- Better documentation & errors when facing HTML rendering limitations for `<table>` tags: <https://py-pdf.github.io/fpdf2/HTML.html>
### Fixed
- [`FPDF.table()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.table): the `colspan` setting has been fixed - [documentation](https://py-pdf.github.io/fpdf2/Tables.html#column-span)
- [`FPDF.image()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image): allowing images path starting with `data` to be passed as input
- text overflow is better handled by `FPDF.write()` & `FPDF.write_html()` - _cf._ [issue #847](https://github.com/py-pdf/fpdf2/issues/847)
- the initial text color is preserved when using `FPDF.write_html()` - _cf._ [issue #846](https://github.com/py-pdf/fpdf2/issues/846)
- PDF metadata not encrypted - _cf._ [issue #865](https://github.com/py-pdf/fpdf2/issues/865)
- handle superscript and subscript correctly when rendering `TextLine`- thanks to @Tolker-KU - _cf._ [Pull Request #862](https://github.com/py-pdf/fpdf2/pull/862)
- make sure warnings always point to the users code - _cf._ [Pull request #869](https://github.com/py-pdf/fpdf2/pull/869)
### Deprecated
- the `center` optional parameter of [`FPDF.cell()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.cell) is **no more** deprecated, as it allows for horizontal positioning, which is different from text alignment control with `align="C"`

## [2.7.4] - 2023-04-28
### Added
- [`FPDF.image()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image): CMYK images can now be inserted directly by passing them into the image method. Contributed by @devdev29
- documentation on how to embed `graphs` and `charts` generated using `Pygal` lib: [documentation section](https://py-pdf.github.io/fpdf2/Maths.html#using-pygal) - thanks to @ssavi-ict
- documentation on how to use `fpdf2` with [FastAPI](https://fastapi.tiangolo.com/): <https://py-pdf.github.io/fpdf2/UsageInWebAPI.html#FastAPI> - thanks to @KamarulAdha
- [`FPDF.write_html()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write_html): `<table>` elements can now be aligned left or right on the page using `align=`
- [`FPDF.write_html()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write_html): a custom font can now be specified for `<code>` & `<pre>` elements, using the new optional parameter `pre_code_font`
### Fixed
- [`FPDF.table()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.table): images no more overflow cells
- [`FPDF.table()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.table): text overflow in the last cell of the header row is now properly handled
- [`FPDF.table()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.table): when `align="RIGHT"` is provided, the page right margin is now properly taken in consideration
### Changed
- [`FPDF.write_html()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write_html) does not render the top row as a header, in bold with a line below, when no `<th>` are used, in order to be more backward-compatible with earlier versions of `fpdf2` - _cf._ [#740](https://github.com/py-pdf/fpdf2/issues/740)
### Deprecated
- the `split_only` optional parameter of [`FPDF.multi_cell()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell), which is replaced by two new distincts optional parameters: `dry_run` & `output`

## [2.7.3] - 2023-04-03
### Fixed
- removed a debug `print()` statement left in `output.py:OutputProducer._add_fonts()` 🤦‍♂️ - A rule was also added to `.pre-commit-config.yaml` to avoid this to happen again.

## [2.7.2] - 2023-04-03
### Fixed
- custom fonts can be used with `FPDF.table()` without triggering a `TypeError: cannot pickle 'dict_keys' object` - thanks @aeris07 for the bug report
- the SVG parser now accepts `<rect>` with `width` / `height` defined as percents
### Added
- documentation on how to generate Code128 barcodes using the `python-barcode` lib: [documentation section](https://py-pdf.github.io/fpdf2/Barcodes.html#Code128)

## [2.7.1] - 2023-03-27
### Changed
- renamed `fonts.FontStyle` to [`fonts.FontFace`](https://py-pdf.github.io/fpdf2/fpdf/fonts.html#fpdf.fonts.FontFace), and `FPDF.use_font_style` to [`FPDF.use_font_face`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.FPDF.FPDF.use_font_face), to avoid confusions with `FPDF.font_style`
- new translation of the tutorial in [বাংলা](https://py-pdf.github.io/fpdf2/Tutorial-bn.html) - thanks to @ssavi-ict

## [2.7.0] - 2023-03-27
### Added
- new method [`FPDF.table()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.table): [documentation](https://py-pdf.github.io/fpdf2/Tables.html)
- [`FPDF.image()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image) has a new `keep_aspect_ratio` optional boolean parameter, to fit it inside a given rectangle: [documentation](https://py-pdf.github.io/fpdf2/Images.html#fitting-an-image-inside-a-rectangle)
- [`FPDF.multi_cell()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) and [`FPDF.write()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write) now accept a `wrapmode` argument for word or character based line wrapping ("WORD"/"CHAR"), thanks to @gmischler
- new method [`FPDF.set_fallback_fonts()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fallback_fonts) allow alternative fonts to be provided if a character on the text is not available on the currently set font - thanks to @andersonhc
- for inserted images that have an ICC Profile, this profile is now extracted and embedded; they should now be honored by PDF viewers - thanks to @eroux
- new methods: [`FPDF.preload_image()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.preload_image) & [`FPDF.use_font_style()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.use_font_style)
- new translation of the tutorial in [简体中文](https://py-pdf.github.io/fpdf2/Tutorial-zh.html) - thanks to @Bubbu0129
- documentation on how to embed static [Plotly](https://plotly.com/python/) charts: [link to docs](https://py-pdf.github.io/fpdf2/Maths.html)
- additional linter / static code analyser in GitHub Actions CI pipeline: [semgrep](https://github.com/returntocorp/semgrep)
### Fixed
- outlines & hyperlinks were not working on encrypted files - thanks to @andersonhc
- a bug was introduced in the previous release (2.6.1): `FPDF.set_link()` could not update links generated with `add_link()`
- unicode (non limited to ASCII) text can now be provided as metadata [#685](https://github.com/py-pdf/fpdf2/issues/685)
- all `TitleStyle` constructor parameters are now effectively optional
- memory usage was reduced by 10 MiB in some cases, thanks to a small optimization in using `fonttools`
### Changed
* [`FPDF.write_html()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write_html) now uses the new [`FPDF.table()`](https://py-pdf.github.io/fpdf2/Tables.html) method to render `<table>` tags. As a consequence, vertical space before `<table>` tags has sometimes been reduced.
- vector images parsing is now more robust: `fpdf2` can now embed SVG files without `viewPort` or no `height` / `width`
- bitonal images are now encoded using `CCITTFaxDecode`, reducing their size in the PDF document - thanks to @eroux
- when possible, JPG and group4 encoded TIFFs are now embedded directly without recompression - thanks to @eroux
### Removed
* [`FPDF.write_html()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write_html) now uses the new [`FPDF.table()`](https://py-pdf.github.io/fpdf2/Tables.html) method to render `<table>` tags. As a consequence, it does not support the `height` attribute defined on `<td>` / `<th>` tags anymore, nor `height` / `width` attributes defined on `<img>` tags inside cells, nor `width` attributes defined on `<thead>` / `<tfoot>` tags.

## [2.6.1] - 2023-01-13
### Added
* support for PDF **encryption** (RC4 and AES-128): [documentation page](https://py-pdf.github.io/fpdf2/Encryption.html) - thanks to @andersonhc
* [`FPDF.skew()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.skew) - New method: [documentation page](https://py-pdf.github.io/fpdf2/Transformations.html) - thanks to @erap129
* ensured support for Python 3.11
* [`FPDF.image()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image): the `x` parameter now accepts a value of `"C"` / `Align.C` / `"R"` / `Align.R` to horizontally position the image centered or aligned right
* [`FPDF.image()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image): dimensions can now be provided to set the intrinsic image width & height before storing it in the PDF
* [`FPDF.cell()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.cell) & [`FPDF.multi_cell()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell): support for `[]()` hyperlinks when `markdown=True`
* [`FPDF.write_html()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write_html): support for `line-height` attribute of paragraph (`<p>`) - thanks to @Bubbu0129
* documentation on [useful tools to manipulate PDFs](https://py-pdf.github.io/fpdf2/Development.html#useful-tools-to-manipulate-pdfs)
* show a warning if the font being used doesn't have all the necessary glyphs for the text - thanks to @andersonhc
### Changed
* [`FPDF.add_link()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_link) creates a link to the current page by default, and now accepts optional parameters: `x`, `y`, `page` & `zoom`.
  Hence calling [`set_link()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_link) is not needed anymore after creating a link with `add_link()`.
* [`FPDF.write_html()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write_html) now generates warnings for unclosed HTML tags, unless `warn_on_tags_not_matching=False` is set
### Fixed
* [`FPDF.write_html()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write_html): a `ValueError: Incoherent hierarchy` could be raised with some headings hierarchy
* [`FPDF.write_html()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write_html): `<img>` without `height` attribute overlaps with the following content [#632](https://github.com/py-pdf/fpdf2/issues/632) - thanks to @Bubbu0129
* [`FPDF.image()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image): performance issue with adding large images with `FlateDecode` image filter [#644](https://github.com/py-pdf/fpdf2/pull/644) - thanks to @Markovvn1
* [`FPDF.add_font()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_font): fix support for upper case font file name [#638](https://github.com/py-pdf/fpdf2/issues/638) - thanks to @CY-Qiu

## [2.6.0] - 2022-11-20
### Added
- demonstration Jupyter notebook: [tutorial/notebook.ipynb](https://github.com/py-pdf/fpdf2/blob/master/tutorial/notebook.ipynb)
- new [`.default_page_dimensions`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.default_page_dimensions) property on `FPDF` instances
- support for description list (`<dl>`), description titles (`<dt>`), description details (`<dd>`) and code blocks (`<code>`) in `write_html()` - thanks to @yk-jp & @seanpmulholland
- support for monochromatic images (PIL `image.mode == '1'`) thanks to @GerardoAllende
- the 1000+ unit tests suite is now executed under Linux **<ins>and</ins>** Windows, with extra timing & memory usage checks ensuring we control `fpdf2` resource usage
- new translation of the tutorial in [עברית](https://py-pdf.github.io/fpdf2/Tutorial-he.html), thanks to @TzviGreenfeld
- new documentation for using [PyPDF2](https://github.com/py-pdf/PyPDF2) with `fpdf2`, added by @devdev29: https://py-pdf.github.io/fpdf2/CombineWithPyPDF2.html
- new documentation for using [Jinja](https://jinja.palletsprojects.com/) with `fpdf2`: https://py-pdf.github.io/fpdf2/TemplatingWithJinja.html
### Deprecated
- `HTMLMixin` is deprecated, and not needed anymore: **the `write_html()` method is now natively available in the `FPDF` class** - thanks to @yk-jp
### Removed
- `open()` & `close()` methods, that were only used internally and should never have been called by end-user code
- `FPDF.state`, which was an instance of the `DocumentState` enum, and has been replaced by moving the final rendering logic into a new `fpdf.output` module
### Fixed
- after an "empty" `cell()`, `ln()` applied a line height of zero [#601](https://github.com/py-pdf/fpdf2/issues/601)
- when using `multi_cell()` with `max_line_height` to render multiline text, the last line is now rendered like all the others
- templates don't leak graphics state changes to their surroundings anymore; [#570](https://github.com/py-pdf/fpdf2/issues/570)
- automatic page break is never performed on an empty page (when the Y position is at the top margin)
- fixed [`insert_toc_placeholder()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.insert_toc_placeholder) usage with [`footer()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.footer) and `{{nb}}`; [#548](https://github.com/py-pdf/fpdf2/issues/548)
- the SVG parser now accepts `stroke-width` attribute values with an explicit unit, thanks to @gmischler; [#526](https://github.com/py-pdf/fpdf2/issues/526)
- the SVG parser now accepts absolute units for `width` and `height` attributes, thanks to @darioackermann; [#555](https://github.com/py-pdf/fpdf2/issues/555)
- `write_html()` method now correctly handles whitespace when parsing HTML. `<pre></pre>` blocks still maintain spaces, tabs and line breaks. 
### Changed
- the first parameter of `FPDF.add_font()` is now **optional**: if it is not provided, the base name of the `fname` font path is used to define the font family. Hence `pdf.add_font(fname="fonts/NotoSansArabic.ttf")` will define a font named `NotoSansArabic`.
- the output of [`embed_file()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.embed_file) is now a `PDFEmbeddedFile`, not a string, but the internal file name can be retrieved through its `.basename` property
- forbid use of `get_y()` & `local_context()` inside `unbreakable()` as it is currently not supported; [#557](https://github.com/py-pdf/fpdf2/discussions/557)
- [fontTools](https://fonttools.readthedocs.io/en/latest/) minimal version requirement set to 4.34.0; [#524](https://github.com/py-pdf/fpdf2/issues/524)

## [2.5.7] - 2022-09-08
### Added
- support for subscript, superscript, nominator and denominator char positioning as well as `<sub>` and `<sup>` HTML tags, thanks to @gmischler: [link to documentation](https://py-pdf.github.io/fpdf2/TextStyling.html#subscript-superscript-and-fractional-numbers)
- [`set_page_background()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_page_background): new method added by @semaeostomea: [link to documentation](https://py-pdf.github.io/fpdf2/PageFormatAndOrientation.html#per-page-format-orientation-and-background)
- [`embed_file()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.embed_file) & [`file_attachment_annotation()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.file_attachment_annotation): new methods to add file attachments - [link to documentation](https://py-pdf.github.io/fpdf2/FileAttachments.html)
- a new method [`set_char_spacing()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_char_spacing) allows to increase the spacing between individual characters, thanks to @gmischler: [link to documentation](https://py-pdf.github.io/fpdf2/TextStyling.html)
- workaround by @semaeostomea to support arabic and right-to-left scripts: [link to documentation](https://py-pdf.github.io/fpdf2/Unicode.html#right-to-left-arabic-script-workaround)
- documentation on shapes styling: [link to documentation](https://py-pdf.github.io/fpdf2/Shapes.html#path-styling)
- documentation on sharing the images cache among FPDF instances: [link to documentation](https://py-pdf.github.io/fpdf2/Images.html#sharing-the-image-cache-among-fpdf-instances)

### Changed
- HTML headings are now rendered with an additional leading of 20% the font size above and below them; [#520](https://github.com/py-pdf/fpdf2/issues/520)
- `fpdf2` now uses [fontTools](https://fonttools.readthedocs.io/en/latest/) to read and embed fonts in the PDF, thanks to @gmischler and @RedShy
- since the fonttools library offers similar functionality, the dependency to "svg.path" is gone again, thanks to @gmischler; [#525](https://github.com/py-pdf/fpdf2/issues/525)

### Fixed
- text following a HTML heading can't overlap with that heading anymore, thanks to @gmischler
- `arc()` not longer renders artefacts at intersection point, thanks to @Jmillan-Dev; [#488](https://github.com/py-pdf/fpdf2/issues/488)
- [`write_html()`](https://py-pdf.github.io/fpdf2/HTML.html):
    * `<em>` & `<strong>` HTML tags are now properly supported - they were ignored previously; [#498](https://github.com/py-pdf/fpdf2/issues/498)
    * `bgcolor` is now properly supported in `<table>` tags; [#512](https://github.com/py-pdf/fpdf2/issues/512)
- the `CreationDate` of PDFs & embedded files now includes the system timezone

## [2.5.6] - 2022-08-16
### Added
- new methods to allow signing PDF documents: [link to docs](https://py-pdf.github.io/fpdf2/Signing.html)
- support for colors defined with the `rgb()` syntax in SVG images - _cf._ [#480](https://github.com/py-pdf/fpdf2/issues/480)
- New translation of the tutorial in [Ελληνικά](https://py-pdf.github.io/fpdf2/Tutorial-gr.html), thanks to @sokratisvas
### Changed
- an `/ID` is now inserted in the trailer dictionary of all PDF documents generated.
  This ID can be controlled through the new [file_id()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.file_id) method.
- the [svg.path](https://pypi.org/project/svg.path/) package was added as a dependency to better parse SVG images
### Fixed
- `font_stretching` doesn't make text spill out of `multi_cell()` and `write()` boundaries anymore, thanks to @gmischler
- `local_context()` now always restores the correct font settings after finishing, thanks to @gmischler
- properly parsing single-digits arguments in SVG paths - _cf._ [#450](https://github.com/py-pdf/fpdf2/issues/450)
- document outline encoding: it was found to be broken when using a thai font - _cf._ [#458](https://github.com/py-pdf/fpdf2/issues/458)

## [2.5.5] - 2022-06-17
### Added
- a new option `align="X"` to `.cell()` and `.multi_cell()` allows to center text around the current x position, thanks to @gmischler
- allowing to provide an [`AnnotationName`](https://py-pdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.AnnotationName)
  and [`AnnotationFlags`](https://py-pdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.AnnotationFlag)
  onto [text_annotation()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.text_annotation)
- allowing correctly parsing of SVG files with CSS styling (`style="..."` attribute), thanks to @RedShy
- [`FPDF.star()`](https://py-pdf.github.io/fpdf2/Shapes.html#regular-star): new method added to draw regular stars, thanks to @digidigital and @RedShy
- [`FPDF.ink_annotation()`](https://py-pdf.github.io/fpdf2/Annotations.html#ink-annotations): new method added to add path annotations
- allowing embedding of indexed PNG images without converting them to RGB colorspace, thanks to @RedShy
- allowing to change appearance of [highlight annotations](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.highlight) by specifying a [`TextMarkupType`](https://py-pdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.TextMarkupType)
- documentation on how to control objects transparency: [link to docs](https://py-pdf.github.io/fpdf2/Transparency.html)
- documentation on how to create tables and charts using [pandas](https://pandas.pydata.org/) DataFrames: [link to docs](https://py-pdf.github.io/fpdf2/Maths.html), thanks to @iwayankurniawan
- added argument `round_corners` to `FPDF.rect()` that allows to draw rectangles with round corners: [link to docs](https://py-pdf.github.io/fpdf2/Shapes.html#rectangle) - thanks to @gonzalobarbaran
### Changed
- `FPDF.add_highlight()` as been renamed into [`FPDF.highlight()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.highlight)
### Fixed
- support for `"x"` & `"y"` attributes in SVG `<use>` tags - _cf._ [#446](https://github.com/py-pdf/fpdf2/issues/446)
- `CreationDate` of PDFs generated, that was broken - _cf._ [#451](https://github.com/py-pdf/fpdf2/issues/451)
- `multi_cell()` and `write()` ignored a trailing newline character in the supplied text since 2.5.1 - fixed thanks to @gmischler

## [2.5.4] - 2022-05-05
### Added
- new `FPDF.page_mode` property, allowing to display a PDF automatically in **full screen**: [link to docs](https://py-pdf.github.io/fpdf2/PageFormatAndOrientation.html#full-screen)
- new `FPDF.viewer_preferences` property: [link to docs](https://py-pdf.github.io/fpdf2/PageFormatAndOrientation.html#viewer-preferences)
### Fixed
- removed a debug `print()` statement (`multi_cell: new_x=... new_y=...`) that had been left in [multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) method 🤦‍♂️
- preserved backward compatibility with PyFPDF for passing positional arguments to `cell()` & `multi_cell()`, which was broken in 2.5.2
### Modified
- when [`regular_polygon()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.regular_polygon) is called with `style="f"`,
  the shape outline is not drawn anymore. Use `style="DF"` to also draw a line around its perimeter.
### Deprecated
- the `fill` parameter of the [`polygon()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.polygon)
  & [`polyline()`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.polyline) methods have been replaced by a `style` argument,
  offering more control

## [2.5.3] - 2022-05-03
### Added
- new `round_clip()` & `elliptic_clip()` image clipping methods: [link to docs](https://py-pdf.github.io/fpdf2/Images.html#image-clipping)
- `CoerciveEnum` subclasses have been added: [`Align`](https://py-pdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.Align) & [`RenderStyle`](https://py-pdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.RenderStyle)
- documentation on how to embed Matplotlib charts: [link to docs](https://py-pdf.github.io/fpdf2/Maths.html)
- documentation on how to use `fpdf2` with [Flask](https://flask.palletsprojects.com), [streamlit](https://streamlit.io/), AWS lambdas: [link to docs](https://py-pdf.github.io/fpdf2/UsageInWebAPI.html)
- documentation on how to store PDFs in a database with [SQLAlchemy](https://www.sqlalchemy.org/): [link to docs](https://py-pdf.github.io/fpdf2/DatabaseStorage.html)
### Modified
- `TextMode`, `XPos` & `YPos` now inherit from `CoerciveEnum` and hence can simply be passed as string parameters
### Fixed
- infinite loop when calling `.multi_cell()` without enough horizontal space - _cf._ [#389](https://github.com/py-pdf/fpdf2/issues/389)
### Removed
- support for `.pkl` files passed to `add_font()`. This was deprecated since v2.5.1.
  As a consequence, `fpdf2` no more uses the `pickle` module \o/

## [2.5.2] - 2022-04-13
### Added
- new parameters `new_x` and `new_y` for `cell()` and `multi_cell()`, replacing `ln=0`, thanks to @gmischler
- new `highlight()` method to insert highlight annotations: [documentation](https://py-pdf.github.io/fpdf2/Annotations.html#highlights)
- new `offset_rendering()` method: [documentation](https://py-pdf.github.io/fpdf2/PageBreaks.html#unbreakable-sections)
- new `.text_mode` property: [documentation](https://py-pdf.github.io/fpdf2/TextStyling.html#text_mode)
- the page structure of the documentation has been revised, with a new page about [adding text](https://py-pdf.github.io/fpdf2/Text.html), thanks to @gmischler
- a warning is now raised if a context manager is used inside an `unbreakable()` section, which is not supported
### Changed
- `local_context()` can now "scope" even more properties, like `blend_mode`: [documentation](https://py-pdf.github.io/fpdf2/Images.html#blending-images)
### Fixed
- No font properties should be leaked anymore after using markdown or in any other situations (_cf._ [#359](https://github.com/py-pdf/fpdf2/issues/349)), thanks to @gmischler
- If `multi_cell(align="J")` is given text with multiple paragraphs (text followed by an empty line) at once, it now renders the last line of each paragraph left-aligned,
  instead of just the very last line (_cf._ [#364](https://github.com/py-pdf/fpdf2/issues/364)), thanks to @gmischler
- a regression: now again `multi_cell()` always renders a cell, even if `txt` is an empty string - _cf._ [#349](https://github.com/py-pdf/fpdf2/issues/349)
- a bug with string width calculation when Markdown is enabled - _cf._ [#351](https://github.com/py-pdf/fpdf2/issues/351)
- a few bugs when parsing some SVG files - _cf._ [#356](https://github.com/py-pdf/fpdf2/issues/356), [#358](https://github.com/py-pdf/fpdf2/issues/358) & [#376](https://github.com/py-pdf/fpdf2/issues/376)
- a bug when using `multi_cell(..., split_only=True)` inside an `unbreakable` section - _cf._ [#359](https://github.com/py-pdf/fpdf2/issues/359)
### Deprecated
- The parameter `ln` to `cell()` and `multi_cell()` is now deprecated: use `new_x` and `new_y` instead.
- The parameter `center` to `cell()` is now deprecated, use `align="C"` instead.

## [2.5.1] - 2022-03-07
### Added
- The documentation outline is revised, and a page about creating Text added, thanks to @gmischler
- support for soft-hyphen (`\u00ad`) break in `write()`, `cell()` & `multi_cell()` calls - thanks @oleksii-shyman & @gmischler!
  Documentation: [Line breaks](https://py-pdf.github.io/fpdf2/LineBreaks.html)
- new documentation page on [Emojis, Symbols & Dingbats](https://py-pdf.github.io/fpdf2/EmojisSymbolsDingbats.html)
- documentation on combining `borb` & `fpdf2`: [Creating a borb.pdf.document.Document from a FPDF instance](https://py-pdf.github.io/fpdf2/borb.html)

### Changed
- `write()` now supports soft hyphen characters, thanks to @gmischler
- `fname` is now a required parameter for `FPDF.add_font()`
- `image()` method now insert `.svg` images as PDF paths
- the [defusedxml](https://pypi.org/project/defusedxml/) package was added as dependency in order to make SVG parsing safer
- log level of `_substitute_page_number()` has been lowered from `INFO` to `DEBUG`

### Fixed
- a bug when rendering Markdown and setting a custom `text_color` or `fill_color`
- a bug in `get_string_width()` with unicode fonts and Markdown enabled,
  resulting in calls to `cell()` / `multi_cell()` with `align="R"` to display nothing - thanks @mcerveny for the fix!
- a bug with incorrect width calculation of markdown text

### Deprecated
- the font caching mechanism, that used the `pickle` module, has been removed, for security reasons,
  and because it provided little performance gain, and only for specific use cases - _cf._ [issue #345](https://github.com/py-pdf/fpdf2/issues/345).
  That means that the `font_cache_dir` optional parameter of `fpdf.FPDF` constructor
  and the `uni` optional argument of `FPDF.add_font()` are deprecated.
  The `fpdf.fpdf.load_cache` function has also been removed.

To be extra clear: `uni=True` can now be removed from all calls to `FPDF.add_font()`.
If the value of the `fname` argument passed to `add_font()` ends with `.ttf`, it is considered a TrueType font.

## [2.5.0] - 2022-01-22
### Added
Thanks to @torque for contributing this massive new feature:
- add [`fpdf.drawing`](https://py-pdf.github.io/fpdf2/Drawing.html) API for composing paths from an arbitrary sequence of lines and curves.
- add [`fpdf.svg.convert_svg_to_drawing`](https://py-pdf.github.io/fpdf2/SVG.html) function to support converting basic scalable vector graphics (SVG) images to PDF paths.

### Fixed
- `will_page_break()` & `accept_page_break` are not invoked anymore during a call to `multi_cell(split_only=True)`
- Unicode characters in headings are now properly displayed in the table of content, _cf._ [#320](https://github.com/py-pdf/fpdf2/issues/320) - thanks @lcomrade

## [2.4.6] - 2021-11-16
### Added
- New `FPDF.pages_count` property, thanks to @paulacampigotto
- Temporary changes to graphics state variables are now possible using `with FPDF.local_context():`, thanks to @gmischler
- a mechanism to detect & downscale oversized images,
  _cf._ [documentation](https://py-pdf.github.io/fpdf2/Images.html#oversized-images-detection-downscaling).
  [Feedbacks](https://github.com/py-pdf/fpdf2/discussions) on this new feature are welcome!
- New `set_dash_pattern()`, which works with all lines and curves, thanks to @gmischler.
- Templates now support drawing ellipses, thanks to @gmischler
- New documentation on how to display equations, using Google Charts or `matplotlib`: [Maths](https://py-pdf.github.io/fpdf2/Maths.html)
- The whole documentation can now be downloaded as a PDF: [fpdf2-manual.pdf](https://py-pdf.github.io/fpdf2/fpdf2-manual.pdf)
- New sections have been added to [the tutorial](https://py-pdf.github.io/fpdf2/Tutorial.html), thanks to @portfedh:

    5. [Creating Tables](https://py-pdf.github.io/fpdf2/Tutorial.html#tuto-5-creating-tables)
    6. [Creating links and mixing text styles](https://py-pdf.github.io/fpdf2/Tutorial.html#tuto-6-creating-links-and-mixing-text-styles)
- New translation of the tutorial in Hindi, thanks to @Mridulbirla13: [हिंदी संस्करण](https://py-pdf.github.io/fpdf2/Tutorial-hi.html); [Deutsch](https://py-pdf.github.io/fpdf2/Tutorial-de.html), thanks to @digidigital; and [Italian](https://py-pdf.github.io/fpdf2/Tutorial-it.html) thanks to @xit4; [Русский](https://py-pdf.github.io/fpdf2/Tutorial-ru.html) thanks to @AABur; and [português](https://py-pdf.github.io/fpdf2/Tutorial-pt.html) thanks to @fuscati; [français](https://py-pdf.github.io/fpdf2/Tutorial-fr.html), thanks to @Tititesouris
- While images transparency is still handled by default through the use of `SMask`,
  this can be disabled by setting `pdf.allow_images_transparency = False`
  in order to allow compliance with [PDF/A-1](https://en.wikipedia.org/wiki/PDF/A#Description)
- [`FPDF.arc`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.arc): new method added. 
  It enables to draw arcs in a PDF document.
- [`FPDF.solid_arc`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.solid_arc): new method added.
  It enables to draw solid arcs in a PDF document. A solid arc combines an arc and a triangle to form a pie slice.
- [`FPDF.regular_polygon`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.regular_polygon): new method added, thanks to @bettman-latin
### Fixed
- All graphics state manipulations are now possible within a rotation context, thanks to @gmischler
- The exception making the "x2" template field optional for barcode elements did not work correctly, fixed by @gmischler
- It is now possible to get back to a previous page to add more content, _e.g._ with a 2-column layout, thanks to @paulacampigotto
### Changed
- All template elements now have a transparent default background instead of white, thanks to @gmischler
- To reduce the size of generated PDFs, no `SMask` entry is inserted for images that are fully opaque
  (= with an alpha channel containing only 0xff characters)
- The `rect`, `ellipse` & `circle` all have a `style` parameter in common.
  They now all properly accept a value of `"D"` and raise a `ValueError` for invalid values.
### Deprecated
- `dashed_line()` is now deprecated in favor of `set_dash_pattern()`

## [2.4.5] - 2021-10-03
### Fixed
- ensure support for old field names in `Template.code39` for backward compatibility

## [2.4.4] - 2021-10-01
### Added
- `Template()` has gained a more flexible cousin `FlexTemplate()`, _cf._ [documentation](https://py-pdf.github.io/fpdf2/Templates.html), thanks to @gmischler
- markdown support in `multi_cell()`, thanks to Yeshi Namkhai
- base 64 images can now be provided to `FPDF.image`, thanks to @MWhatsUp
- documentation on how to generate datamatrix barcodes using the `pystrich` lib: [documentation section](https://py-pdf.github.io/fpdf2/Barcodes.html#datamatrix),
  thanks to @MWhatsUp
- `write_html`: headings (`<h1>`, `<h2>`...) relative sizes can now be configured through an optional `heading_sizes` parameter
- a subclass of `HTML2FPDF` can now easily be used by setting `FPDF.HTML2FPDF_CLASS`,
  _cf._ [documentation](https://py-pdf.github.io/fpdf2/DocumentOutlineAndTableOfContents.html#with-html)
### Fixed
- `Template`: `split_multicell()` will not write spurious font data to the target document anymore, thanks to @gmischler
- `Template`: rotation now should work correctly in all situations, thanks to @gmischler
- `write_html`: headings (`<h1>`, `<h2>`...) can now contain non-ASCII characters without triggering a `UnicodeEncodeError`
- `Template`: CSV column types are now safely parsed, thanks to @gmischler
- `cell(..., markdown=True)` "leaked" its final style (bold / italics / underline) onto the following cells
### Changed
- `write_html`: the line height of headings (`<h1>`, `<h2>`...) is now properly scaled with its font size
- some `FPDF` methods should not be used inside a `rotation` context, or things can get broken.
  This is now forbidden: an exception is now raised in those cases.
### Deprecated
- `Template`: `code39` barcode input field names changed from `x/y/w/h` to `x1/y1/y2/size`

## [2.4.3] - 2021-09-01
### Added
- support for **emojis**! More precisely unicode characters above `0xFFFF` in general, thanks to @moe-25
- `Template` can now insert justified text
- [`get_scale_factor`](https://py-pdf.github.io/fpdf2/fpdf/util.html#fpdf.util.get_scale_factor) utility function to obtain `FPDF.k` without having to create a document
- [`convert_unit`](https://py-pdf.github.io/fpdf2/fpdf/util.html#fpdf.util.convert_unit) utility function to convert a number, `x,y` point, or list of `x,y` points from one unit to another unit
### Changed
- `fpdf.FPDF()` constructor now accepts ints or floats as a unit, and raises a `ValueError` if an invalid unit is provided.
### Fixed
- `Template` `background` property is now properly supported - [#203](https://github.com/py-pdf/fpdf2/pull/203)
  ⚠️ Beware that its default value changed from `0` to `0xffffff`, as a value of **zero would render the background as black**.
- `Template.parse_csv`: preserving numeric values when using CSV based templates - [#205](https://github.com/py-pdf/fpdf2/pull/205)
- the code snippet to generate Code 39 barcodes in the documentation was missing the start & end `*` characters.
This has been fixed, and a warning is now triggered by the [`FPDF.code39`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.code39) method when those characters are missing.
### Fixed
- Detect missing `uni=True` when loading cached fonts (page numbering was missing digits)

## [2.4.2] - 2021-06-29
### Added
- disable font caching when `fpdf.FPDF` constructor invoked with `font_cache_dir=None`, thanks to @moe-25 !
- [`FPDF.circle`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.circle): new method added, thanks to @viraj-shah18 !
- `write_html`: support setting HTML font colors by name and short hex codes
- [`FPDF.will_page_break`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.will_page_break)
utility method to let users know in advance when adding an elemnt will trigger a page break.
This can be useful to repeat table headers on each page for exemple,
_cf._ [documentation on Tables](https://py-pdf.github.io/fpdf2/Tables.html#repeat-table-header-on-each-page).
- [`FPDF.set_link`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_link) now support a new optional `x` parameter to set the horizontal position after following the link
### Fixed
- fixed a bug when `fpdf.Template` was used to render QRCodes, due to a forced conversion to string (#175)

## [2.4.1] - 2021-06-12
### Fixed
- erroneous page breaks occured for full-width / full-height images
- rendering issue of non-ASCII characaters with unicode fonts

## [2.4.0] - 2021-06-11
### Changed
- now `fpdf2` uses the newly supported `DCTDecode` image filter for JPEG images,
  instead of `FlateDecode` before, in order to improve the compression ratio without any image quality loss.
  On test images, this reduced the size of embeded JPEG images by 90%.
- `FPDF.cell`: the `w` (width) parameter becomes optional, with a default value of `None`, meaning to generate a cell with the size of the text content provided
- the `h` (height) parameter of the `cell`, `multi_cell` & `write` methods gets a default value change, `None`, meaning to use the current font size
- removed the useless `w` & `h` parameters of the `FPDF.text_annotation()` method
### Added
- new `FPDF.add_action()` method, documented in the [Annotations section](https://py-pdf.github.io/fpdf2/Annotations.html)
- `FPDF.cell`: new optional `markdown=True` parameter that enables basic Markdown-like styling: `**bold**, __italics__, --underlined--`
- `FPDF.cell`: new optional boolean `center` parameter that positions the cell horizontally
- `FPDF.set_link`: new optional `zoom` parameter that sets the zoom level after following the link.
  Currently ignored by Sumatra PDF Reader, but observed by Adobe Acrobat reader.
- `write_html`: now support `align="justify"`
- new method `FPDF.image_filter` to control the image filters used for images
- `FPDF.add_page`: new optional `duration` & `transition` parameters
  used for [presentations (documentation page)](https://py-pdf.github.io/fpdf2/Presentations.html)
- extra documentation on [how to configure different page formats for specific pages](https://py-pdf.github.io/fpdf2/PageFormatAndOrientation.html)
- support for Code 39 barcodes in `fpdf.template`, using `type="C39"`
### Fixed
- avoid an `Undefined font` error when using `write_html` with unicode bold or italics fonts
### Deprecated
- the `FPDF.set_doc_option()` method is deprecated in favour of just setting the `core_fonts_encoding` property
  on an instance of `FPDF`
- the `fpdf.SYSTEM_TTFONTS` configurable module constant is now ignored

## [2.3.5] - 2021-05-12
### Fixed
- a bug in the `deprecation` module that prevented to configure `fpdf2` constants at the module level

## [2.3.4] - 2021-04-30
### Fixed
- a "fake duplicates" bug when a `Pillow.Image.Image` was passed to `FPDF.image`

## [2.3.3] - 2021-04-21
### Added
- new features: **document outline & table of contents**! Check out the new dedicated [documentation page](https://py-pdf.github.io/fpdf2/DocumentOutlineAndTableOfContents.html) for more information
- new method `FPDF.text_annotation` to insert... Text Annotations
- `FPDF.image` now also accepts an `io.BytesIO` as input
### Fixed
- `write_html`: properly handling `<img>` inside `<td>` & allowing to center them horizontally

## [2.3.2] - 2021-03-27
### Added
- `FPDF.set_xmp_metadata`
- made `<li>` bullets & indentation configurable through class attributes, instance attributes or optional method arguments, _cf._ [`test_customize_ul`](https://github.com/py-pdf/fpdf2/blob/2.3.2/test/html/test_html.py#L242)
### Fixed
- `FPDF.multi_cell`: line wrapping with justified content and unicode fonts, _cf._ [#118](https://github.com/py-pdf/fpdf2/issues/118)
- `FPDF.multi_cell`: when `ln=3`, automatic page breaks now behave correctly at the bottom of pages

## [2.3.1] - 2021-02-28
### Added
- `FPDF.polyline` & `FPDF.polygon` : new methods added by @uovodikiwi - thanks!
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
Many thanks to [@eumiro](https://github.com/py-pdf/fpdf2/pulls?q=is%3Apr+author%3Aeumiro) & [@fbernhart](https://github.com/py-pdf/fpdf2/pulls?q=is%3Apr+author%3Aeumiro) for their contributions to make `fpdf2` code cleaner!
### Added
- `FPDF.unbreakable` : a new method providing a context-manager in which automatic page breaks are disabled.
  _cf._ https://py-pdf.github.io/fpdf2/PageBreaks.html
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
- new boolean parameter `table_line_separators` for `write_html` & underlying `HTML2FPDF` constructor
### Changed
- the documentation URL is now simply https://py-pdf.github.io/fpdf2/
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
* Fix user's font path ([issue](https://github.com/reingart/pyfpdf/issues/166) [PR](https://github.com/py-pdf/fpdf2/pull/14))
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
