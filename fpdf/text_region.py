from .errors import FPDFException
from .enums import Align, XPos, YPos
from .line_break import MultiLineBreak

# Since Python doesn't have "friend classes"...
# pylint: disable=protected-access


class TextRegionMixin:
    """Mix-in to be added FPDF() in order to support text regions."""

    def __init__(self, *args, **kwargs):
        self.clear_text_region()
        super().__init__(*args, **kwargs)

    def register_text_region(self, region):
        self.__current_text_region = region

    def is_current_text_region(self, region):
        return self.__current_text_region == region

    def clear_text_region(self):
        self.__current_text_region = None


class Paragraph:
    def __init__(self, region, *args, align=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.region = region
        self.pdf = region.pdf
        if align:
            align = Align.coerce(align)
        self.align = align
        self._text_fragments = []
        self.current_y = 0
        super().__init__(*args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.region.end_paragraph()

    def write(self, txt: str):  # , link: str = ""):
        if not self.pdf.font_family:
            raise FPDFException("No font set, you need to call set_font() beforehand")
        normalized_string = self.pdf.normalize_text(txt).replace("\r", "")
        # YYY _preload_font_styles() should accept a "link" argument.
        styled_text_fragments = self.pdf._preload_font_styles(normalized_string, False)
        self._text_fragments.extend(styled_text_fragments)

    def _build_lines(self, current_y, print_sh):
        self.current_y = current_y
        text_lines = []
        multi_line_break = MultiLineBreak(
            self._text_fragments,
            max_width=self.region.get_width,
            align=self.align or self.region.align or Align.L,
            print_sh=print_sh,
        )
        self._text_fragments = []
        text_line = multi_line_break.get_line()
        while (text_line) is not None:
            self.current_y += text_line.height
            text_lines.append(text_line)
            text_line = multi_line_break.get_line()
        return text_lines


class ParagraphCollectorMixin:
    def __init__(self, pdf, *args, align="LEFT", **kwargs):
        self.pdf = pdf
        self.align = Align.coerce(align)  # default for auto paragraphs
        self._paragraphs = []
        self._has_paragraph = None
        super().__init__(pdf, *args, **kwargs)

    def __enter__(self):
        if self.pdf.is_current_text_region(self):
            raise FPDFException(
                f"Unable to enter the same {self.__class__.__name__} context recursively."
            )
        self._page = self.pdf.page
        self.pdf._push_local_stack()
        self.pdf.page = 0
        self.pdf.register_text_region(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.pdf.clear_text_region()
        self.pdf.page = self._page
        self.pdf._pop_local_stack()
        self.render()

    def write(self, txt: str):  # , link: str = ""):
        if self._has_paragraph == "EXPLICIT":
            raise FPDFException(
                "Conflicts with active paragraph. Consider adding your text there."
            )
        if self._has_paragraph is None:
            p = Paragraph(region=self, align=self.align)
            self._paragraphs.append(p)
            self._has_paragraph = "AUTO"
        self._paragraphs[-1].write(txt)

    def paragraph(self, align=None):
        if self._has_paragraph == "EXPLICIT":
            raise FPDFException("Unable to nest paragraphs.")
        p = Paragraph(region=self, align=align or self.align)
        self._paragraphs.append(p)
        self._has_paragraph = "EXPLICIT"
        return p

    def end_paragraph(self):
        if not self._has_paragraph:
            raise FPDFException("No active paragraph to end.")
        self._has_paragraph = None


class TextRegion(ParagraphCollectorMixin):
    """Abstract base class for all text region subclasses."""

    def _ln(self, h=None):
        self.pdf.ln(h)

    def current_x_extents(
        self, y, height
    ):  # xpylint: disable=no-self-use,unused-argument
        """Return the horizontal extents of the current line."""
        raise NotImplementedError()

    def _render_lines(self, text_lines):
        page_break_triggered = False
        self.pdf.y = max(self.pdf.y, self.pdf.t_margin)
        text_line = None
        for text_line_index, text_line in enumerate(text_lines):
            if text_line_index != 0:
                self._ln()
            # print(self.pdf.y + text_line.height, self.pdf.page_break_trigger)
            if hasattr(self, "accept_page_break"):
                if self.pdf.y + text_line.height > self.pdf.page_break_trigger:
                    page_break_triggered = self.accept_page_break()
            new_page = self.pdf._render_styled_text_line(
                text_line,
                text_line.max_width,
                h=text_line.height,
                border=0,
                new_x=XPos.WCONT,
                new_y=YPos.TOP,
                fill=False,
                #                link=link,
            )
            page_break_triggered = page_break_triggered or new_page
        if text_line and text_line.trailing_nl:
            # The line renderer can't handle trailing newlines in the text.
            self.pdf._ln()
        return page_break_triggered

    def collect_lines(self, print_sh: bool = False):
        text_lines = []
        current_y = self.pdf.y
        for paragraph in self._paragraphs:
            cur_lines = paragraph._build_lines(current_y, print_sh)
            if not cur_lines:
                continue
            current_y = paragraph.current_y
            text_lines.extend(cur_lines)
        return text_lines

    def render(self, print_sh: bool = False):
        if not self._paragraphs:
            return False
        text_lines = self.collect_lines(print_sh)
        return self._render_lines(text_lines)

    def get_width(self, height):
        limits = self.current_x_extents(self.pdf.y, height)
        res = limits[1] - max(self.pdf.x, limits[0]) - 2 * self.pdf.c_margin
        return res


class TextColumnarMixin:
    """Enable a TextRegion to perform page breaks"""

    def __init__(self, pdf, *args, l_margin=None, r_margin=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.l_margin = pdf.l_margin if l_margin is None else l_margin
        left = self.l_margin
        self.r_margin = pdf.r_margin if r_margin is None else r_margin
        right = pdf.w - self.r_margin
        self._set_left_right(left, right)

    def _set_left_right(self, left, right):
        self.left = self.pdf.l_margin if left is None else left
        self.right = (self.pdf.w - self.pdf.r_margin) if right is None else right
        if self.right <= self.left:
            raise FPDFException(
                f"{self.__class__.__name__}(): "
                f"Right limit ({self.right}) lower than left limit ({self.left})."
            )

    def current_x_extents(self, y, height):  # pylint: disable=unused-argument
        """Return the horizontal extents of the current line.
        Columnar regions simply return the boundaries of the column.
        Regions with non-vertical boundaries need to check how the largest
        font-height in the current line actually fits in there.
        For that reason we include the current y and the line height.
        """
        return self.left, self.right


class TextColumns(TextRegion, TextColumnarMixin):
    def __init__(self, pdf, *args, ncols: int = 1, gap_width: float = 10, **kwargs):
        super().__init__(pdf, *args, **kwargs)
        self.cur_column = 0
        self.cur_top = self.pdf.t_margin
        self.ncols = ncols
        self.gap_width = gap_width
        total_w = self.right - self.left
        self.col_width = (total_w - (self.ncols - 1) * self.gap_width) / self.ncols
        # We calculate the column extents once in advance, and store them for lookup.
        # This way we can later also enable the possibility to request columns of
        # differing width.
        c_left = self.left
        self.cols = [(c_left, c_left + self.col_width)]
        for i in range(1, ncols):  # pylint: disable=unused-variable
            c_left += self.col_width + self.gap_width
            self.cols.append((c_left, c_left + self.col_width))

    def render(
        self,
        print_sh: bool = False,
        stay_below: bool = False,
        balance: bool = False,
    ):
        if not self._paragraphs:
            return False
        text_lines = self.collect_lines()
        if stay_below or (self.cur_column == 0 and balance):
            self.cur_top = self.pdf.y
        else:
            self.cur_top = self.pdf.t_margin
        if not text_lines:
            return False
        #        if not balance:
        return self._render_lines(text_lines)
        # balance the columns.

    #        hgt_lines = sum(l.height for l in text_lines)
    #        bottom = self.pdf.h - self.pdf.b_margin
    #        hgt_avail = bottom - self.pdf.y
    #        hgt_avail += (self.ncols - self.cur_column - 1) * (bottom - self.cur_top)
    # YYY Finish balancing

    def accept_page_break(self):
        if self.cur_column == self.ncols - 1:
            self.cur_top = self.pdf.t_margin
            self.cur_column = 0
            self.pdf.x = self.cols[self.cur_column][0]
            return True
        self.cur_column += 1
        self.pdf.x = self.cols[self.cur_column][0]
        self.pdf.y = self.cur_top
        return False

    def _ln(self, h=None):
        self.pdf.ln(h=h)
        self.pdf.x = self.cols[self.cur_column][0]

    def current_x_extents(self, y, height):
        left = self.cols[self.cur_column][0]
        right = self.cols[self.cur_column][1]
        return left, right
