import pytest
import fpdf


class TestAddPage:
    def test_throws_without_page(self):
        pdf = fpdf.FPDF()
        with pytest.raises(Exception) as e:
            pdf.text(1, 2, "ok")

        msg = "No page open, you need to call add_page() first"
        assert str(e.value) == msg


class TestOrientation:
    def test_portrait_landscape(self):
        l = fpdf.FPDF(orientation="l")
        landscape = fpdf.FPDF(orientation="landscape")
        p = fpdf.FPDF(orientation="p")
        portrait = fpdf.FPDF(orientation="portrait")

        assert l.w_pt == landscape.w_pt
        assert l.h_pt == landscape.h_pt
        assert l.def_orientation == landscape.def_orientation

        assert p.w_pt == portrait.w_pt
        assert p.h_pt == portrait.h_pt
        assert p.def_orientation == portrait.def_orientation

        assert landscape.w_pt == portrait.h_pt
        assert landscape.h_pt == portrait.w_pt

    def test_incorrect_orientation(self):
        with pytest.raises(Exception) as e:
            fpdf.FPDF(orientation="hello")

        msg = "Incorrect orientation: hello"
        assert str(e.value) == msg


class TestUnit:
    def test_constructor(self):
        with pytest.raises(Exception) as e:
            fpdf.FPDF(unit="smiles")

        assert str(e.value) == "Incorrect unit: smiles"

        assert fpdf.FPDF(unit="pt").k == pytest.approx(1)
        assert fpdf.FPDF(unit="mm").k == pytest.approx(2.83464566929)
        assert fpdf.FPDF(unit="cm").k == pytest.approx(28.3464566929)
        assert fpdf.FPDF(unit="in").k == pytest.approx(72)


class TestDocOption:
    def test_only_core_fonts_encoding(self):
        pdf = fpdf.FPDF()
        pdf.set_doc_option("core_fonts_encoding", 4)
        assert pdf.core_fonts_encoding == 4

        with pytest.raises(Exception) as e:
            pdf.set_doc_option("not core_fonts_encoding", None)

        msg = 'Unknown document option "not core_fonts_encoding"'
        assert str(e.value) == msg
