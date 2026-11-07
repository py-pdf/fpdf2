from fpdf import FPDF


def _render_with_clip(clip):
    pdf = FPDF()
    pdf.set_compression(False)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    with clip(pdf):
        pdf.text(20, 20, "clipped")
    pdf.text(20, 40, "unclipped")
    return bytes(pdf.output())


def _assert_font_set_after_clip(content):
    clip_end = content.rfind(b"Q")
    unclipped_text = content.find(b"unclipped")
    assert clip_end != -1
    assert unclipped_text > clip_end
    assert b"Tf" in content[clip_end:unclipped_text]


def test_rect_clip_restores_font_state():
    content = _render_with_clip(lambda pdf: pdf.rect_clip(10, 10, 40, 40))
    _assert_font_set_after_clip(content)


def test_elliptic_clip_restores_font_state():
    content = _render_with_clip(lambda pdf: pdf.elliptic_clip(10, 10, 40, 40))
    _assert_font_set_after_clip(content)
