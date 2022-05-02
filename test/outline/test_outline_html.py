from pathlib import Path

from fpdf import FPDF, HTMLMixin, HTML2FPDF
from test.conftest import assert_pdf_equal


HERE = Path(__file__).resolve().parent


class MyFPDF(FPDF, HTMLMixin):
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
    assert_pdf_equal(pdf, HERE / "html_toc.pdf", tmp_path)


def test_html_toc_2_pages(tmp_path):
    pdf = MyFPDF()
    pdf.add_page()
    pdf.write_html(
        """<h1>Document title</h1>
        <br><br><br>
        <u>Table of content:</u>
        <br>
        <toc pages="2"></toc>
        <h2>Subtitle 0</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 1</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 2</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 3</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 4</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 5</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 6</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 7</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 8</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 9</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 10</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 11</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 12</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 13</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 14</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 15</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 16</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 17</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 18</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 19</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 20</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 21</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 22</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 23</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 24</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 25</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 26</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 27</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 28</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 29</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 30</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 31</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 32</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 33</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 34</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 35</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 36</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 37</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 38</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 39</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 40</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 41</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 42</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 43</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 44</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 45</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 46</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 47</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 48</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 49</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 50</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 51</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 52</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 53</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 54</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        <h2>Subtitle 55</h2>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
        sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
        """
    )
    assert_pdf_equal(pdf, HERE / "html_toc_2_pages.pdf", tmp_path)


def test_html_toc_with_h1_as_2nd_heading(tmp_path):  # issue 239
    pdf = MyFPDF()
    pdf.add_page()
    pdf.write_html(
        """<toc></toc>
        <h2>?-1</h2>
        <h3>?-1-1</h3>
        <h1>1</h1>
        <h2>1-1</h2>
        <h3>1-1-1</h3>"""
    )
    assert_pdf_equal(pdf, HERE / "html_toc_with_h1_as_2nd_heading.pdf", tmp_path)


def test_custom_HTML2FPDF(tmp_path):  # issue 240
    class CustomHTML2FPDF(HTML2FPDF):
        def render_toc(self, pdf, outline):
            pdf.cell(txt="Table of contents:", new_x="LMARGIN", new_y="NEXT")
            for section in outline:
                pdf.cell(
                    txt=f"* {section.name} (page {section.page_number})",
                    new_x="LMARGIN",
                    new_y="NEXT",
                )

    class CustomPDF(FPDF, HTMLMixin):
        HTML2FPDF_CLASS = CustomHTML2FPDF

    pdf = CustomPDF()
    pdf.add_page()
    pdf.write_html(
        """<toc></toc>
        <h1>Level 1</h1>
        <h2>Level 2</h2>
        <h3>Level 3</h3>
        <h4>Level 4</h4>
        <h5>Level 5</h5>
        <h6>Level 6</h6>
        <p>paragraph<p>"""
    )
    assert_pdf_equal(pdf, HERE / "custom_HTML2FPDF.pdf", tmp_path)
