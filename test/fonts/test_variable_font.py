"""
Tests for variable fonts feature
"""

from pathlib import Path

import pytest

from fpdf import FPDF
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


def test_font_without_variations(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Roboto Variable", "", HERE / "Roboto-Variable.ttf")
    pdf.set_font("Roboto Variable", "")
    pdf.cell(
        w=pdf.epw,
        text="Roboto Variable Font - unspecified axes",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    assert_pdf_equal(pdf, HERE / "variable_font_without_variations.pdf", tmp_path)


def test_font_with_variations(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(
        "Roboto Variable",
        "",
        HERE / "Roboto-Variable.ttf",
        variations={
            "B": {"wght": 900, "wdth": 75},
        },
    )
    pdf.set_font("Roboto Variable", "B", 20)
    pdf.cell(
        w=pdf.epw,
        text="Roboto Variable Font - Condensed Bold (wght=900, wdth=75)",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    assert_pdf_equal(pdf, HERE / "variable_font_with_variations.pdf", tmp_path)


def test_invalid_variable_font():
    static_font_path = HERE / "Roboto-Regular.ttf"

    pdf = FPDF()
    pdf.add_page()
    with pytest.raises(AttributeError) as error:
        pdf.add_font(
            "Roboto Variable",
            "",
            static_font_path,
            variations={
                "": {"B": {"wght": 900, "wdth": 75}},
            },
        )
        assert str(error.value) == f"{static_font_path} is not a variable font"


def test_font_already_added():
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(
        "Roboto Variable",
        "",
        HERE / "Roboto-Variable.ttf",
        variations={"": {"wght": 400, "wdth": 100}, "B": {"wght": 600, "wdth": 100}},
    )

    #  Notice the B after 'roboto variable' in the match message
    with pytest.warns(
        UserWarning,
        match="Core font or font already added 'roboto variableB': doing nothing",
    ):
        # Adding another variation of the same font with a different font weight.
        pdf.add_font(
            "Roboto Variable",
            "",
            HERE / "Roboto-Variable.ttf",
            variations={"B": {"wght": 900, "wdth": 100}},
        )


def test_font_with_one_axis(tmp_path):
    pdf = FPDF()
    pdf.add_page()

    pdf.add_font(
        "Roboto Variable",
        "",
        HERE / "Roboto-Variable.ttf",
        variations={"": {"wght": 100}},
    )
    pdf.set_font("Roboto Variable", "", 20)
    pdf.cell(
        w=pdf.epw,
        text="Roboto Variable Thin (wght=100)",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.add_font(
        "Roboto Variable",
        "",
        HERE / "Roboto-Variable.ttf",
        variations={"B": {"wdth": None, "wght": 500}},
    )
    pdf.set_font("Roboto Variable", "B", 20)
    pdf.cell(
        w=pdf.epw,
        text="Roboto Variable Bolder(wdth=None, wght=500)",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    assert_pdf_equal(pdf, HERE / "variable_font_with_one_modified_axis.pdf", tmp_path)


def test_invalid_axes_dict():
    pdf = FPDF()
    pdf.add_page()

    # Value for "" is a string instead of a dict.
    invalid_variations_dict = {"B": ""}

    with pytest.raises(ValueError) as error:
        pdf.add_font(
            "Roboto Variable",
            "",
            HERE / "Roboto-Variable.ttf",
            variations=invalid_variations_dict,
        )
        assert error == "Variations dictionary is invalid"


def test_variations_not_dictionary():
    pdf = FPDF()
    pdf.add_page()

    # variations is not a dict
    invalid_variations_list = []
    with pytest.raises(TypeError) as error:
        pdf.add_font(
            "Roboto Variable",
            "",
            HERE / "Roboto-Variable.ttf",
            variations=invalid_variations_list,
        )
        assert error == "Variations, if specified, must be a dictionary"


def test_variations_are_axes(tmp_path):
    pdf = FPDF()
    pdf.add_page()

    # Provide axes dictionary instead of variations
    # and also provide a style.
    pdf.add_font(
        "Roboto Variable",
        "B",
        HERE / "Roboto-Variable.ttf",
        variations={"wght": 600},
    )

    pdf.set_font("Roboto Variable", "B", 20)

    pdf.cell(
        w=pdf.epw,
        text="Roboto Variable Bold(wdth=600)",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    assert_pdf_equal(pdf, HERE / "variable_font_variations_are_axes.pdf", tmp_path)


def test_multicell_and_markdown(tmp_path):
    pdf = FPDF()
    pdf.add_page()

    # Add font with regular and bold style, but render
    # bold text using markdown and multi_cell() method.
    pdf.add_font(
        "Roboto Variable",
        "",
        HERE / "Roboto-Variable.ttf",
        variations={"": {"wdth": 100, "wght": 400}, "B": {"wght": 600}},
    )
    pdf.set_font("Roboto Variable", "", 20)

    pdf.multi_cell(
        w=pdf.epw,
        text="Regular and **Bold** text",
        markdown=True,
        new_x="LMARGIN",
        new_y="NEXT",
    )
    assert_pdf_equal(pdf, HERE / "variable_font_with_markdown.pdf", tmp_path)
