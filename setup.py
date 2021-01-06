#!/usr/bin/env python

from setuptools import setup, find_packages

import unittest, re


def run_test_suite():
    return unittest.TestLoader().discover("test", pattern="*.py")


def read(path):
    """Read a file's contents."""
    with open(path, "r") as f:
        return f.read()


if __name__ == "__main__":
    version = re.findall(r'FPDF_VERSION = "(\d+.\d+.\d+[^"]*)"', read("./fpdf/fpdf.py"))[0]
    setup(
        name="fpdf2",
        version=version,
        description="Simple PDF generation for Python",
        long_description=read("./PyPIReadme.rst"),
        author="Olivier PLATHEY ported by Max",
        author_email="maxpat78@yahoo.it",
        maintainer="David Ankin",
        maintainer_email="daveankin@gmail.com",
        url="https://alexanderankin.github.io/pyfpdf/",
        license="LGPLv3+",
        download_url="https://github.com/alexanderankin/pyfpdf/tarball/%s" % version,
        packages=find_packages(),
        package_dir={"fpdf": "fpdf"},
        test_suite="setup.run_test_suite",
        install_requires=[
            "Pillow>=4,<=8",
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
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: Multimedia :: Graphics",
        ],
        keywords=["pdf", "unicode", "png", "jpg", "ttf"],
    )
