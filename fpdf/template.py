"""PDF Template Helpers for fpdf.py"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "LGPL 3.0"

import csv, locale, warnings

from .deprecation import get_stack_level
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
            "E": self._ellipse,
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
        key_config = {
            # key: type
            "name": (str, type(None)),
            "type": (str, type(None)),
            "x1": (int, float),
            "y1": (int, float),
            "x2": (int, float),
            "y2": (int, float),
            "font": (str, type(None)),
            "size": (int, float),
            "bold": object,  # "bool or equivalent"
            "italic": object,
            "underline": object,
            "foreground": int,
            "background": int,
            "align": (str, type(None)),
            "text": (str, type(None)),
            "priority": int,
            "multiline": (bool, type(None)),
            "rotate": (int, float),
        }

        self.elements = elements
        self.keys = []
        for e in elements:
            # priority is optional, but we need a default for sorting.
            if not "priority" in e:
                e["priority"] = 0
            for k in ("name", "type", "x1", "y1", "y2"):
                if k not in e:
                    if e["type"] == "C39":
                        # lots of legacy special casing.
                        # We need to do that here, so that rotation and scaling
                        # still work.
                        if k == "x1" and "x" in e:
                            e["x1"] = e["x"]
                            continue
                        if k == "y1" and "y" in e:
                            e["y1"] = e["y"]
                            continue
                        if k == "y2" and "h" in e:
                            e["y2"] = e["y1"] + e["h"]
                            continue
                    raise KeyError(f"Mandatory key '{k}' missing in input data")
            # x2 is optional for barcode types, but needed for offset rendering
            if "x2" not in e:
                if e["type"] in ["BC", "C39"]:
                    e["x2"] = 0
                else:
                    raise KeyError("Mandatory key 'x2' missing in input data")
            if not "size" in e and e["type"] == "C39":
                if "w" in e:
                    e["size"] = e["w"]
            for k, t in key_config.items():
                if k in e and not isinstance(e[k], t):
                    ttype = (
                        t.__name__
                        if isinstance(t, type)
                        else " or ".join([f"'{x.__name__}'" for x in t])
                    )
                    raise TypeError(
                        f"Value of element item '{k}' must be {ttype}, not '{type(e[k]).__name__}'."
                    )
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
                            if cfg[0] == "x2" and row[1] in ["BC", "C39"]:
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
        assert isinstance(
            name, str
        ), f"name must be of type 'str', not '{type(name).__name__}'."
        # value has too many valid types to reasonably check here
        if name.lower() not in self.keys:
            raise FPDFException(f"Element not loaded, cannot set item: {name}")
        self.texts[name.lower()] = value

    # setitem shortcut (may be further extended)
    set = __setitem__

    def __contains__(self, name):
        assert isinstance(
            name, str
        ), f"name must be of type 'str', not '{type(name).__name__}'."
        return name.lower() in self.keys

    def __getitem__(self, name):
        assert isinstance(
            name, str
        ), f"name must be of type 'str', not '{type(name).__name__}'."
        if name not in self.keys:
            raise KeyError(name)
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
        if element.get("bold"):
            style += "B"
        if element.get("italic"):
            style += "I"
        if element.get("underline"):
            style += "U"
        self.splitting_pdf.set_font(element["font"], style, element["size"])
        return self.splitting_pdf.multi_cell(
            w=element["x2"] - element["x1"],
            h=element["y2"] - element["y1"],
            txt=str(text),
            align=element.get("align", ""),
            dry_run=True,
            output="LINES",
        )

    def _text(
        self,
        *_,
        x1=0,
        y1=0,
        x2=0,
        y2=0,
        text="",
        font="helvetica",
        size=10,
        scale=1.0,
        bold=False,
        italic=False,
        underline=False,
        align="",
        foreground=0,
        background=None,
        multiline=None,
        **__,
    ):
        if not text:
            return
        pdf = self.pdf
        if pdf.text_color != _rgb_as_str(foreground):
            pdf.set_text_color(*_rgb(foreground))
        if background is None:
            fill = False
        else:
            fill = True
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
        pdf.set_font(font, style, size * scale)
        pdf.set_xy(x1, y1)
        width, height = x2 - x1, y2 - y1
        if multiline is None:  # write without wrapping/trimming (default)
            pdf.cell(w=width, h=height, txt=text, border=0, align=align, fill=fill)
        elif multiline:  # automatic word - warp
            pdf.multi_cell(
                w=width, h=height, txt=text, border=0, align=align, fill=fill
            )
        else:  # trim to fit exactly the space defined
            text = pdf.multi_cell(
                w=width,
                h=height,
                txt=text,
                align=align,
                dry_run=True,
                output="LINES",
            )[0]
            pdf.cell(w=width, h=height, txt=text, border=0, align=align, fill=fill)

    def _line(
        self,
        *_,
        x1=0,
        y1=0,
        x2=0,
        y2=0,
        size=0,
        scale=1.0,
        foreground=0,
        **__,
    ):
        if self.pdf.draw_color.serialize().lower() != _rgb_as_str(foreground):
            self.pdf.set_draw_color(*_rgb(foreground))
        self.pdf.set_line_width(size * scale)
        self.pdf.line(x1, y1, x2, y2)

    def _rect(
        self,
        *_,
        x1=0,
        y1=0,
        x2=0,
        y2=0,
        size=0,
        scale=1.0,
        foreground=0,
        background=None,
        **__,
    ):
        pdf = self.pdf
        if pdf.draw_color.serialize().lower() != _rgb_as_str(foreground):
            pdf.set_draw_color(*_rgb(foreground))
        if background is None:
            style = "D"
        else:
            style = "FD"
            if pdf.fill_color != _rgb_as_str(background):
                pdf.set_fill_color(*_rgb(background))
        pdf.set_line_width(size * scale)
        pdf.rect(x1, y1, x2 - x1, y2 - y1, style=style)

    def _ellipse(
        self,
        *_,
        x1=0,
        y1=0,
        x2=0,
        y2=0,
        size=0,
        scale=1.0,
        foreground=0,
        background=None,
        **__,
    ):
        pdf = self.pdf
        if pdf.draw_color.serialize().lower() != _rgb_as_str(foreground):
            pdf.set_draw_color(*_rgb(foreground))
        if background is None:
            style = "D"
        else:
            style = "FD"
            if pdf.fill_color != _rgb_as_str(background):
                pdf.set_fill_color(*_rgb(background))
        pdf.set_line_width(size * scale)
        pdf.ellipse(x1, y1, x2 - x1, y2 - y1, style=style)

    def _image(self, *_, x1=0, y1=0, x2=0, y2=0, text="", **__):
        if text:
            self.pdf.image(text, x1, y1, w=x2 - x1, h=y2 - y1, link="")

    def _barcode(
        self,
        *_,
        x1=0,
        y1=0,
        x2=0,
        y2=0,
        text="",
        font="interleaved 2of5 nt",
        size=1,
        scale=1.0,
        foreground=0,
        **__,
    ):
        # pylint: disable=unused-argument
        pdf = self.pdf
        if pdf.fill_color.serialize().lower() != _rgb_as_str(foreground):
            pdf.set_fill_color(*_rgb(foreground))
        font = font.lower().strip()
        if font == "interleaved 2of5 nt":
            pdf.interleaved2of5(text, x1, y1, w=size * scale, h=y2 - y1)

    def _code39(
        self,
        *_,
        x1=0,
        y1=0,
        y2=0,
        text="",
        size=1.5,
        scale=1.0,
        foreground=0,
        x=None,
        y=None,
        w=None,
        h=None,
        **__,
    ):
        if x is not None or y is not None or w is not None or h is not None:
            warnings.warn(
                "code39 arguments x/y/w/h are deprecated, please use x1/y1/y2/size instead",
                DeprecationWarning,
                stacklevel=get_stack_level(),
            )
        pdf = self.pdf
        if pdf.fill_color.serialize().lower() != _rgb_as_str(foreground):
            pdf.set_fill_color(*_rgb(foreground))
        h = y2 - y1
        if h <= 0:
            h = 5
        pdf.code39(text, x1, y1, size * scale, h)

    # Added by Derek Schwalenberg Schwalenberg1013@gmail.com to allow (url) links in
    # templates (using write method) 2014-02-22
    def _write(
        self,
        *_,
        x1=0,
        y1=0,
        x2=0,
        y2=0,
        text="",
        font="helvetica",
        size=10,
        scale=1.0,
        bold=False,
        italic=False,
        underline=False,
        link="",
        foreground=0,
        **__,
    ):
        # pylint: disable=unused-argument
        if not text:
            return
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
        pdf.set_font(font, style, size * scale)
        pdf.set_xy(x1, y1)
        pdf.write(5, text, link)

    def render(self, offsetx=0.0, offsety=0.0, rotate=0.0, scale=1.0):
        """
        Add the contents of the template to the PDF document.

        Arguments:

            offsetx, offsety (float):
                Place the template to move its origin to the given coordinates.

            rotate (float):
                Rotate the inserted template around its (offset) origin.

            scale (float):
                Scale the inserted template by this factor.
        """
        sorted_elements = sorted(self.elements, key=lambda x: x["priority"])
        with self.pdf.local_context():
            for element in sorted_elements:
                ele = element.copy()  # don't want to modify the callers original
                ele["text"] = self.texts.get(ele["name"].lower(), ele.get("text", ""))
                if scale != 1.0:
                    ele["x1"] = ele["x1"] * scale
                    ele["y1"] = ele["y1"] * scale
                    ele["x2"] = ele["x1"] + ((ele["x2"] - element["x1"]) * scale)
                    ele["y2"] = ele["y1"] + ((ele["y2"] - element["y1"]) * scale)
                if offsetx:
                    ele["x1"] = ele["x1"] + offsetx
                    ele["x2"] = ele["x2"] + offsetx
                if offsety:
                    ele["y1"] = ele["y1"] + offsety
                    ele["y2"] = ele["y2"] + offsety
                ele["scale"] = scale
                handler_name = ele["type"].upper()
                if rotate:  # don't rotate by 0.0 degrees
                    with self.pdf.rotation(rotate, offsetx, offsety):
                        if "rotate" in ele and ele["rotate"]:
                            with self.pdf.rotation(ele["rotate"], ele["x1"], ele["y1"]):
                                self.handlers[handler_name](**ele)
                        else:
                            self.handlers[handler_name](**ele)
                else:
                    if "rotate" in ele and ele["rotate"]:
                        with self.pdf.rotation(ele["rotate"], ele["x1"], ele["y1"]):
                            self.handlers[handler_name](**ele)
                    else:
                        self.handlers[handler_name](**ele)
        self.texts = {}  # reset modified entries for the next page


class Template(FlexTemplate):
    """
    A simple templating class.

    Allows to apply a single template definition to all pages of a document.
    """

    # Disabling this check due to the "format" parameter below:
    # pylint: disable=redefined-builtin
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
                [**DEPRECATED since 2.2.0**] unused, will be removed in a later version

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
        if infile:
            warnings.warn(
                '"infile" is deprecated, unused and will soon be removed',
                DeprecationWarning,
                stacklevel=get_stack_level(),
            )
        for arg in (
            "format",
            "orientation",
            "unit",
            "title",
            "author",
            "subject",
            "creator",
            "keywords",
        ):
            # nosemgrep: python.lang.security.dangerous-globals-use.dangerous-globals-use
            if not isinstance(locals()[arg], str):
                raise TypeError(f'Argument "{arg}" must be of type str.')
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
                [**DEPRECATED since 2.2.0**] unused, will be removed in a later version.
        """
        if dest:
            warnings.warn(
                '"dest" is deprecated, unused and will soon be removed',
                DeprecationWarning,
                stacklevel=get_stack_level(),
            )
        self.pdf.set_font("helvetica", "B", 16)
        self.pdf.set_auto_page_break(False, margin=0)
        super().render()
        if outfile:
            self.pdf.output(outfile)
