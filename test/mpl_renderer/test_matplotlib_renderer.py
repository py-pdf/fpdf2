from cmath import cos, sin
import io
import logging
import os
import time
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path as MplPath
from matplotlib import font_manager

from fpdf import FPDF

# from test.conftest import assert_pdf_equal

default_backend = plt.get_backend()
HERE = Path(__file__).resolve().parent
GENERATED_PDF_DIR = HERE / "generated_pdf"
os.makedirs(GENERATED_PDF_DIR, exist_ok=True)
font_file = HERE / "../fonts/DejaVuSans.ttf"
logging.getLogger("fpdf.svg").setLevel(logging.ERROR)


def create_fpdf(w_mm, h_mm):
    pdf = FPDF(unit="mm", format=(w_mm, h_mm))
    print(f"Adding font from file: {font_file}")
    pdf.add_font("dejavu sans", "", str(font_file))
    pdf.add_page()
    font_manager.fontManager.addfont(str(font_file))
    mpl.rcParams["font.sans-serif"] = ["dejavu sans"]
    return pdf


def test_mpl_simple_figure():

    plt.rcParams["font.sans-serif"][0] = "Arial"
    plt.switch_backend(default_backend)
    w_inch = 4
    h_inch = 3
    w_mm = w_inch * 25.4
    h_mm = h_inch * 25.4

    fig = gen_fig(w_inch, h_inch)

    svg_buffer = io.BytesIO()
    fig.savefig(svg_buffer, format="svg")
    svg_buffer.seek(0)

    pdf_svg = create_fpdf(w_mm, h_mm)
    pdf_svg.image(svg_buffer, x=0, y=0, w=w_mm, h=h_mm)
    pdf_svg.output(GENERATED_PDF_DIR / "test_simple_figure_svg.pdf")
    # assert_pdf_equal(
    #     pdf_svg,
    #     GENERATED_PDF_DIR / "test_simple_figure_svg.pdf",
    #     tmp_path,
    #     generate=True,
    # )

    plt.switch_backend("module://fpdf.fpdf_renderer")

    # Re-generate the figure to use FPDFRenderer backend
    fig = gen_fig(w_inch, h_inch)

    pdf_fpdf = create_fpdf(w_mm, h_mm)

    scale = float(w_mm / fig.bbox.width)
    origin = (0, 0 + h_mm)  # FPDF uses bottom-left as origin

    fig.savefig(fname=None, fpdf=pdf_fpdf, origin=origin, scale=scale)

    pdf_fpdf.output(GENERATED_PDF_DIR / "test_simple_figure_fpdf.pdf")
    # assert_pdf_equal(pdf_fpdf, GENERATED_PDF_DIR / "test_simple_figure_svg.pdf", tmp_path, ignore_original_obj_ids=True, ignore_id_changes=True)


def gen_fig(w_inch, h_inch):
    fig, ax = plt.subplots(figsize=(w_inch, h_inch))
    ax.plot([0, 1], [0, 1], "blue", linewidth=2)
    ax.set_title("Simple Figure")
    ax.set_xlabel("X Axis")
    ax.set_ylabel("Y Axis")
    return fig


def test_mpl_figure_with_arrows():

    plt.rcParams["font.sans-serif"][0] = "Arial"
    plt.switch_backend(default_backend)

    w_inch = 4
    h_inch = 3
    w_mm = w_inch * 25.4
    h_mm = h_inch * 25.4

    fig = gen_fig_arrows(w_inch, h_inch)

    svg_buffer = io.BytesIO()
    fig.savefig(svg_buffer, format="svg")
    svg_buffer.seek(0)

    pdf_svg = create_fpdf(w_mm, h_mm)
    pdf_svg.image(svg_buffer, x=0, y=0, w=w_mm, h=h_mm)
    pdf_svg.output(GENERATED_PDF_DIR / "test_arrows_figure_svg.pdf")

    plt.switch_backend("module://fpdf.fpdf_renderer")

    # Re-generate the figure to use FPDFRenderer backend
    fig = gen_fig_arrows(w_inch, h_inch)

    pdf_fpdf = create_fpdf(w_mm, h_mm)

    scale = float(w_mm / fig.bbox.width)
    origin = (0, 0 + h_mm)  # FPDF uses bottom-left as origin
    fig.savefig(fname=None, fpdf=pdf_fpdf, origin=origin, scale=scale)
    pdf_fpdf.output(GENERATED_PDF_DIR / "test_arrows_figure_fpdf.pdf")


