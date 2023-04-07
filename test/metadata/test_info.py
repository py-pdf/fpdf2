from pathlib import Path

from fpdf import FPDF
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent

XMP_METADATA = """<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="fpdf2">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about="">
      <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">
        <rdf:Alt>
          <rdf:li xml:lang="x-default">{title}</rdf:li>
        </rdf:Alt>
      </dc:title>
    </rdf:Description>
    <rdf:Description rdf:about="">
      <dc:description xmlns:dc="http://purl.org/dc/elements/1.1/">
        <rdf:Alt>
          <rdf:li xml:lang="x-default">{desc}</rdf:li>
        </rdf:Alt>
      </dc:description>
    </rdf:Description>
    <rdf:Description rdf:about="">
      <dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">
        <rdf:Seq>
          <rdf:li>{creator}</rdf:li>
        </rdf:Seq>
      </dc:creator>
    </rdf:Description>
    <rdf:Description xmlns:pdf="http://ns.adobe.com/pdf/1.3/" rdf:about="" pdf:Keywords="{keywords}"/>
    <rdf:Description xmlns:pdf="http://ns.adobe.com/pdf/1.3/" rdf:about="" pdf:Producer="PyFPDF/fpdf2.X.Y"/>
    <rdf:Description xmlns:xmp="http://ns.adobe.com/xap/1.0/" rdf:about="" xmp:CreatorTool="fpdf2"/>
  </rdf:RDF>
</x:xmpmeta>"""


def document_operations(doc):
    doc.add_page()
    doc.set_font("helvetica", size=12)
    doc.cell(w=72, h=0, border=1, txt="hello world", fill=False, link="")


def test_put_info_all(tmp_path):
    """This test tests all possible inputs to FPDF#_put_info."""
    doc = FPDF()
    document_operations(doc)
    doc.set_title("sample title")
    doc.set_lang("en-US")
    doc.set_subject("sample subject")
    doc.set_author("sample author")
    doc.set_keywords("sample keywords")
    doc.set_creator("sample creator")
    doc.set_producer("PyFPDF/fpdf2.X.Y")
    assert_pdf_equal(doc, HERE / "put_info_all.pdf", tmp_path)


def test_put_info_some(tmp_path):
    """This test tests some possible inputs to FPDF#_put_info."""
    doc = FPDF()
    document_operations(doc)
    doc.set_title("sample title")
    doc.set_keywords("sample keywords")
    doc.set_creator("sample creator")
    assert_pdf_equal(doc, HERE / "put_info_some.pdf", tmp_path)


def test_xmp_metadata(tmp_path):
    doc = FPDF()
    document_operations(doc)
    doc.set_xmp_metadata(
        XMP_METADATA.format(
            title="My document title",
            desc="This is a test document for fpdf2 with XMP metadata",
            creator="Lucas Cimon",
            keywords="test data pdf fpdf2",
        )
    )
    assert_pdf_equal(doc, HERE / "xmp_metadata.pdf", tmp_path)


def test_metadata_unicode(tmp_path):  # issue 685
    doc = FPDF()
    document_operations(doc)
    doc.set_creator("༄༅། །སྒྲུབ།")
    doc.set_title("༄༅། །སྒྲུབ།")
    doc.set_keywords("༄༅། །སྒྲུབ།")
    doc.set_creator("༄༅། །སྒྲུབ།")
    assert_pdf_equal(doc, HERE / "metadata_unicode.pdf", tmp_path)


def test_xmp_metadata_unicode(tmp_path):  # issue 685
    doc = FPDF()
    document_operations(doc)
    doc.set_xmp_metadata(
        XMP_METADATA.format(
            title="༄༅། །སྒྲུབ།",
            desc="༄༅། །སྒྲུབ།",
            creator="༄༅། །སྒྲུབ།",
            keywords="༄༅། །སྒྲུབ།",
        )
    )
    assert_pdf_equal(doc, HERE / "xmp_metadata_unicode.pdf", tmp_path)
