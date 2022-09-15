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

## [2.5.8] - not released yet
### Added
- support for monochromatic images (PIL `image.mode == '1'`) thanks to @GerardoAllende
- demonstration Jupyter notebook: [tutorial/notebook.ipynb](https://github.com/PyFPDF/fpdf2/blob/master/tutorial/notebook.ipynb)
### Fixed
- automatic page break is never performed on an empty page (when the Y position is at the top margin)
- The SVG parser now accepts stroke-width attribute values with an explicit unit, thanks to @gmischler; [#526](https://github.com/PyFPDF/fpdf2/issues/526)

### Added
- [fontTools](https://fonttools.readthedocs.io/en/latest/) minimal version requirement set to 4.30.0; [#524](https://github.com/PyFPDF/fpdf2/issues/524)

## [2.5.7] - 2022-09-08
### Changed
- HTML headings are now rendered with an additional leading of 20% the font size above and below them; [#520](https://github.com/PyFPDF/fpdf2/issues/520)
- `fpdf2` now uses [fontTools](https://fonttools.readthedocs.io/en/latest/) to read and embed fonts in the PDF, thanks to @gmischler and @RedShy

### Fixed
- Text following a HTML heading can't overlap with that heading anymore, thanks to @gmischler
- `arc()` not longer renders artefacts at intersection point, thanks to @Jmillan-Dev; [#488](https://github.com/PyFPDF/fpdf2/issues/488)
- [`write_html()`](https://pyfpdf.github.io/fpdf2/HTML.html):
    * `<em>` & `<strong>` HTML tags are now properly supported - they were ignored previously; [#498](https://github.com/PyFPDF/fpdf2/issues/498)
    * `bgcolor` is now properly supported in `<table>` tags; [#512](https://github.com/PyFPDF/fpdf2/issues/512)
- the `CreationDate` of PDFs & embedded files now includes the system timezone

### Added
- Added support for subscript, superscript, nominator and denominator char positioning as well as `<sub>` and `<sup>` HTML tags, thanks to @gmischler: [link to documentation](https://pyfpdf.github.io/fpdf2/TextStyling.html#subscript-superscript-and-fractional-numbers)
- [`set_page_background()`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_page_background): new method added by @semaeostomea: [link to documentation](https://pyfpdf.github.io/fpdf2/PageFormatAndOrientation.html#per-page-format-orientation-and-background)
- [`embed_file()`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.embed_file) & [`file_attachment_annotation()`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.file_attachment_annotation): new methods to add file attachments - [link to documentation](https://pyfpdf.github.io/fpdf2/FileAttachments.html)
- A new method [`set_char_spacing()`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_char_spacing) allows to increase the spacing between individual characters, thanks to @gmischler: [link to documentation](https://pyfpdf.github.io/fpdf2/TextStyling.html)
- workaround by @semaeostomea to support arabic and right-to-left scripts: [link to documentation](https://pyfpdf.github.io/fpdf2/Unicode.html#right-to-left-arabic-script-workaround)
- documentation on shapes styling: [link to documentation](https://pyfpdf.github.io/fpdf2/Shapes.html#path-styling)
- documentation on sharing the images cache among FPDF instances: [link to documentation](https://pyfpdf.github.io/fpdf2/Images.html#sharing-the-image-cache-among-fpdf-instances)

## [2.5.6] - 2022-08-16
### Added
- new methods to allow signing PDF documents: [link to docs](https://pyfpdf.github.io/fpdf2/Signing.html)
- support for colors defined with the `rgb()` syntax in SVG images - _cf._ [#480](https://github.com/PyFPDF/fpdf2/issues/480)
- New translation of the tutorial in [Ελληνικά](https://pyfpdf.github.io/fpdf2/Tutorial-gr.html), thanks to @sokratisvas
### Changed
- an `/ID` is now inserted in the trailer dictionary of all PDF documents generated.
  This ID can be controlled through the new [file_id()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.file_id) method.
- the [svg.path](https://pypi.org/project/svg.path/) package was added as a dependency to better parse SVG images
### Fixed
- `font_stretching` doesn't make text spill out of `multi_cell()` and `write()` boundaries anymore, thanks to @gmischler
- `local_context()` now always restores the correct font settings after finishing, thanks to @gmischler
- properly parsing single-digits arguments in SVG paths - _cf._ [#450](https://github.com/PyFPDF/fpdf2/issues/450)
- document outline encoding: it was found to be broken when using a thai font - _cf._ [#458](https://github.com/PyFPDF/fpdf2/issues/458)

## [2.5.5] - 2022-06-17
### Added
- a new option `align="X"` to `.cell()` and `.multi_cell()` allows to center text around the current x position, thanks to @gmischler
- allowing to provide an [`AnnotationName`](https://pyfpdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.AnnotationName)
  and [`AnnotationFlags`](https://pyfpdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.AnnotationFlag)
  onto [text_annotation()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.text_annotation)
- allowing correctly parsing of SVG files with CSS styling (`style="..."` attribute), thanks to @RedShy
- [`FPDF.star()`](https://pyfpdf.github.io/fpdf2/Shapes.html#regular-star): new method added to draw regular stars, thanks to @digidigital and @RedShy
- [`FPDF.ink_annotation()`](https://pyfpdf.github.io/fpdf2/Annotations.html#ink-annotations): new method added to add path annotations
- allowing embedding of indexed PNG images without converting them to RGB colorspace, thanks to @RedShy
- allowing to change appearance of [highlight annotations](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.highlight) by specifying a [`TextMarkupType`](https://pyfpdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.TextMarkupType)
- documentation on how to control objects transparency: [link to docs](https://pyfpdf.github.io/fpdf2/Transparency.html)
- documentation on how to create tables and charts using [pandas](https://pandas.pydata.org/) DataFrames: [link to docs](https://pyfpdf.github.io/fpdf2/Maths.html), thanks to @iwayankurniawan
- added argument `round_corners` to `FPDF.rect()` that allows to draw rectangles with round corners: [link to docs](https://pyfpdf.github.io/fpdf2/Shapes.html#rectangle) - thanks to @gonzalobarbaran
### Fixed
- support for `"x"` & `"y"` attributes in SVG `<use>` tags - _cf._ [#446](https://github.com/PyFPDF/fpdf2/issues/446)
- `CreationDate` of PDFs generated, that was broken - _cf._ [#451](https://github.com/PyFPDF/fpdf2/issues/451)
- `multi_cell()` and `write()` ignored a trailing newline character in the supplied text since 2.5.1 - fixed thanks to @gmischler

## [2.5.4] - 2022-05-05
### Added
- new `FPDF.page_mode` property, allowing to display a PDF automatically in **full screen**: [link to docs](https://pyfpdf.github.io/fpdf2/PageFormatAndOrientation.html#full-screen)
- new `FPDF.viewer_preferences` property: [link to docs](https://pyfpdf.github.io/fpdf2/PageFormatAndOrientation.html#viewer-preferences)
### Fixed
- removed a debug `print()` statement (`multi_cell: new_x=... new_y=...`) that had been left in [multi_cell()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) method 🤦‍♂️
- preserved backward compatibility with PyFPDF for passing positional arguments to `cell()` & `multi_cell()`, which was broken in 2.5.2
### Modified
- when [`regular_polygon()`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.regular_polygon) is called with `style="f"`,
  the shape outline is not drawn anymore. Use `style="DF"` to also draw a line around its perimeter.
### Deprecated
- the `fill` parameter of the [`polygon()`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.polygon)
  & [`polyline()`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.polyline) methods have been replaced by a `style` argument,
  offering more control

## [2.5.3] - 2022-05-03
### Added
- new `round_clip()` & `elliptic_clip()` image clipping methods: [link to docs](https://pyfpdf.github.io/fpdf2/Images.html#image-clipping)
- `CoerciveEnum` subclasses have been added: [`Align`](https://pyfpdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.Align) & [`RenderStyle`](https://pyfpdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.RenderStyle)
- documentation on how to embed Matplotlib charts: [link to docs](https://pyfpdf.github.io/fpdf2/Maths.html)
- documentation on how to use `fpdf2` with [Flask](https://flask.palletsprojects.com), [streamlit](https://streamlit.io/), AWS lambdas: [link to docs](https://pyfpdf.github.io/fpdf2/UsageInWebAPI.html)
- documentation on how to store PDFs in a database with [SQLAlchemy](https://www.sqlalchemy.org/): [link to docs](https://pyfpdf.github.io/fpdf2/DatabaseStorage.html)
### Modified
- `TextMode`, `XPos` & `YPos` now inherit from `CoerciveEnum` and hence can simply be passed as string parameters
### Fixed
- infinite loop when calling `.multi_cell()` without enough horizontal space - _cf._ [#389](https://github.com/PyFPDF/fpdf2/issues/389)
### Removed
- support for `.pkl` files passed to `add_font()`. This was deprecated since v2.5.1.
  As a consequence, `fpdf2` no more uses the `pickle` module \o/

## [2.5.2] - 2022-04-13
### Added
- new parameters `new_x` and `new_y` for `cell()` and `multi_cell()`, replacing `ln=0`, thanks to @gmischler
- new `highlight()` method to insert highlight annotations: [documentation](https://pyfpdf.github.io/fpdf2/Annotations.html#highlights)
- new `offset_rendering()` method: [documentation](https://pyfpdf.github.io/fpdf2/PageBreaks.html#unbreakable-sections)
- new `.text_mode` property: [documentation](https://pyfpdf.github.io/fpdf2/TextStyling.html#text_mode)
- the page structure of the documentation has been revised, with a new page about [adding text](https://pyfpdf.github.io/fpdf2/Text.html), thanks to @gmischler
- a warning is now raised if a context manager is used inside an `unbreakable()` section, which is not supported
### Changed
- `local_context()` can now "scope" even more properties, like `blend_mode`: [documentation](https://pyfpdf.github.io/fpdf2/Images.html#blending-images)
### Fixed
- No font properties should be leaked anymore after using markdown or in any other situations (_cf._ [#359](https://github.com/PyFPDF/fpdf2/issues/349)), thanks to @gmischler
- If `multi_cell(align="J")` is given text with multiple paragraphs (text followed by an empty line) at once, it now renders the last line of each paragraph left-aligned,
  instead of just the very last line (_cf._ [#364](https://github.com/PyFPDF/fpdf2/issues/364)), thanks to @gmischler
- a regression: now again `multi_cell()` always renders a cell, even if `txt` is an empty string - _cf._ [#349](https://github.com/PyFPDF/fpdf2/issues/349)
- a bug with string width calculation when Markdown is enabled - _cf._ [#351](https://github.com/PyFPDF/fpdf2/issues/351)
- a few bugs when parsing some SVG files - _cf._ [#356](https://github.com/PyFPDF/fpdf2/issues/356), [#358](https://github.com/PyFPDF/fpdf2/issues/358) & [#376](https://github.com/PyFPDF/fpdf2/issues/376)
- a bug when using `multi_cell(..., split_only=True)` inside an `unbreakable` section - _cf._ [#359](https://github.com/PyFPDF/fpdf2/issues/359)
### Deprecated
- The parameter `ln` to `cell()` and `multi_cell()` is now deprecated: use `new_x` and `new_y` instead.
- The parameter `center` to `cell()` is now deprecated, use `align="C"` instead.

## [2.5.1] - 2022-03-07
### Added
- The documentation outline is revised, and a page about creating Text added, thanks to @gmischler
- support for soft-hyphen (`\u00ad`) break in `write()`, `cell()` & `multi_cell()` calls - thanks @oleksii-shyman & @gmischler!
  Documentation: [Line breaks](https://pyfpdf.github.io/fpdf2/LineBreaks.html)
- new documentation page on [Emojis, Symbols & Dingbats](https://pyfpdf.github.io/fpdf2/EmojisSymbolsDingbats.html)
- documentation on combining `borb` & `fpdf2`: [Creating a borb.pdf.document.Document from a FPDF instance](https://pyfpdf.github.io/fpdf2/borb.html)

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
  and because it provided little performance gain, and only for specific use cases - _cf._ [issue #345](https://github.com/PyFPDF/fpdf2/issues/345).
  That means that the `font_cache_dir` optional parameter of `fpdf.FPDF` constructor
  and the `uni` optional argument of `FPDF.add_font()` are deprecated.
  The `fpdf.fpdf.load_cache` function has also been removed.

To be extra clear: `uni=True` can now be removed from all calls to `FPDF.add_font()`.
If the value of the `fname` argument passed to `add_font()` ends with `.ttf`, it is considered a TrueType font.

## [2.5.0] - 2022-01-22
### Added
Thanks to @torque for contributing this massive new feature:
- add [`fpdf.drawing`](https://pyfpdf.github.io/fpdf2/Drawing.html) API for composing paths from an arbitrary sequence of lines and curves.
- add [`fpdf.svg.convert_svg_to_drawing`](https://pyfpdf.github.io/fpdf2/SVG.html) function to support converting basic scalable vector graphics (SVG) images to PDF paths.

### Fixed
- `will_page_break()` & `accept_page_break` are not invoked anymore during a call to `multi_cell(split_only=True)`
- Unicode characters in headings are now properly displayed in the table of content, _cf._ [#320](https://github.com/PyFPDF/fpdf2/issues/320) - thanks @lcomrade

## [2.4.6] - 2021-11-16
### Added
- New `FPDF.pages_count` property, thanks to @paulacampigotto
- Temporary changes to graphics state variables are now possible using `with FPDF.local_context():`, thanks to @gmischler
- a mechanism to detect & downscale oversized images,
  _cf._ [documentation](https://pyfpdf.github.io/fpdf2/Images.html#oversized-images-detection-downscaling).
  [Feedbacks](https://github.com/PyFPDF/fpdf2/discussions) on this new feature are welcome!
- New `set_dash_pattern()`, which works with all lines and curves, thanks to @gmischler.
- Templates now support drawing ellipses, thanks to @gmischler
- New documentation on how to display equations, using Google Charts or `matplotlib`: [Maths](https://pyfpdf.github.io/fpdf2/Maths.html)
- The whole documentation can now be downloaded as a PDF: [fpdf2-manual.pdf](https://pyfpdf.github.io/fpdf2/fpdf2-manual.pdf)
- New sections have been added to [the tutorial](https://pyfpdf.github.io/fpdf2/Tutorial.html), thanks to @portfedh:

    5. [Creating Tables](https://pyfpdf.github.io/fpdf2/Tutorial.html#tuto-5-creating-tables)
    6. [Creating links and mixing text styles](https://pyfpdf.github.io/fpdf2/Tutorial.html#tuto-6-creating-links-and-mixing-text-styles)
- New translation of the tutorial in Hindi, thanks to @Mridulbirla13: [हिंदी संस्करण](https://pyfpdf.github.io/fpdf2/Tutorial-हिंदी.html); [Deutsch](https://pyfpdf.github.io/fpdf2/Tutorial-de.html), thanks to @digidigital; and [Italian](https://pyfpdf.github.io/fpdf2/Tutorial-it.html) thanks to @xit4; [Русский](https://pyfpdf.github.io/fpdf2/Tutorial-ru.html) thanks to @AABur; and [português](https://pyfpdf.github.io/fpdf2/Tutorial-pt.html) thanks to @fuscati; [français](https://pyfpdf.github.io/fpdf2/Tutorial-fr.html), thanks to @Tititesouris
- While images transparency is still handled by default through the use of `SMask`,
  this can be disabled by setting `pdf.allow_images_transparency = False`
  in order to allow compliance with [PDF/A-1](https://en.wikipedia.org/wiki/PDF/A#Description)
- [`FPDF.arc`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.arc): new method added. 
  It enables to draw arcs in a PDF document.
- [`FPDF.solid_arc`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.solid_arc): new method added.
  It enables to draw solid arcs in a PDF document. A solid arc combines an arc and a triangle to form a pie slice.
- [`FPDF.regular_polygon`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.regular_polygon): new method added, thanks to @bettman-latin
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
- `Template()` has gained a more flexible cousin `FlexTemplate()`, _cf._ [documentation](https://pyfpdf.github.io/fpdf2/Templates.html), thanks to @gmischler
- markdown support in `multi_cell()`, thanks to Yeshi Namkhai
- base 64 images can now be provided to `FPDF.image`, thanks to @MWhatsUp
- documentation on how to generate datamatrix barcodes using the `pystrich` lib: [documentation section](https://pyfpdf.github.io/fpdf2/Barcodes.html#datamatrix),
  thanks to @MWhatsUp
- `write_html`: headings (`<h1>`, `<h2>`...) relative sizes can now be configured through an optional `heading_sizes` parameter
- a subclass of `HTML2FPDF` can now easily be used by setting `FPDF.HTML2FPDF_CLASS`,
  _cf._ [documentation](https://pyfpdf.github.io/fpdf2/DocumentOutlineAndTableOfContents.html#with-html)
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
- [`get_scale_factor`](https://pyfpdf.github.io/fpdf2/fpdf/util.html#fpdf.util.get_scale_factor) utility function to obtain `FPDF.k` without having to create a document
- [`convert_unit`](https://pyfpdf.github.io/fpdf2/fpdf/util.html#fpdf.util.convert_unit) utility function to convert a number, `x,y` point, or list of `x,y` points from one unit to another unit
### Changed
- `fpdf.FPDF()` constructor now accepts ints or floats as a unit, and raises a `ValueError` if an invalid unit is provided.
### Fixed
- `Template` `background` property is now properly supported - [#203](https://github.com/PyFPDF/fpdf2/pull/203)
  ⚠️ Beware that its default value changed from `0` to `0xffffff`, as a value of **zero would render the background as black**.
- `Template.parse_csv`: preserving numeric values when using CSV based templates - [#205](https://github.com/PyFPDF/fpdf2/pull/205)
- the code snippet to generate Code 39 barcodes in the documentation was missing the start & end `*` characters.
This has been fixed, and a warning is now triggered by the [`FPDF.code39`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.code39) method when those characters are missing.
### Fixed
- Detect missing `uni=True` when loading cached fonts (page numbering was missing digits)

## [2.4.2] - 2021-06-29
### Added
- disable font caching when `fpdf.FPDF` constructor invoked with `font_cache_dir=None`, thanks to @moe-25 !
- [`FPDF.circle`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.circle): new method added, thanks to @viraj-shah18 !
- `write_html`: support setting HTML font colors by name and short hex codes
- [`FPDF.will_page_break`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.will_page_break)
utility method to let users know in advance when adding an elemnt will trigger a page break.
This can be useful to repeat table headers on each page for exemple,
_cf._ [documentation on Tables](https://pyfpdf.github.io/fpdf2/Tables.html#repeat-table-header-on-each-page).
- [`FPDF.set_link`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_link) now support a new optional `x` parameter to set the horizontal position after following the link
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
- new `FPDF.add_action()` method, documented in the [Annotations section](https://pyfpdf.github.io/fpdf2/Annotations.html)
- `FPDF.cell`: new optional `markdown=True` parameter that enables basic Markdown-like styling: `**bold**, __italics__, --underlined--`
- `FPDF.cell`: new optional boolean `center` parameter that positions the cell horizontally
- `FPDF.set_link`: new optional `zoom` parameter that sets the zoom level after following the link.
  Currently ignored by Sumatra PDF Reader, but observed by Adobe Acrobat reader.
- `write_html`: now support `align="justify"`
- new method `FPDF.image_filter` to control the image filters used for images
- `FPDF.add_page`: new optional `duration` & `transition` parameters
  used for [presentations (documentation page)](https://pyfpdf.github.io/fpdf2/Presentations.html)
- extra documentation on [how to configure different page formats for specific pages](https://pyfpdf.github.io/fpdf2/PageFormatAndOrientation.html)
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
- new features: **document outline & table of contents**! Check out the new dedicated [documentation page](https://pyfpdf.github.io/fpdf2/DocumentOutlineAndTableOfContents.html) for more information
- new method `FPDF.text_annotation` to insert... Text Annotations
- `FPDF.image` now also accepts an `io.BytesIO` as input
### Fixed
- `write_html`: properly handling `<img>` inside `<td>` & allowing to center them horizontally

## [2.3.2] - 2021-03-27
### Added
- `FPDF.set_xmp_metadata`
- made `<li>` bullets & indentation configurable through class attributes, instance attributes or optional method arguments, _cf._ [`test_customize_ul`](https://github.com/PyFPDF/fpdf2/blob/2.3.2/test/html/test_html.py#L242)
### Fixed
- `FPDF.multi_cell`: line wrapping with justified content and unicode fonts, _cf._ [#118](https://github.com/PyFPDF/fpdf2/issues/118)
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
- new boolean parameter `table_line_separators` for `write_html` & underlying `HTML2FPDF` constructor
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
