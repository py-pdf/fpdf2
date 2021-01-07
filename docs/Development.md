# Development #

[TOC]

## Introduction ##

This page has summary information about developing the PyPDF library.

This project, fpdf2 is a [FORK] of the PyFPDF project, which can be found
[on GitHub at reingart/pyfpdf](https://github.com/reingart/pyfpdf).
It is made in order to keep the library updated and fulfill the goals of its
[Roadmap](https://github.com/reingart/pyfpdf/wiki/Roadmap) and a general overhaul of
the codebase because there was technical debt keeping features from being
created and bugs from being eradicated.

More on pyfpdf:

> This project started as Python fork of the [FPDF](http://fpdf.org/) PHP library. 
> Later, code for native reading TTF fonts was added. FPDF has not been updated since
> 2011. See also the [TCPDF](http://www.tcpdf.org/) library.
> 
> Until 2015 the code was developed at [Google Code](https://code.google.com/p/pyfpdf/).
> Now the main repository is at [Github](https://github.com/reingart/pyfpdf).
> 
> You can also view the
> [old repository](https://github.com/reingart/pyfpdf_googlecode),
> [old issues](https://github.com/reingart/pyfpdf_googlecode/issues), and 
> [old wiki](https://github.com/reingart/pyfpdf_googlecode/tree/wiki).


## Repository structure ##

  * `[.github]` - GitHub Actions configuration
  * `[docs]` - documentation folder
  * `[fpdf]` - library source
  * `[scripts]` - manipulate this repository
  * `[test]` - tests
  * `[tutorial]` - tutorials (see also [Tutorial](Tutorial.md))
  * `README.md`, `PyPIReadme.rst` - Github and PyPI Readme's.
  * `LICENSE` - license information
  * `setup.cfg`, `setup.py`, `MANIFEST.in` - setup configuration
  * `mkdocs.yml` - config for [MkDocs](https://www.mkdocs.org/)
  * `tox.ini` - config for [Tox](https://tox.readthedocs.io/en/latest/)

## Code auto-formatting ##

We use [black](https://github.com/psf/black) as a code prettifier.
This _"uncomprimising Python code formatter"_ must be installed
in your development environment (`pip install black`) in order to
auto-format source code before any commit.

## Linting ##

We use [pylint](https://github.com/PyCQA/pylint/) as a static code analyzer
to detect potential issues in the code.

In case of special "false positive" cases,
checks can be disabled locally with `#pylint disable=XXX` code comments,
or globally through the `.pylintrc` file.

## Pre-commit hook ##
If you use a UNIX system, you can place the following shell code
in `.git/hooks/pre-commit` in order to always invoke `black` & `pylint`
before every commit:

```shell
#!/bin/sh
modified_py_files=$(git diff --cached --name-only --diff-filter=ACM | grep '.py$')
if [ -n "$modified_py_files" ]; then
    if ! black --check $modified_py_files; then
        black $modified_py_files
        exit 1
    fi
    pylint $modified_py_files
fi
```

It will abort the commit if `pylint` found issues
or `black` detect non-properly formatted code.
In the later case though, it will auto-format your code
and you will just have to run `git commit -a` again.

## Testing ##

Testing is done with [Tox](https://tox.readthedocs.io/en/latest/), and is
self-documented in the `tox.ini` file in the repository. To run tests,
`cd` into the repository and run `tox`.

To only run tests for your version of Python, run `python setup.py test`.

When a unit test generates a PDF, it is recommended to use the `assert_pdf_equal`
utility function in order to validate the output.
It relies on the very handy [qpdf](https://github.com/qpdf/qpdf) CLI program
to generate a PDF that is easy to compare: annotated, strictly formatted,
whith uncompressed internal streams.
You will need to have its binary in your `$PATH`,
otherwise `assert_pdf_equal` will fall back to hash-based comparison.
In order to generate a "reference" PDF file, simply call `assert_pdf_equal` once
with `delete=False`, and retrieve the generated `/tmp/pyfpdf-test-*-actual.pdf` file.

Be sure to see the example tests in the `test/` folder in general.

## GitHub pipeline ##

A [GitHub Actions](https://help.github.com/en/actions/reference) pipeline
is executed on every commit on the `master` branch,
and for every _Pull Request_.

It performs all validation steps detailed above: code checking with `black`,
linting with `pylint`, unit tests...
_Pull Requests_ submitted must pass all those checks in order to be approved.
Ask maintainers through comments if some errors in the pipeline seem obscure to you.

## Documentation ##

To build docs, cd into repository and `tox -e docs`.

This Standalone documentation is in the `docs` subfolder in 
[Markdown](https://daringfireball.net/projects/markdown/) format. Building
instructions are contained in the configuration file `mkdocs.yml` and also in
the docs script in the `tox.ini` file.

Additional documentation is generated from inline comments, and is available
in the project [home page](https://alexanderankin.github.io/pyfpdf/fpdf/).

After being committed to the master branch, code documentation is automatically uploaded to
[GitHub Pages](https://alexanderankin.github.io/pyfpdf/).

There is a useful one-page example Python module with docstrings illustrating how to document code:
[pdoc3 example_pkg](https://github.com/pdoc3/pdoc/blob/master/pdoc/test/example_pkg/__init__.py).

To preview the API documentation generated by `pdoc`, launch a local rendering server with:

    pdoc --html -o public/ fpdf --http :

## See also ##
[Project Home](index.md), [Frequently asked questions](FAQ.md), 
[Unicode](Unicode.md).