def gen_fig_arrows(w_inch, h_inch):
    fig, ax = plt.subplots(figsize=(w_inch, h_inch))
    ax.plot([0, 1], [1, 0], "blue", linewidth=2)
    ax.set_title("Arrows Figure")
    ax.set_xlabel("X Axis")
    ax.set_ylabel("Y Axis")
    ax.arrow(
        0.2, 0.2, 0.4, 0.4, head_width=0.05, head_length=0.1, fc="orange", ec="red"
    )
    ax.arrow(0.3, 0.3, 0.4, 0.2, head_width=0.2, head_length=0.3, fc="blue", ec="green")
    return fig


def test_mpl_figure_with_labels():
    plt.rcParams["font.sans-serif"][0] = "Arial"
    plt.switch_backend(default_backend)

    w_inch = 4
    h_inch = 3
    w_mm = w_inch * 25.4
    h_mm = h_inch * 25.4

    fig = gen_fig_labels(w_inch, h_inch)

    svg_buffer = io.BytesIO()
    fig.savefig(svg_buffer, dpi=600, format="png")
    svg_buffer.seek(0)

    pdf_svg = create_fpdf(w_mm, h_mm)
    pdf_svg.image(svg_buffer, x=0, y=0, w=w_mm, h=h_mm)
    pdf_svg.output(GENERATED_PDF_DIR / "test_labels_figure_svg.pdf")

    plt.switch_backend("module://fpdf.fpdf_renderer")

    # Re-generate the figure to use FPDFRenderer backend
    fig = gen_fig_labels(w_inch, h_inch)

    pdf_fpdf = create_fpdf(w_mm, h_mm)

    scale = float(w_mm / fig.bbox.width)
    origin = (0, 0 + h_mm)  # FPDF uses bottom-left as origin
    fig.savefig(fname=None, fpdf=pdf_fpdf, origin=origin, scale=scale)
    pdf_fpdf.output(GENERATED_PDF_DIR / "test_labels_figure_fpdf.pdf")


def gen_fig_labels(w_inch, h_inch):
    fig, ax = plt.subplots(figsize=(w_inch, h_inch))
    ax.plot([0, 1], [1, 0], "blue", linewidth=2)
    ax.set_title("Labels Figure")
    ax.set_xlabel("X Axis")
    ax.set_ylabel("Y Axis")
    ax.get_yaxis().set_ticks([])
    ax.text(0.3, 0.3, "Label 0\u00b0", fontsize=12, color="green", rotation=0)
    ax.text(
        0.3, 0.2, "Label 0\u00b0", fontsize=12, color="green", rotation=0, ha="center"
    )
    ax.text(
        0.3, 0.1, "Label 0\u00b0", fontsize=12, color="green", rotation=0, ha="right"
    )
    ax.text(0.3, 0.3, "Label 30\u00b0", fontsize=12, color="red", rotation=30)
    ax.text(0.3, 0.3, "Label 60\u00b0", fontsize=12, color="blue", rotation=60)
    ax.text(0.3, 0.3, "Label 90\u00b0", fontsize=12, color="black", rotation=90)

    # ax.text(0.7, 0.7, "Label 0\u00B0", fontsize=4, color='green', rotation=0)
    # ax.text(0.7, 0.7, "Label -30\u00B0", fontsize=4, color='red', rotation=-30)
    # ax.text(0.7, 0.7, "Label -60\u00B0", fontsize=4, color='blue', rotation=-60)
    # ax.text(0.7, 0.7, "Label -90\u00B0", fontsize=4, color='black', rotation=-90)

    return fig


def test_mpl_figure_with_legend():

    plt.rcParams["font.sans-serif"][0] = "Arial"
    plt.switch_backend(default_backend)

    w_inch = 4
    h_inch = 3
    w_mm = w_inch * 25.4
    h_mm = h_inch * 25.4

    fig = gen_fig_legend(w_inch, h_inch)

    svg_buffer = io.BytesIO()
    fig.savefig(svg_buffer, format="svg")
    svg_buffer.seek(0)

    pdf_svg = create_fpdf(w_mm, h_mm)
    pdf_svg.image(svg_buffer, x=0, y=0, w=w_mm, h=h_mm)
    pdf_svg.output(GENERATED_PDF_DIR / "test_legend_figure_svg.pdf")

    plt.switch_backend("module://fpdf.fpdf_renderer")

    # Re-generate the figure to use FPDFRenderer backend
    fig = gen_fig_legend(w_inch, h_inch)

    pdf_fpdf = create_fpdf(w_mm, h_mm)

    scale = float(w_mm / fig.bbox.width)
    origin = (0, 0 + h_mm)  # FPDF uses bottom-left as origin

    fig.savefig(fname=None, fpdf=pdf_fpdf, origin=origin, scale=scale)
    pdf_fpdf.output(GENERATED_PDF_DIR / "test_legend_figure_fpdf.pdf")


