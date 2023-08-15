# Development

This page has summary information about developing the PyPDF library.

[TOC]

## Repository structure

  * `.github/` - GitHub Actions configuration
  * `docs/` - documentation folder
  * `fpdf/` - library sources
  * `scripts/` - utilities to validate PDF files & publish the package on Pypi
  * `test/` - non-regression tests
  * `tutorial/` - tutorials (see also [Tutorial](Tutorial.md))
  * `README.md` - Github and PyPI ReadMe
  * `CHANGELOG.md` - details of each release content
  * `LICENSE` - code license information
  * `CODEOWNERS` - define individuals or teams responsible for code in this repository
  * `CONTRIBUTORS.md` - the people who helped build this library ❤️
  * `setup.cfg`, `setup.py`, `MANIFEST.in` - packaging configuration to publish [a package on Pypi](https://pypi.org/project/fpdf2/)
  * `mkdocs.yml` - configuration for [MkDocs](https://www.mkdocs.org/)
  * `tox.ini` - configuration for [Tox](https://tox.readthedocs.io/en/latest/)
  * `.banditrc.yml` - configuration for [bandit](https://pypi.org/project/bandit/)
  * `.pylintrc` - configuration for [Pylint](http://pylint.pycqa.org/en/latest/)

## Installing fpdf2 from a local git repository
```
pip install --editable $path/to/fpdf/repo
```

This will link the installed Python package to the repository location,
basically meaning any changes to the code package will get reflected directly in your environment.

## Code auto-formatting
We use [black](https://github.com/psf/black) as a code prettifier.
This _"uncomprimising Python code formatter"_ must be installed
in your development environment in order to auto-format source code before any commit:
```
pip install black
black .  # inside fpdf2 root directory
```

## Linting
We use [pylint](https://github.com/PyCQA/pylint/) as a static code analyzer
to detect potential issues in the code.

In case of special "false positive" cases,
checks can be disabled locally with `#pylint disable=XXX` code comments,
or globally through the `.pylintrc` file.

## Pre-commit hook
This project uses `git` **pre-commit hooks**: https://pre-commit.com

Those hooks are configured in [`.pre-commit-config.yaml`](https://github.com/py-pdf/fpdf2/blob/master/.pre-commit-config.yaml).

They are intended to abort your commit if `pylint` found issues
or `black` detected non-properly formatted code.
In the later case though, it will auto-format your code
and you will just have to run `git commit -a` again.

To install pre-commit hooks on your computer, run:
```
pip install pre-commit
pre-commit install
```

## Testing

### Running tests
To run tests, `cd` into `fpdf2` repository, install the dependencies using
`pip install -r test/requirements.txt`,  and run `pytest`.

You can run a single test by executing: `pytest -k function_name`.

Alternatively, you can use [Tox](https://tox.readthedocs.io/en/latest/).
It is self-documented in the `tox.ini` file in the repository.
To run tests for all versions of Python, simply run `tox`.
If you do not want to run tests for all versions of python, run `tox -e py39`
(or your version of Python).

### Why is a test failing?
If there are some failing tests after you made a code change,
it is usually because **there are difference between an expected PDF generated and the actual one produced**.

Calling `pytest -vv` will display **the difference of PDF source code** between the expected & actual files,
but that may be difficult to understand,

You can also have a look at the PDF files involved by navigating to the temporary test directory
that is printed out during the test failure:
```
=================================== FAILURES ===================================
____________________________ test_html_simple_table ____________________________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-0/test_html_simple_table0')
```

This directory contains the **actual** & **expected** files, that you can vsualize to spot differences:
```
$ ls /tmp/pytest-of-runner/pytest-0/test_html_simple_table0
actual.pdf
actual_qpdf.pdf
expected_qpdf.pdf
```

### assert_pdf_equal & writing new tests
When a unit test generates a PDF, it is recommended to use the `assert_pdf_equal`
utility function in order to validate the output.
It relies on the very handy [qpdf](https://github.com/qpdf/qpdf) CLI program
to generate a PDF that is easy to compare: annotated, strictly formatted,
with uncompressed internal streams.
You will need to have its binary in your `$PATH`,
otherwise `assert_pdf_equal` will fall back to hash-based comparison.

All generated PDF files (including those processed by `qpdf`) will be stored in
`/tmp/pytest-of-USERNAME/pytest-current/NAME_OF_TEST/`. By default, three
last test runs will be saved and then automatically deleted, so you can
check the output in case of a failed test.

In order to generate a "reference" PDF file, simply call `assert_pdf_equal`
once with `generate=True`.

## GitHub pipeline
A [GitHub Actions](https://help.github.com/en/actions/reference) pipeline
is executed on every commit on the `master` branch, and for every _Pull Request_.

It performs all validation steps detailed above: code checking with `black`,
static code analysis with `pylint`, unit tests...
_Pull Requests_ submitted must pass all those checks in order to be approved.
Ask maintainers through comments if some errors in the pipeline seem obscure to you.

### Release checklist
1. complete `CHANGELOG.md` and add the version & date of the new release
2. bump `FPDF_VERSION` in `fpdf/fpdf.py`.
Also (optionnal, once every year), update `contributors/contributors-map-small.png` based on <https://py-pdf.github.io/fpdf2/contributors.html>
3. `git commit` & `git push`
4. check that [the GitHub Actions succeed](https://github.com/py-pdf/fpdf2/actions), and that [a new release appears on Pypi](https://pypi.org/project/fpdf2/#history)
5. perform a [GitHub release](https://github.com/py-pdf/fpdf2/releases), taking the description from the `CHANGELOG.md`.
It will create a new `git` tag.
6. Announce the release on [r/pythonnews](https://www.reddit.com/r/pythonnews/),
   and add an announcement to the documentation website: [docs/overrides/main.html](https://github.com/py-pdf/fpdf2/blob/master/docs/overrides/main.html)

## Documentation
The standalone documentation is in the `docs` subfolder,
written in [Markdown](https://daringfireball.net/projects/markdown/).
Building instructions are contained in the configuration file `mkdocs.yml`
and also in `.github/workflows/continuous-integration-workflow.yml`.

Additional documentation is generated from inline comments, and is available
in the project [home page](https://py-pdf.github.io/fpdf2/fpdf/).

After being committed to the master branch, code documentation is automatically uploaded to
[GitHub Pages](https://py-pdf.github.io/fpdf2/).

There is a useful one-page example Python module with docstrings illustrating how to document code:
[pdoc3 example_pkg](https://github.com/pdoc3/pdoc/blob/master/pdoc/test/example_pkg/__init__.py).

To preview the Markdown documentation, launch a local rendering server with:

    mkdocs serve

To preview the API documentation, launch a local rendering server with:

    pdoc --html -o public/ fpdf --http :

## PDF spec & new features
The **PDF 1.7 spec** is available on Adobe website:
[PDF32000_2008.pdf](https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf).

It may be intimidating at first, but while technical, it is usually quite clear and understandable.

It is also a great place to look for new features for `fpdf2`:
there are still many PDF features that this library does not support.

## Useful tools to manipulate PDFs

### qpdf

[qpdf](https://qpdf.sourceforge.io/) is a very powerful tool to analyze PDF documents.

One of it most useful features is the [QDF mode](https://qpdf.readthedocs.io/en/stable/qdf.html) that can convert any PDF file to a human-readable, decompressed & annotated new PDF document:

```
qpdf --qdf doc.pdf doc-qdf.pdf
```

This is extremely useful to peek into the PDF document structure.

### set_pdf_xref.py

[set_pdf_xref.py](https://github.com/Lucas-C/dotfiles_and_notes/blob/master/languages/python/set_pdf_xref.py) is a small Python script that can **rebuild a PDF xref table**.

This is very useful, as a PDF with an invalid xref cannot be opened.
An xref table is basically an index of the document internal sections.
When manually modifying a PDF file (for example one produced by `qpdf --qdf`),
if the characters count in any of its sections changes, the xref table must be rebuilt.

With `set_pdf_xref.py doc.pdf --inplace`, you can change some values inside any PDF file, and then quickly make it valid again to be viewed in a PDF viewer.
