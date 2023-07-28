from .errors import FPDFException
from .enums import Align, XPos, YPos
from .line_break import Fragment, DynamicMultiLineBreak, TextLine

# Since Python doesn't have "friend classes"...
# pylint: disable=protected-access


class TextRegionMixin:
    """Mixing for FPDF() to support text regions."""

    def __init__(self, *args, **kwargs):
        self.clear_text_region()
        super().__init__(*args, **kwargs)

    def register_text_region(self, region):
        self.__current_text_region = region

    def is_current_text_region(self, region):
        return self.__current_text_region == region

    def clear_text_region(self):
        self.__current_text_region = None


class TextCollectorMixin:

    def __init__(self, pdf, *args, **kwargs):
        self.pdf = pdf
        self._text_fragments = []
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

    def __exit__(self, exc_type, exc_value, traceback):
        self.pdf.clear_text_region()
        self.pdf.page = self._page
        self.pdf._pop_local_stack()


class TextRegion(TextCollectorMixin):

    col_wrapper = None

    def _ln(self, h=None):
        self.pdf.ln(h)

    def _build_lines(self, align, print_sh):
        text_lines = []
        multi_line_break = DynamicMultiLineBreak(
            self._text_fragments,
            width_cb=self.get_width,
            justify=(align == Align.J),
            print_sh=print_sh,
        )
        self._text_fragments = []
        text_line = multi_line_break.get_line_of_given_width()
        while (text_line) is not None:
            text_lines.append(text_line)
            text_line = multi_line_break.get_line_of_given_width()
        return text_lines

    def _render_lines(self, text_lines, align):
        page_break_triggered = False
        self.pdf.y = max(self.pdf.y, self.pdf.t_margin)
        text_line = None
        for text_line_index, text_line in enumerate(text_lines):
            is_last_line = text_line_index == len(text_lines) - 1
            if text_line_index != 0:
                self._ln()
            # print(self.pdf.y + text_line.height, self.pdf.page_break_trigger)
            if hasattr(self, "accept_page_break"):
                if self.pdf.y + text_line.height > self.pdf.page_break_trigger:
                    res = self.accept_page_break()
            new_page = self.pdf._render_styled_text_line(
                text_line,
                text_line.max_width,
                h=text_line.height,
                border=0,
                new_x=XPos.WCONT,
                new_y=YPos.TOP,
                align=Align.L if (align == Align.J and is_last_line) else align,
                fill=False,
                #                link=link,
            )
            page_break_triggered = page_break_triggered or new_page
        if text_line and text_line.trailing_nl:
            # The line renderer can't handle trailing newlines in the text.
            self.pdf._ln()
        return page_break_triggered

    def render(self, align=Align.L, print_sh: bool = False):
        if not self._text_fragments:
            return False
        align = Align.coerce(align)
        text_lines = self._build_lines(align, print_sh)
        if not text_lines:
            return False
        return self._render_lines(text_lines, align)

    def write(self, txt: str, link: str = ""):
        # XXX check if we're the current region?
        if not self.pdf.font_family:
            raise FPDFException("No font set, you need to call set_font() beforehand")
        normalized_string = self.pdf.normalize_text(txt).replace("\r", "")
        styled_text_fragments = self.pdf._preload_font_styles(normalized_string, False)
        self._text_fragments.extend(styled_text_fragments)

    def get_width(self, height):
        limits = self.current_x_extents(self.pdf.y, height)
        res = limits[1] - max(self.pdf.x, limits[0]) - 2 * self.pdf.c_margin
        return res


class TextColumnarMixin:
    """Enable a TextRegion to perform page breaks"""

    def __init__(self, pdf, l_margin=None, r_margin=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.l_margin = self.pdf.l_margin if l_margin is None else l_margin
        left = self.l_margin
        self.r_margin = self.pdf.r_margin if r_margin is None else r_margin
        right = self.pdf.w - self.r_margin
        self._set_left_right(left, right)

    def _set_left_right(self, left, right):
        self.left = self.pdf.l_margin if left is None else left
        self.right = (self.pdf.w - self.pdf.r_margin) if right is None else right
        if self.right <= self.left:
            raise FPDFException(
                f"{self.__class__.__name__}(): "
                f"Right limit ({self.right}) lower than left limit ({self.left})."
            )

    def current_x_extents(self, y, height):
        """Return the horizontal extents of the current line.
        Columnar regions simply return the boundaries of the column.
        Regions with non-vertical boundaries need to check how the largest
        font-height in the current line actually fits in there.
        For that reason we include the current y and the line height.
        """
        return self.left, self.right


class TextColumns(TextRegion, TextColumnarMixin):
    def __init__(self, pdf, ncols: int = 1, gap_width: float = 10, *args, **kwargs):
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
        for i in range(1, ncols):
            c_left += self.col_width + self.gap_width
            self.cols.append((c_left, c_left + self.col_width))

    def render(
        self,
        align: Align = Align.L,
        print_sh: bool = False,
        stay_below: bool = False,
        balance: bool = False,
    ):
        if not self._text_fragments:
            return False
        if stay_below or (self.cur_column == 0 and balance):
            self.cur_top = self.pdf.y
        else:
            self.cur_top = self.pdf.t_margin
        align = Align.coerce(align)
        text_lines = self._build_lines(align, print_sh)
        if not text_lines:
            return False
        if not balance:
            return self._render_lines(text_lines, align)
        # balance the columns.
        h_lines = sum([l.text_width for l in text_lines])
        bottom = self.pdf.h - self.pdf.b_margin
        h_avail = bottom - self.pdf.y
        h_avail += (self.ncols - self.cur_column - 1) * (bottom - self.cur_top)

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


class Paragraph(TextRegion):
    def __init__(self, pdf, align=None, *args, **kwargs):
        super().__init__(pdf, *args, **kwargs)
        self.align = align
 
