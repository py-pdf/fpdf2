#!/usr/bin/env python3

# Script to convert a GIF into an animated PDF file.
# Just for lulz.
# Script used in this article: https://chezsoi.org/lucas/blog/fpdf2-4-0-and-converting-gifs-to-pdfs.html

# REQUIRE: pip install fpdf2 imageio
# USAGE: ./gif2pdf.py $gif_filepath

import sys
from fpdf import FPDF
from imageio import mimread
from PIL import Image

in_filepath = sys.argv[1]
if not in_filepath.endswith(".gif"):
    print("Input file must be a GIF", file=sys.stderr)
    sys.exit(1)

imgs = mimread(in_filepath)
size = (imgs[0].shape[1], imgs[0].shape[0])

pdf = FPDF(format=size)
pdf.set_margin(0)
duration_in_secs = 0
for img in imgs:
    pdf.add_page(duration=duration_in_secs)
    # Converting the numpy.ndarray to a PIL.Image:
    pdf.image(Image.frombytes("RGBA", size, img.tobytes()), w=pdf.epw)
    duration_in_secs = img.meta["duration"] / 1000 or 0.04

out_filepath = in_filepath.replace(".gif", ".pdf")
pdf.output(out_filepath)
print(f'You can now open "{out_filepath}" in Adobe Acrobat Reader,')
print("press CTRL+L to launch presentation mode,")
print("and then ENTER to admire the animation!")
