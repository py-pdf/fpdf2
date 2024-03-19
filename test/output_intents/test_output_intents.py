from pathlib import Path

from fpdf import FPDF
from fpdf.enums import OutputIntentSubType

# import pytest
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent

def test_output_intents_properties():
    """
    Make sure the properties in PDF return the correct
    value as of the originating Output Intent.
    """
    pdf = FPDF()

    assert pdf.output_intents is None

    pdf.set_output_intents(
        OutputIntentSubType.PDFA, 'sRGB'
    )  # should create the array and add PDFA
    pdf.set_output_intents(
        OutputIntentSubType.PDFX, 'AdobeRGB'
    )  # should add PDFX
    pdf.set_output_intents(
        OutputIntentSubType.PDFA, 'AdobeRGB'
    )  # should be discarded
    pdf.set_output_intents(
        OutputIntentSubType.ISOPDF, 'AdobeRGB'
    )  # should add ISOPDF

    assert pdf.output_intents == [
        {
            "subtype": OutputIntentSubType.PDFA,
            "output_condition_identifier": 'sRGB',
            "dest_output_profile": None,
            "info": None,
            "output_condition": None,
            "registry_name": None,
        },
        {
            "subtype": OutputIntentSubType.PDFX,
            "output_condition_identifier": 'AdobeRGB',
            "dest_output_profile": None,
            "info": None,
            "output_condition": None,
            "registry_name": None,
        },
        {
            "subtype": OutputIntentSubType.ISOPDF,
            "output_condition_identifier": 'AdobeRGB',
            "dest_output_profile": None,
            "info": None,
            "output_condition": None,
            "registry_name": None,
        },
    ]


def test_output_intents(tmp_path):
    """
    Make sure the Output Intents is set in PDF.
    """
    doc = FPDF()
    doc.set_output_intents(
        OutputIntentSubType.PDFA,
        "sRGB",
        'IEC 61966-2-1:1999',
        "http://www.color.org",
        FPDF.dest_output_profile(fn=HERE / "sRGB2014.icc", N=3, alternate="DeviceRGB"),
        "sRGB2014 (v2)",
    )
    # doc.set_output_intents(OutputIntentSubType.PDFX)
    doc.set_lang("de")
    doc.add_page()
    doc.set_font("Helvetica", size=20)
    for i, color in enumerate(
        (
            (255, 100, 100),
            (255, 255, 100),
            (255, 100, 255),
            (250, 250, 250),
            (0, 0, 0),
        )
    ):
        doc.set_text_color(*color)
        doc.text(20, 20 + 10 * i, f"{color}")
    assert_pdf_equal(doc, HERE / "text_color_with_one_output_intent.pdf", tmp_path, generate=False)
