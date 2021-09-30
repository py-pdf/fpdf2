"""PDF Template Helpers for fpdf.py"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "LGPL 3.0"

import csv
import locale
import warnings

from .errors import FPDFException
from .fpdf import FPDF


def _rgb(col):
    return (col // 65536), (col // 256 % 256), (col % 256)


def _rgb_as_str(col):
    r, g, b = _rgb(col)
    if (r == 0 and g == 0 and b == 0) or g == -1:
        return f"{r / 255:.3f} g"
    return f"{r / 255:.3f} {g / 255:.3f} {b / 255:.3f} rg"


class FlexTemplate:
    """
    A flexible templating class.

    Allows to apply one or several template definitions to any page of
    a document in any combination.
    """

    def __init__(self, pdf, elements=None):
        """
        Arguments:

            pdf (fpdf.FPDF() instance):
                All content will be added to this object.

            elements (list of dicts):
                A template definition in a list of dicts.
                If you omit this, then you need to call either load_elements()
                or parse_csv() before doing anything else.
        """
        if not isinstance(pdf, FPDF):
            raise TypeError("'pdf' must be an instance of fpdf.FPDF()")
        self.pdf = pdf
        self.splitting_pdf = None  # for split_multicell()
        if elements:
            self.load_elements(elements)
        self.handlers = {
            "T": self._text,
            "L": self._line,
            "I": self._image,
            "B": self._rect,
            "BC": self._barcode,
            "C39": self._code39,
            "W": self._write,
        }
        self.texts = {}

    def load_elements(self, elements):
        """
        Load a template definition.

        Arguments:

            elements (list of dicts):
                A template definition in a list of dicts
        """
        self.elements = elements
        self.keys = []
        for e in elements:
            # priority is optional, but we need a default for sorting.
            if not "priority" in e:
                e["priority"] = 0
            for k in ("name", "type", "x1", "y1", "y2"):
                if k not in e:
                    raise KeyError(f"Mandatory key '{k}' missing in input data")
            # x2 is optional for barcode types, but needed for offset rendering
            if "x2" not in e:
                if e["type"] in ["B", "C39"]:
                    e["x2"] = 0
                else:
                    raise KeyError("Mandatory key 'x2' missing in input data")
            self.keys.append(e["name"].lower())

    @staticmethod
    def _parse_colorcode(s):
        """Allow hex and oct values for colors"""
        if s[:2] in ["0x", "0X"]:
            return int(s, 16)
        if s[0] == "0":
            return int(s, 8)
        return int(s)

    @staticmethod
    def _parse_multiline(s):
        i = int(s)
        if i > 0:
            return True
        if i < 0:
            return False
        return None

    def parse_csv(self, infile, delimiter=",", decimal_sep=".", encoding=None):
        """
        Load the template definition from a CSV file.

        Arguments:

            infile (string):
                The filename of the CSV file.

            delimiter (single character):
                The character that seperates the fields in the CSV file:
                Usually a comma, semicolon, or tab.

            decimal_sep (single character):
                The decimal separator used in the file.
                Usually either a point or a comma.

            encoding (string):
                The character encoding of the file.
                Default is the system default encoding.

        """

        def _varsep_float(s, default="0"):
            """Convert to float with given decimal seperator"""
            # glad to have nonlocal scoping...
            return float((s.strip() or default).replace(decimal_sep, "."))

        key_config = (
            # key, converter, mandatory
            ("name", str, True),
            ("type", str, True),
            ("x1", _varsep_float, True),
            ("y1", _varsep_float, True),
            ("x2", _varsep_float, True),
            ("y2", _varsep_float, True),
            ("font", str, False),
            ("size", _varsep_float, False),
            ("bold", int, False),
            ("italic", int, False),
            ("underline", int, False),
            ("foreground", self._parse_colorcode, False),
            ("background", self._parse_colorcode, False),
            ("align", str, False),
            ("text", str, False),
            ("priority", int, False),
            ("multiline", self._parse_multiline, False),
            ("rotate", _varsep_float, False),
        )
        self.elements = []
        if encoding is None:
            encoding = locale.getpreferredencoding()
        with open(infile, encoding=encoding) as f:
            for row in csv.reader(f, delimiter=delimiter):
                # fill in blanks for any missing items
                row.extend([""] * (len(key_config) - len(row)))
                kargs = {}
                for val, cfg in zip(row, key_config):
                    vs = val.strip()
                    if not vs:
                        if cfg[2]:  # mandatory
                            if cfg[0] == "x2" and row["type"] in ["B", "C39"]:
                                # two types don't need x2, but offset rendering does
                                pass
                            else:
                                raise FPDFException(
                                    f"Mandatory value '{cfg[0]}' missing in csv data"
                                )
                        elif cfg[0] == "priority":
                            # formally optional, but we need some value for sorting
                            kargs["priority"] = 0
                        # otherwise, let the type handlers use their own defaults
                    else:
                        kargs[cfg[0]] = cfg[1](vs)
                self.elements.append(kargs)
        self.keys = [val["name"].lower() for val in self.elements]

    def __setitem__(self, name, value):
        if name.lower() not in self.keys:
            raise FPDFException(f"Element not loaded, cannot set item: {name}")
        self.texts[name.lower()] = value

    # setitem shortcut (may be further extended)
    set = __setitem__

    def __contains__(self, name):
        return name.lower() in self.keys

    def __getitem__(self, name):
        if name not in self.keys:
            return None
        key = name.lower()
        if key in self.texts:
            # text for this page:
            return self.texts[key]
        # find first element for default text:
        return next(
            (x["text"] for x in self.elements if x["name"].lower() == key), None
        )

    def split_multicell(self, text, element_name):
        """
        Split a string between words, for the parts to fit into a given element
        width. Additional splits will be made replacing any '\\n' characters.

        Arguments:

            text (string):
                The input text string.

            element_name (string):
                The name of the template element to fit the text inside.

        Returns:
            A list of substrings, each of which will fit into the element width
            when rendered in the element font style and size.
        """
        element = next(
            element
            for element in self.elements
            if element["name"].lower() == element_name.lower()
        )
        if not self.splitting_pdf:
            self.splitting_pdf = FPDF()
            self.splitting_pdf.add_page()
        style = ""
        if element["bold"]:
            style += "B"
        if element["italic"]:
            style += "I"
        if element["underline"]:
            style += "U"
        self.splitting_pdf.set_font(element["font"], style, element["size"])
        return self.splitting_pdf.multi_cell(
            w=element["x2"] - element["x1"],
            h=element["y2"] - element["y1"],
            txt=str(text),
            align=element["align"],
            split_only=True,
        )

    def _text(
        self,
        rotations,
        *_,
        x1=0,
        y1=0,
        x2=0,
        y2=0,
        text="",
        font="helvetica",
        size=10,
        bold=False,
        italic=False,
        underline=False,
        align="",
        foreground=0,
        background=0xFFFFFF,
        multiline=None,
        **__,
    ):
        if not text:
            return
        pdf = self.pdf
        if pdf.text_color != _rgb_as_str(foreground):
            pdf.set_text_color(*_rgb(foreground))
        if pdf.fill_color != _rgb_as_str(background):
            pdf.set_fill_color(*_rgb(background))

        font = font.strip().lower()
        style = ""
        for tag in "B", "I", "U":
            if text.startswith(f"<{tag}>") and text.endswith(f"</{tag}>"):
                text = text[3:-4]
                style += tag
        if bold:
            style += "B"
        if italic:
            style += "I"
        if underline:
            style += "U"
        pdf.set_font(font, style, size)
        width, height = x2 - x1, y2 - y1
        rotate = __.get("rotate")
        if rotate:
            rotations.append((rotate, x1, y2))
        if multiline is None:  # write without wrapping/trimming (default)
            self._render_rotated(
                (x1, y1),
                pdf.cell,
                (),
                {
                    "w": width,
                    "h": height,
                    "txt": text,
                    "border": 0,
                    "ln": 0,
                    "align": align,
                    "fill": True,
                },
                rotations,
            )
        elif multiline:  # automatic word - warp
            self._render_rotated(
                (x1, y1),
                pdf.multi_cell,
                (),
                {
                    "w": width,
                    "h": height,
                    "txt": text,
                    "border": 0,
                    "align": align,
                    "fill": True,
                },
                rotations,
            )
        else:  # trim to fit exactly the space defined
            text = pdf.multi_cell(
                w=width, h=height, txt=text, align=align, split_only=True
            )[0]
            self._render_rotated(
                (x1, y1),
                pdf.cell,
                (),
                {
                    "w": width,
                    "h": height,
                    "txt": text,
                    "border": 0,
                    "ln": 0,
                    "align": align,
                    "fill": True,
                },
                rotations,
            )

    def _line(self, rotations, *_, x1=0, y1=0, x2=0, y2=0, size=0, foreground=0, **__):
        pdf = self.pdf
        if pdf.draw_color.lower() != _rgb_as_str(foreground):
            pdf.set_draw_color(*_rgb(foreground))
        pdf.set_line_width(size)
        rotate = __.get("rotate")
        if rotate:
            rotations.append((rotate, x1, y2))
        self._render_rotated(None, pdf.line, (x1, y1, x2, y2), {}, rotations)

    def _rect(
        self,
        rotations,
        *_,
        x1=0,
        y1=0,
        x2=0,
        y2=0,
        size=0,
        foreground=0,
        background=0xFFFFFF,
        **__,
    ):
        pdf = self.pdf
        if pdf.draw_color.lower() != _rgb_as_str(foreground):
            pdf.set_draw_color(*_rgb(foreground))
        if pdf.fill_color != _rgb_as_str(background):
            pdf.set_fill_color(*_rgb(background))
        pdf.set_line_width(size)
        rotate = __.get("rotate")
        if rotate:
            rotations.append((rotate, x1, y2))
        self._render_rotated(
            None, pdf.rect, (x1, y1, x2 - x1, y2 - y1), {"style": "FD"}, rotations
        )

    def _image(self, rotations, *_, x1=0, y1=0, x2=0, y2=0, text="", **__):
        if text:
            rotate = __.get("rotate")
            if rotate:
                rotations.append((rotate, x1, y2))
            self._render_rotated(
                None,
                self.pdf.image,
                (text, x1, y1),
                {"w": x2 - x1, "h": y2 - y1, "link": ""},
                rotations,
            )

    def _barcode(
        self,
        rotations,
        *_,
        x1=0,
        y1=0,
        x2=0,
        y2=0,
        text="",
        font="interleaved 2of5 nt",
        size=1,
        foreground=0,
        **__,
    ):
        # pylint: disable=unused-argument
        pdf = self.pdf
        if pdf.fill_color.lower() != _rgb_as_str(foreground):
            pdf.set_fill_color(*_rgb(foreground))
        font = font.lower().strip()
        if font == "interleaved 2of5 nt":
            rotate = __.get("rotate")
            if rotate:
                rotations.append((rotate, x1, y2))
            self._render_rotated(
                None,
                pdf.interleaved2of5,
                (text, x1, y1),
                {"w": size, "h": y2 - y1},
                rotations,
            )

    def _code39(
        self,
        rotations,
        *_,
        x1=0,
        y1=0,
        y2=0,
        text="",
        size=1.5,
        foreground=0,
        x=None,
        y=None,
        w=None,
        h=None,
        **__,
    ):
        if x is not None or y is not None or w is not None or h is not None:
            raise ValueError(
                "Arguments x/y/w/h are invalid. Use x1/y1/y2/size instead."
            )
        pdf = self.pdf
        if pdf.fill_color.lower() != _rgb_as_str(foreground):
            pdf.set_fill_color(*_rgb(foreground))
        h = y2 - y1
        if h <= 0:
            h = 5
        rotate = __.get("rotate")
        if rotate:
            rotations.append((rotate, x1, y2))
        self._render_rotated(None, pdf.code39, (text, x1, y1, size, h), {}, rotations)

    # Added by Derek Schwalenberg Schwalenberg1013@gmail.com to allow (url) links in
    # templates (using write method) 2014-02-22
    def _write(
        self,
        rotations,
        *_,
        x1=0,
        y1=0,
        x2=0,
        y2=0,
        text="",
        font="helvetica",
        size=10,
        bold=False,
        italic=False,
        underline=False,
        link="",
        foreground=0,
        **__,
    ):
        # pylint: disable=unused-argument
        pdf = self.pdf
        if pdf.text_color != _rgb_as_str(foreground):
            pdf.set_text_color(*_rgb(foreground))
        font = font.strip().lower()
        style = ""
        for tag in "B", "I", "U":
            if text.startswith(f"<{tag}>") and text.endswith(f"</{tag}>"):
                text = text[3:-4]
                style += tag
        if bold:
            style += "B"
        if italic:
            style += "I"
        if underline:
            style += "U"
        pdf.set_font(font, style, size)
        rotate = __.get("rotate")
        if rotate:
            rotations.append((rotate, x1, y2))
        self._render_rotated((x1, y1), pdf.write, (5, text, link), {}, rotations)

    def _render_rotated(self, pos, func, args, kwargs, rotations):
        # Solves issue 226
        # Settings operations (fonts, colors, line widths etc.) must not appear
        # within a rotation context.
        # The solution is to queue up rotations and execute them all in one go
        # once everything else has been set up.
        # Technically, we could keep rotating until we're dizzy (up to Pythons
        # recursion limit), but in practise we take two turns at most.
        if rotations:
            with self.pdf.rotation(*(rotations[0])):
                self._render_rotated(pos, func, args, kwargs, rotations[1:])
        else:
            if pos:
                self.pdf.set_xy(*pos)
            func(*args, **kwargs)

    def render(self, offsetx=0.0, offsety=0.0, rotate=0.0):
        sorted_elements = sorted(self.elements, key=lambda x: x["priority"])
        for element in sorted_elements:
            element = element.copy()
            element["text"] = self.texts.get(
                element["name"].lower(), element.get("text", "")
            )
            element["x1"] = element["x1"] + offsetx
            element["y1"] = element["y1"] + offsety
            element["x2"] = element["x2"] + offsetx
            element["y2"] = element["y2"] + offsety
            handler_name = element["type"].upper()
            if rotate:  # don't rotate by 0.0 degrees
                rotations = [
                    (rotate, offsetx, offsety),
                ]
                self.handlers[handler_name](rotations, **element)
            else:
                self.handlers[handler_name]([], **element)
        self.texts = {}  # reset modified entries for the next page


class Template(FlexTemplate):
    """
    A simple templating class.

    Allows to apply a single template definition to all pages of a document.
    """

    # Disabling this check due to the "format" parameter below:
    # pylint: disable=redefined-builtin
    # pylint: disable=unused-argument
    def __init__(
        self,
        infile=None,
        elements=None,
        format="A4",
        orientation="portrait",
        unit="mm",
        title="",
        author="",
        subject="",
        creator="",
        keywords="",
    ):
        """
        Arguments:

            infile (str):
                [**DEPRECATED**] unused, will be removed in a later version

            elements (list of dicts):
                A template definition in a list of dicts.
                If you omit this, then you need to call either load_elements()
                or parse_csv() before doing anything else.

            format (str):
                The page format of the document (eg. "A4" or "letter").

            orientation (str):
                The orientation of the document.
                Possible values are "portrait"/"P" or "landscape"/"L"

            unit (str):
                The units used in the template definition.
                One of "mm", "cm", "in", "pt", or a number for points per unit.

            title (str): The title of the document.

            author (str): The author of the document.

            subject (str): The subject matter of the document.

            creator (str): The creator of the document.
        """

        pdf = FPDF(format=format, orientation=orientation, unit=unit)
        pdf.set_title(title)
        pdf.set_author(author)
        pdf.set_creator(creator)
        pdf.set_subject(subject)
        pdf.set_keywords(keywords)
        super().__init__(pdf=pdf, elements=elements)

    def add_page(self):
        """Finish the current page, and proceed to the next one."""
        if self.pdf.page:
            self.render()
        self.pdf.add_page()

    # pylint: disable=arguments-differ
    def render(self, outfile=None, dest=None):
        """
        Finish the document and process all pending data.

        Arguments:

            outfile (str):
                If given, the PDF file will be written to this file name.
                Alternatively, the `.pdf.output()` method can be manually called.

            dest (str):
                [**DEPRECATED**] unused, will be removed in a later version.
        """
        if dest:
            warnings.warn(
                '"dest" is unused and will soon be deprecated',
                PendingDeprecationWarning,
            )
        self.pdf.set_font("helvetica", "B", 16)
        self.pdf.set_auto_page_break(False, margin=0)
        super().render()
        if outfile:
            self.pdf.output(outfile)
