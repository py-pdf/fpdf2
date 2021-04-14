from pathlib import Path

import fpdf
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


class MyFPDF(fpdf.FPDF, fpdf.HTMLMixin):
    pass


def test_html_toc(tmp_path):
    pdf = MyFPDF()
    pdf.add_page()
    pdf.write_html(
        """<h1>Document title</h1>
        <br><br><br>
        <u>Table of content:</u>
        <br>
        <toc></toc>
        <section><h2>Subtitle 1</h2><br>
            <section><h3>Subtitle 1.1</h3>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit,
            sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
            <section>
            <br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>
            <section><h3>Subtitle 1.2</h3><br>
            Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
            <section>
        <section>
        <br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>
        <br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>
        <section><h2>Subtitle 2</h2><br>
            <section><h3>Subtitle 2.1</h3><br>
            Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
            <section>
            <br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>
            <section><h3>Subtitle 2.2</h3><br>
            Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
            <section>
        <section>"""
    )
    assert_pdf_equal(pdf, HERE / "test_html_toc.pdf", tmp_path)
