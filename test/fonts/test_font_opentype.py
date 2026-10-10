from pathlib import Path

from fpdf import FPDF

from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_cid_keyed_cff_font_embeds_cff_font_program(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Shsans", fname=HERE / "SourceHanSansCN-Normal.otf")

    pdf.set_font("Shsans", size=14)
    pdf.multi_cell(
        w=0,
        text=(
            "Lorem ipsum dolor sit amet, consectetur adipisicing elit. Culpa labore "
            "quas fuga magnam, tempora repellendus ipsa, provident officiis adipisci "
            "modi ab perspiciatis ducimus pariatur dolor odio placeat odit atque? "
            "Aperiam. 天地玄黄 宇宙洪荒 日月盈昃 辰宿列张 寒来暑往 秋收冬藏 "
            "闰余成岁 律吕调阳"
        ),
    )

    assert_pdf_equal(
        pdf,
        HERE / "font_opentype.pdf",
        tmp_path,
    )
