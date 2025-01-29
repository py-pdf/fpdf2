from pathlib import Path

from fpdf import FPDF

from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_wraps_zerowidthspace(tmp_path):
    pdf = FPDF()
    pdf.add_font(fname=HERE / "Waree.ttf")
    pdf.set_font("Waree", size=12)
    pdf.add_page()
    pdf.write(
        8,
        "Thai (ideally wouldn't wrap after the space after '1000'): "
        + "นโยบาย\u200bสาธารณะ\u200bมี\u200bความ\u200bสำคัญ\u200bต่อ\u200b"
        + "การ\u200bสนับสนุน\u200bการ\u200bออก\u200bแบบ\u200bและ\u200bการ"
        + "\u200bสร้าง\u200bชุมชน\u200bและ\u200bเมือง\u200bสุขภาพ\u200bดี\u200b"
        + "และ\u200bยั่งยืน รายการ\u200bตรวจ\u200bสอบนโยบาย\u200bความ\u200b"
        + "ท้าทาย 1,000 เมือง\u200bสำหรับ\u200bใช้\u200bเพื่อ\u200bประเมิน\u200bการ"
        + "\u200bมี\u200bอยู่\u200bและ\u200bคุณภาพ\u200bของ\u200bนโยบาย\u200bที่"
        + "\u200bสอด\u200bคล้อง\u200bกับ\u200bหลัก\u200bฐาน\u200bและ\u200bหลัก"
        + "\u200bการ\u200bสำหรับ\u200bเมือง\u200bที่\u200bมี\u200bสุขภาพ\u200bดี"
        + "\u200bและ\u200bยั่งยืน",
    )
    assert_pdf_equal(pdf, HERE / "thai_wraps_zerowidthspace.pdf", tmp_path)
