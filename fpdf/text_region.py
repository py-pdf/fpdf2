

from .errors import FPDFException
from .enums import Align, XPos, YPos
from .line_break import Fragment, DynamicMultiLineBreak, TextLine


class TextRegionMixin:
    """ Mixing for FPDF() to support text regions. """
    def __init__(self, *args, **kwargs):
        self.clear_text_region()
        super().__init__(*args, **kwargs)

    def register_text_region(self, region):
        self.__current_text_region = region

    def is_current_text_region(self, region):
        return self.__current_text_region == region

    def clear_text_region(self):
        self.__current_text_region = None




class TextRegion:

    col_wrapper = None

    def __init__(self, pdf, *args, **kwargs):
        self.pdf = pdf
        self._text_fragments = []
        self._added = []
        self._removed = []
        super().__init__(pdf, *args, **kwargs)

    def __enter__(self):
        if self.pdf.is_current_text_region(self):
            raise UserError(
                f"Unable to enter the same {self.__class__.__name__} context recursively.")
        self._page = self.pdf.page
        self.pdf._push_local_stack()
        self.pdf.page = 0
        self.pdf.register_text_region(self)

    def __exit__(self, exc_type, exc_value, traceback):
        self.pdf.clear_text_region()
        self.pdf.page = self._page
        self.pdf._pop_local_stack()

    def ln(self, h=None):
        self.pdf.ln(h)

    def render(self, align=Align.L, print_sh: bool = False):
        if not self._text_fragments:
            return
        align = Align.coerce(align)
        page_break_triggered = False
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
        if not text_lines:
            return False
        self.pdf.y = max(self.pdf.y, self.pdf.t_margin)
        for text_line_index, text_line in enumerate(text_lines):
            is_last_line = text_line_index == len(text_lines) -1
            if text_line_index != 0:
                self.ln()
            #print(self.pdf.y + text_line.height, self.pdf.page_break_trigger)
            if hasattr(self, "accept_page_break"):
                if self.pdf.y + text_line.height > self.pdf.page_break_trigger:
                    res = self.accept_page_break()
            new_page = self.pdf._render_styled_text_line(
                text_line,
                text_line.text_width,
                h=text_line.height,
                border=0,
                new_x=XPos.WCONT,
                new_y=YPos.TOP,
                align=Align.L if (align == Align.J and is_last_line) else align,
                fill=False,
#                link=link,
            )
            page_break_triggered = page_break_triggered or new_page
        if text_line.trailing_nl:
            # The line renderer can't handle trailing newlines in the text.
            self.pdf.ln()
        return page_break_triggered


    def write(self, txt: str, link: str = ""):
        # XXX check if we're the current region?
        if not self.pdf.font_family:
            raise FPDFException("No font set, you need to call set_font() beforehand")
        normalized_string = self.pdf.normalize_text(txt).replace("\r", "")
        styled_text_fragments = self.pdf._preload_font_styles(normalized_string, False)
        self._text_fragments.extend(styled_text_fragments)

    def get_width(self, height):
        limits = self.current_x_extents(self.pdf.y, height)
        return limits[1] - max(self.pdf.x, limits[0]) - 2 * self.pdf.c_margin


class TextColumnarMixin:
    """Enable a TextRegion to perform page breaks"""

    def __init__(self, pdf, left=None, right=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        '''Return the horizontal extents of the current line.
        Columnar regions simply return the boundaries of the column.
        Regions with non-vertical boundaries need to check how the largest
        font-height in the current line actually fits in there.
        For that reason we include the current y and the line height.
        '''
        return self.left, self.right


class TextColumns(TextRegion, TextColumnarMixin):

    def __init__(self, pdf, ncols: int = 1, gap_width: float = 10, *args, **kwargs):
        super().__init__(pdf, *args, **kwargs)
        self.cur_column = 0
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

    def accept_page_break(self):
        if self.cur_column == self.ncols - 1:
            self.cur_column = 0
            self.pdf.x = self.cols[self.cur_column][0]
            return True
        self.cur_column += 1
        self.pdf.x = self.cols[self.cur_column][0]
        self.pdf.y = self.pdf.t_margin
        return False

    def ln(self, h=None):
        self.pdf.x = self.cols[self.cur_column][0]
        self.pdf.y  += self.pdf.lasth if h is None else h

    def current_x_extents(self, y, height):
        left = self.cols[self.cur_column][0]
        right = self.cols[self.cur_column][1]
        return left, right





