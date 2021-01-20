#!/usr/bin/env python

from setuptools import setup, find_packages

import re


def read(path):
    """Read a file's contents."""
    with open(path) as f:
        return f.read()


if __name__ == "__main__":
    version = re.findall(
        r'FPDF_VERSION = "(\d+.\d+.\d+[^"]*)"', read("./fpdf/fpdf.py")
    )[0]
    setup(
        name="fpdf2",
        version=version,
        description="Simple PDF generation for Python",
        long_description=read("./README.md"),
        long_description_content_type="text/markdown",
        author="Olivier PLATHEY ported by Max",
        author_email="maxpat78@yahoo.it",
        maintainer="David Ankin",
        maintainer_email="daveankin@gmail.com",
        url="https://pyfpdf.github.io/fpdf2/",
        license="LGPLv3+",
        download_url=f"https://github.com/PyFPDF/fpdf2/tarball/{version}",
        packages=find_packages(),
        package_dir={"fpdf": "fpdf"},
        install_requires=[
            "Pillow",
        ],
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Operating System :: OS Independent",
            "Topic :: Printing",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: Text Processing :: Markup",
            "Topic :: Multimedia :: Graphics",
            "Topic :: Multimedia :: Graphics :: Presentation",
        ],
        keywords=["pdf", "unicode", "png", "jpg", "ttf", "barcode"],
    )
