#!/usr/bin/env python

import re
from pathlib import Path

from setuptools import find_packages, setup


if __name__ == "__main__":
    version = re.findall(
        r'FPDF_VERSION = "(\d+.\d+.\d+[^"]*)"',
        Path("fpdf/fpdf.py").read_text(encoding="utf-8"),
    )[0]
    setup(
        name="fpdf2",
        version=version,
        description="Simple & fast PDF generation for Python",
        long_description=Path("README.md").read_text(encoding="utf-8"),
        long_description_content_type="text/markdown",
        author="Olivier PLATHEY ported by Max",
        maintainer="Lucas Cimon",
        url="https://pyfpdf.github.io/fpdf2/",
        download_url=f"https://github.com/PyFPDF/fpdf2/tarball/{version}",
        project_urls={
            "Documentation": "https://pyfpdf.github.io/fpdf2/",
            "Code": "https://github.com/PyFPDF/fpdf2",
            "Issue tracker": "https://github.com/PyFPDF/fpdf2/issues",
        },
        license="LGPLv3+",
        packages=find_packages(),
        package_dir={"fpdf": "fpdf"},
        install_requires=[
            "defusedxml",
            "svg.path",
            "Pillow>=6.2.2",  # minimum version tested there: https://github.com/PyFPDF/fpdf2/actions/runs/2295868575
            "fonttools",
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
