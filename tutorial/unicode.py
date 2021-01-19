#!/usr/bin/env python

from fpdf import FPDF
import sys

pdf = FPDF()
pdf.add_page()

# Add a DejaVu Unicode font (uses UTF-8)
# Supports more than 200 languages. For a coverage status see:
# http://dejavu.svn.sourceforge.net/viewvc/dejavu/trunk/dejavu-fonts/langcover.txt
pdf.add_font("DejaVu", fname="DejaVuSansCondensed.ttf", uni=True)
pdf.set_font("DejaVu", size=14)

text = """
English: Hello World
Greek: Γειά σου κόσμος
Polish: Witaj świecie
Portuguese: Olá mundo
Russian: Здравствуй, Мир
Vietnamese: Xin chào thế giới
Arabic: مرحبا العالم
Hebrew: שלום עולם
"""

for txt in text.split("\n"):
    pdf.write(8, txt)
    pdf.ln(8)

# Add a Indic Unicode font (uses UTF-8)
# Supports: Bengali, Devanagari, Gujarati,
#           Gurmukhi (including the variants for Punjabi)
#           Kannada, Malayalam, Oriya, Tamil, Telugu, Tibetan
pdf.add_font("gargi", fname="gargi.ttf", uni=True)
pdf.set_font("gargi", size=14)
pdf.write(8, "Hindi: नमस्ते दुनिया")
pdf.ln(20)

# Add a AR PL New Sung Unicode font (uses UTF-8)
# The Open Source Chinese Font (also supports other east Asian languages)
pdf.add_font("fireflysung", fname="fireflysung.ttf", uni=True)
pdf.set_font("fireflysung", size=14)
pdf.write(8, "Chinese: 你好世界\n")
pdf.write(8, "Japanese: こんにちは世界\n")
pdf.ln(10)

# Add a Alee Unicode font (uses UTF-8)
# General purpose Hangul truetype fonts that contain Korean syllable
# and Latin9 (iso8859-15) characters.
pdf.add_font("eunjin", fname="Eunjin.ttf", uni=True)
pdf.set_font("eunjin", size=14)
pdf.write(8, "Korean: 안녕하세요")
pdf.ln(20)

# Add a Fonts-TLWG (formerly ThaiFonts-Scalable) (uses UTF-8)
pdf.add_font("waree", fname="Waree.ttf", uni=True)
pdf.set_font("waree", size=14)
pdf.write(8, "Thai: สวัสดีชาวโลก")
pdf.ln(20)

# Select a standard font (uses windows-1252)
pdf.set_font("helvetica", size=14)
pdf.ln(10)
pdf.write(5, "This is standard built-in font")

fn = "unicode.pdf"
pdf.output(fn)
import os

try:
    os.startfile(fn)
except:
    os.system(f'xdg-open "{fn}"')
