# History #

This project, `fpdf2` is a _fork_ of the `PyFPDF` project, which can still be found [on GitHub at reingart/pyfpdf](https://github.com/reingart/pyfpdf), but has been totally inactive since January 2018, and has not seen any new release since 2015.

About the original `PyFPDF` lib:

> This project started as a Python fork of the [FPDF](http://fpdf.org/) PHP library,
> ported to Python by Max Pat in 2006: <http://www.fpdf.org/dl.php?id=94>.
> Later, code for native reading TTF fonts was added.
> The project aim is to keep the library up to date, to fulfill the goals of its
> [original roadmap](https://github.com/reingart/pyfpdf/wiki/Roadmap) and provide
> a general overhaul of the codebase to address technical debt keeping features from being added and bugs to be eradicated.
> Until 2015 the code was developed at [Google Code](https://code.google.com/p/pyfpdf/):
> you can still access the [old issues](https://github.com/reingart/pyfpdf_googlecode/issues),
> and [old wiki](https://github.com/reingart/pyfpdf_googlecode/tree/wiki).

## How fpdf2 came to be ##

During the spring of 2016, David Ankin (`@alexanderankin`) started a fork of PyFPDF, and added the first commit of what became `fpdf2`:
[bd608e4](https://github.com/py-pdf/fpdf2/commits/master?after=1db5f7fdc93eac981c8f1d15856649b68e523ec8+69&branch=master&qualified_name=refs%2Fheads%2Fmaster).
On May of 2017, the first release of `fpdf2` was published on Pypi:
[v2.0.0](https://pypi.org/project/fpdf2/#history).

On 2020, the first PRs were merged from external contributors.
At the end of the year, Lucas Cimon (`@Lucas-C`) started contributing several improvements, in order to use `fpdf2` for his [Undying Dusk](https://lucas-c.itch.io/undying-dusk) project.
[Version **2.1.0** was released](https://github.com/py-pdf/fpdf2/blob/master/CHANGELOG.md#210---2020-12-07) and on 2021/01/10 `fpdf2` was moved to a dedicated `PyFPDF` GitHub organization, and `@Lucas-C` became another maintainer of the project.

On 2023/08/04, `fpdf2` moved to the `py-pdf` organization: <https://github.com/py-pdf/fpdf2>. The context for this move can be found there: <https://github.com/py-pdf/fpdf2/discussions/752>. On this date, the `PyFPDF` GitHub organization has been **archived**.

## Compatibility between PyFPDF & fpdf2 ##

`fpdf2` aims to be fully compatible with PyFPDF code.

The notable exceptions are:

* for the [`cell()` method](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell), the default value of `h` has changed. It used to be `0` and is now set to the current value of `FPDF.font_size`
* the font caching mechanism, that used the `pickle` module, has been **removed**, for security reasons, and because it provided little performance gain, and only for specific use cases - _cf._ [issue #345](https://github.com/py-pdf/fpdf2/issues/345).
* [Template](https://py-pdf.github.io/fpdf2/fpdf/template.html#fpdf.template.Template) elements now have a **transparent background** by default, instead of white

Some features are also **deprecated**. As of version 2.7.5 they **still work** but **generate a warning** when used:

* ⚠️ [FPDF.rotate()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.rotate) can produce malformed PDFs: use [FPDF.rotation()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.rotation) instead
* [FPDF.set_doc_option()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_doc_option): simply set the `.core_fonts_encoding` property as a replacement
* [FPDF.dashed_line()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.dashed_line): use [FPDF.set_dash_pattern()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_dash_pattern) and the normal drawing operations instead
* the `font_cache_dir` parameter of [FPDF() constructor](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF), that is currently ignored
* the `uni` parameter of [FPDF.add_font()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_font), that is currently ignored: if the value of the `fname` argument passed to `add_font()` ends with `.ttf`, it is considered a TrueType font
* the `type` parameter of [FPDF.image()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image), that is currently ignored
* the `dest` parameter of [FPDF.output()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.output), that is currently ignored
* the `ln` parameter of [FPDF.multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell): use `new_x=` & `new_y=` instead
* the `split_only` parameter of [FPDF.multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell): use `dry_run=True` and `output="LINES"` instead
* the [HTMLMixin class](https://py-pdf.github.io/fpdf2/fpdf/html.html#fpdf.html.HTMLMixin): you can now directly use the [FPDF.write_html()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write_html) method
* the `infile` parametyer of [Template() constructor](https://py-pdf.github.io/fpdf2/fpdf/template.html#fpdf.template.Template), that is currently ignored
* the parameters `x/y/w/h` of `code39` elements provided to the [`Template` system](https://py-pdf.github.io/fpdf2/fpdf/template.html#fpdf.template.Template): please use `x1/y1/y2/size` instead
* the `dest` parameter of [Template.render()](https://py-pdf.github.io/fpdf2/fpdf/template.html#fpdf.template.Template.render), that is currently ignored

Note that `DeprecationWarning` messages are not displayed by Python by default.
To get warned about deprecated features used in your code, you must execute your scripts with the `-Wd` option (_cf._ [documentation](https://docs.python.org/3/using/cmdline.html#cmdoption-W)), or enable them programmatically with `warnings.simplefilter('default', DeprecationWarning)`.