def gen_fig_legend(w_inch, h_inch):

    fig, ax = plt.subplots(figsize=(w_inch, h_inch))
    ax.plot([0, 1], [1, 0], "blue", linewidth=1)
    ax.plot([0, 1], [0, 1], "green", linewidth=1)
    ax.legend(["Line 1", "Line 2"])
    ax.set_title("Legend Figure")
    ax.set_axis_off()

    return fig


def test_mpl_figure_with_bezier():
    plt.rcParams["font.sans-serif"][0] = "Arial"
    plt.switch_backend(default_backend)

    w_inch = 4
    h_inch = 3
    w_mm = w_inch * 25.4
    h_mm = h_inch * 25.4

    fig = gen_fig_bezier(w_inch, h_inch)

    svg_buffer = io.BytesIO()
    fig.savefig(svg_buffer, format="svg")
    svg_buffer.seek(0)

    pdf_svg = create_fpdf(w_mm, h_mm)
    pdf_svg.image(svg_buffer, x=0, y=0, w=w_mm, h=h_mm)
    pdf_svg.output(GENERATED_PDF_DIR / "test_bezier_figure_svg.pdf")

    plt.switch_backend("module://fpdf.fpdf_renderer")

    # Re-generate the figure to use FPDFRenderer backend
    fig = gen_fig_bezier(w_inch, h_inch)

    pdf_fpdf = create_fpdf(w_mm, h_mm)

    scale = float(w_mm / fig.bbox.width)
    origin = (0, 0 + h_mm)  # FPDF uses bottom-left as origin

    fig.savefig(fname=None, fpdf=pdf_fpdf, origin=origin, scale=scale)
    pdf_fpdf.output(GENERATED_PDF_DIR / "test_bezier_figure_fpdf.pdf")


def gen_fig_bezier(w_inch, h_inch):

    fig, ax = plt.subplots(figsize=(w_inch, h_inch))

    # Vertices must be a flat list of coordinate tuples
    verts = [
        (5, 30),
        (15, 55),
        (25, 15),
        (35, 40),  # 4 points for first curve
        (20, 10),
        (30, 0),
        (35, 10),
    ]  # 3 points for second curve

    # `codes` means: the instructions used to guide the line through the points
    codes = [
        MplPath.MOVETO,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CURVE4,  # Begin the curve
        MplPath.MOVETO,
        MplPath.CURVE3,
        MplPath.CURVE3,
    ]  # Start a new one

    bezier1 = mpatches.PathPatch(
        MplPath(verts, codes),
        # You can also tweak your line properties, like its color, width, etc.
        fc="none",
        transform=ax.transData,
        color="green",
        lw=2,
    )

    ax.add_patch(bezier1)
    ax.autoscale_view()

    return fig


def test_mpl_figure_with_lineplot():

    plt.switch_backend(default_backend)

    w_inch = 4
    h_inch = 3
    w_mm = w_inch * 25.4
    h_mm = h_inch * 25.4

    fig = gen_fig_lineplot(w_inch, h_inch)

    svg_buffer = io.BytesIO()
    fig.savefig(svg_buffer, format="svg")
    svg_buffer.seek(0)

    pdf_svg = create_fpdf(w_mm, h_mm)
    pdf_svg.image(svg_buffer, x=0, y=0, w=w_mm, h=h_mm)
    pdf_svg.output(GENERATED_PDF_DIR / "test_lineplot_figure_svg.pdf")

    plt.switch_backend("module://fpdf.fpdf_renderer")

    # Re-generate the figure to use FPDFRenderer backend
    fig = gen_fig_lineplot(w_inch, h_inch)

    pdf_fpdf = create_fpdf(w_mm, h_mm)

    scale = float(w_mm / fig.bbox.width)
    origin = (0, 0 + h_mm)  # FPDF uses bottom-left as origin

    fig.savefig(fname=None, fpdf=pdf_fpdf, origin=origin, scale=scale)
    pdf_fpdf.output(GENERATED_PDF_DIR / "test_lineplot_figure_fpdf.pdf")


