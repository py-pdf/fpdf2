import re
from pathlib import Path

from setuptools import setup


if __name__ == "__main__":
    version = re.findall(
        r'FPDF_VERSION = "(\d+.\d+.\d+[^"]*)"',
        Path("fpdf/fpdf.py").read_text(encoding="utf-8"),
    )[0]
    setup(
        version=version,
        download_url=f"https://github.com/PyFPDF/fpdf2/tarball/{version}",
    )
