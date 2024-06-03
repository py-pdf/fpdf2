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
        "Thai (ideally wouldn't wrap after the space after '1000'): นโยบาย\u200Bสาธารณะ\u200Bมี\u200Bความ\u200Bสำคัญ\u200Bต่อ\u200Bการ\u200Bสนับสนุน\u200Bการ\u200Bออก\u200Bแบบ\u200Bและ\u200Bการ\u200Bสร้าง\u200Bชุมชน\u200Bและ\u200Bเมือง\u200Bสุขภาพ\u200Bดี\u200Bและ\u200Bยั่งยืน รายการ\u200Bตรวจ\u200Bสอบนโยบาย\u200Bความ\u200Bท้าทาย 1,000 เมือง\u200Bสำหรับ\u200Bใช้\u200Bเพื่อ\u200Bประเมิน\u200Bการ\u200Bมี\u200Bอยู่\u200Bและ\u200Bคุณภาพ\u200Bของ\u200Bนโยบาย\u200Bที่\u200Bสอด\u200Bคล้อง\u200Bกับ\u200Bหลัก\u200Bฐาน\u200Bและ\u200Bหลัก\u200Bการ\u200Bสำหรับ\u200Bเมือง\u200Bที่\u200Bมี\u200Bสุขภาพ\u200Bดี\u200Bและ\u200Bยั่งยืน",
    )
    assert_pdf_equal(pdf, HERE / "thai_wraps_zerowidthspace.pdf", tmp_path)