def gen_fig_lineplot(w_inch, h_inch):
    fig, ax = plt.subplots(figsize=(w_inch, h_inch))

    t = [i * 0.01 for i in range(1000)]
    s = [sin(value) + cos(value * value) for value in t]
    ax.plot(t, s, "blue", linewidth=1)
    ax.set_title("Line Plot Figure")
    ax.set_xlabel("t")
    ax.set_ylabel("sin(t) + cos(t^2)")
    ax.autoscale_view()

    return fig


def test_mplrenderer_speed_test():

    plt.switch_backend(default_backend)

    ROUNDS = 1000
    w_inch = 4
    h_inch = 3
    w_mm = w_inch * 25.4
    h_mm = h_inch * 25.4

    fig = gen_fig_lineplot(w_inch, h_inch)

    svg_buffer = io.BytesIO()
    fig.savefig(svg_buffer, format="svg")
    svg_buffer.seek(0)
    plt.close(fig)

    pdf_svg = create_fpdf(210, 297)

    t0 = time.time()
    for i in range(ROUNDS):
        x = i / 10
        y = (i % 20) * 10
        pdf_svg.image(svg_buffer, x=x, y=y, w=w_mm, h=h_mm)

    pdf_svg.output(GENERATED_PDF_DIR / "test_speed_figure_svg.pdf")
    total_svg = time.time() - t0
    print(f"SVG backend time for {ROUNDS} rounds: {total_svg:.2f} seconds")

    plt.switch_backend("module://fpdf.fpdf_renderer")

    # Re-generate the figure to use FPDFRenderer backend
    fig = gen_fig_lineplot(w_inch, h_inch)

    pdf_fpdf = create_fpdf(210, 297)

    t0 = time.time()
    for i in range(ROUNDS):
        x = i / 10
        y = (i % 20) * 10
        # plot scale
        scale = float(w_mm / fig.bbox.width)
        origin = (x, 297 - y)  # FPDF uses bottom-left of page as origin
        fig.savefig(fname=None, fpdf=pdf_fpdf, origin=origin, scale=scale)

    plt.close(fig)
    pdf_fpdf.output(GENERATED_PDF_DIR / "test_speed_figure_fpdf.pdf")

    total_fpdf = time.time() - t0
    print(f"FPDF backend time for {ROUNDS} rounds: {total_fpdf:.2f} seconds")


def test_mpl_figure_with_linestyles():
    plt.rcParams["font.sans-serif"][0] = "Arial"
    plt.switch_backend(default_backend)

    w_inch = 4
    h_inch = 3
    w_mm = w_inch * 25.4
    h_mm = h_inch * 25.4

    fig = gen_fig_linestyles(w_inch, h_inch)

    svg_buffer = io.BytesIO()
    fig.savefig(svg_buffer, format="svg")
    svg_buffer.seek(0)

    pdf_svg = create_fpdf(w_mm, h_mm)
    pdf_svg.image(svg_buffer, x=0, y=0, w=w_mm, h=h_mm)
    pdf_svg.output(GENERATED_PDF_DIR / "test_linestyles_figure_svg.pdf")

    plt.switch_backend("module://fpdf.fpdf_renderer")

    # Re-generate the figure to use FPDFRenderer backend
    fig = gen_fig_linestyles(w_inch, h_inch)

    pdf_fpdf = create_fpdf(w_mm, h_mm)

    scale = float(w_mm / fig.bbox.width)
    origin = (0, 0 + h_mm)  # FPDF uses bottom-left as origin

    fig.savefig(fname=None, fpdf=pdf_fpdf, origin=origin, scale=scale)
    pdf_fpdf.output(GENERATED_PDF_DIR / "test_linestyles_figure_fpdf.pdf")


def gen_fig_linestyles(w_inch, h_inch):
    fig, ax = plt.subplots(figsize=(w_inch, h_inch))

    t = [i * 0.1 for i in range(100)]
    ax.plot(t, [0.5] * 100, color="blue", linestyle="solid", linewidth=2, label="solid")
    ax.plot(
        t, [0.4] * 100, color="orange", linestyle="dashed", linewidth=2, label="dashed"
    )
    ax.plot(
        t, [0.3] * 100, color="green", linestyle="dashdot", linewidth=2, label="dashdot"
    )
    ax.plot(
        t, [0.2] * 100, color="red", linestyle="dotted", linewidth=2, label="dotted"
    )
    ax.set_title("Line Styles Figure")
    ax.set_xlabel("t")
    ax.set_ylabel("Value")
    ax.autoscale_view()
    ax.legend()

    return fig
