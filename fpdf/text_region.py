import math
from typing import NamedTuple, Any, Optional, Union, Sequence

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
    def __init__(
            self,
            region,
            align=None,
            line_height=None,
            top_margin: float = 0,
            bottom_margin: float = 0,
            skip_leading_spaces: bool = False,
            ):
        print("New Paragraph")
        self.region = region
        self.pdf = region.pdf
        if align:
            align = Align.coerce(align)
        self.align = align
        if line_height is None:
            self.line_height = region.line_height
        else:
            self.line_height = line_height
        self.top_margin = top_margin
        self.bottom_margin = bottom_margin
        self.skip_leading_spaces = skip_leading_spaces
        self._text_fragments = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.region.end_paragraph()

    def write(self, text: str, link=None):  # pylint: disable=unused-argument
        if not self.pdf.font_family:
            raise FPDFException("No font set, you need to call set_font() beforehand")
        normalized_string = self.pdf.normalize_text(text).replace("\r", "")
        # YYY _preload_font_styles() should accept a "link" argument.
        fragments = self.pdf._preload_font_styles(normalized_string, False)
        for frag in fragments:
            print("write:", frag.font.fontkey, f'"{text}"')
        self._text_fragments.extend(fragments)

    def ln(self, h=None):
        if not self.pdf.font_family:
            raise FPDFException("No font set, you need to call set_font() beforehand")
        if h is None:
            h = self.pdf.font_size * self.line_height
        fragment = self.pdf._preload_font_styles("\n", False)[0]
        fragment.graphics_state["font_size_pt"] = h * fragment.k
        self._text_fragments.append(fragment)

    def build_lines(self, print_sh):
        text_lines = []
        multi_line_break = MultiLineBreak(
            self._text_fragments,
            max_width=self.region.get_width,
            align=self.align or self.region.align or Align.L,
            print_sh=print_sh,
            # wrapmode=self.wrapmode,
            line_height=self.line_height,
            skip_leading_spaces=self.skip_leading_spaces or self.region.skip_leading_spaces,
        )
        self._text_fragments = []
        text_line = multi_line_break.get_line()
        first_line = True
        while (text_line) is not None:
            text_lines.append(LWrapper(text_line, self, first_line=first_line))
            first_line = False
            text_line = multi_line_break.get_line()
        if text_lines:
            last = text_lines[-1]
            last = LWrapper(last.line, self, first_line=last.first_line, last_line=True)
            text_lines[-1] = last
        return text_lines


class ParagraphCollectorMixin:
    def __init__(
        self,
        pdf,
        *args,
        text=None,
        align="LEFT",
        line_height: float = 1.0,
        print_sh: bool = False,
        skip_leading_spaces: bool = False,
        **kwargs,
    ):
        self.pdf = pdf
        self.align = Align.coerce(align)  # default for auto paragraphs
        self.line_height = line_height
        self.print_sh = print_sh
        self.skip_leading_spaces = skip_leading_spaces
        self._paragraphs = []
        self._active_paragraph = None
        super().__init__(pdf, *args, **kwargs)
        if text:
            self.write(text)

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

    def _check_paragraph(self):
        if self._active_paragraph == "EXPLICIT":
            raise FPDFException(
                "Conflicts with active paragraph. Either close the current paragraph or write your text inside it."
            )
        if self._active_paragraph is None:
            p = Paragraph(region=self, align=self.align, skip_leading_spaces=self.skip_leading_spaces)
            self._paragraphs.append(p)
            self._active_paragraph = "AUTO"

    def write(self, text: str, link=None):  # pylint: disable=unused-argument
        self._check_paragraph()
        self._paragraphs[-1].write(text)

    def ln(self, h=None):
        self._check_paragraph()
        self._paragraphs[-1].ln(h)

    def paragraph(
            self,
            align=None,
            line_height=None,
            skip_leading_spaces: bool = False,
            top_margin=0,
            bottom_margin=0,
            ):
        if self._active_paragraph == "EXPLICIT":
            raise FPDFException("Unable to nest paragraphs.")
        p = Paragraph(
                region=self,
                align=align or self.align,
                line_height=line_height,
                skip_leading_spaces=skip_leading_spaces or self.skip_leading_spaces,
                top_margin=top_margin,
                bottom_margin=bottom_margin,
               )
        self._paragraphs.append(p)
        self._active_paragraph = "EXPLICIT"
        return p

    def end_paragraph(self):
        print("Ending Paragraph")
        if not self._active_paragraph:
            raise FPDFException("No active paragraph to end.")
        #self._paragraphs[-1].write("\n")
        self._active_paragraph = None


class TextRegion(ParagraphCollectorMixin):
    """Abstract base class for all text region subclasses."""

    def _do_ln(self, h=None):
        self.pdf.ln(h)

    def current_x_extents(
        self, y, height
    ):  # xpylint: disable=no-self-use,unused-argument
        """Return the horizontal extents of the current line."""
        raise NotImplementedError()

    def _render_column_lines(
        self, text_lines, top, bottom
    ):  # xpylint: disable=undefined-loop-variable
        if not text_lines:
            return 0  # no rendered height
        self.pdf.y = top
        prev_line_height = 0
        last_line_height = None
        rendered_lines = 0
        for tl_wrapper in text_lines:
            text_line = tl_wrapper.line
#            print("Top-Margin:", tl_wrapper.paragraph.top_margin, tl_wrapper.first_line,
#                    list(frag.string for frag in text_line.fragments))
            text_rendered = False
            for i, frag in enumerate(text_line.fragments):
                print("render Fragment:", frag.font.fontkey, i, f'"{frag.string}"')
                if frag.characters:
                    text_rendered = True
                    break
            print(f"Tr:{text_rendered} fl:{tl_wrapper.first_line} tm:{tl_wrapper.paragraph.top_margin}")
            if (text_rendered and tl_wrapper.first_line
                    and tl_wrapper.paragraph.top_margin
                    #and self.pdf.y > self.pdf.t_margin
                    ):
                print(f"top-margin moving y by {tl_wrapper.paragraph.top_margin}")
                self.pdf.y += tl_wrapper.paragraph.top_margin
            if self.pdf.y + text_line.height > bottom:
                last_line_height = prev_line_height
                break
            prev_line_height = last_line_height
            last_line_height = text_line.height
            extents = self.current_x_extents(self.pdf.y, 0)
            self.pdf.x = extents[0]
            # Don't check the return, we never render past the bottom here.
            self.pdf._render_styled_text_line(
                text_line,
                w=text_line.max_width + 2 * self.pdf.c_margin,
                h=text_line.height,
                border=0,
                new_x=XPos.LEFT,
                new_y=YPos.NEXT,
                fill=False,
                # link=link,  # Must be part of Fragment
            )
            if tl_wrapper.last_line:
                margin = tl_wrapper.paragraph.bottom_margin
                if (text_rendered and (self.pdf.y + margin) < bottom):
                    print(f"bottom-margin moving y by {margin}")
                    self.pdf.y += tl_wrapper.paragraph.bottom_margin
            rendered_lines += 1
        if rendered_lines:
            del text_lines[:rendered_lines]
        return last_line_height

    def _render_lines(self, text_lines, top, bottom):
        """Default page rendering a set of lines in one column"""
        if text_lines:
            self._render_column_lines(text_lines, top, bottom)

    def collect_lines(self):
        text_lines = []
        for paragraph in self._paragraphs:
            cur_lines = paragraph.build_lines(self.print_sh)
            if not cur_lines:
                continue
            text_lines.extend(cur_lines)
        return text_lines

    def render(self):
        raise NotImplementedError()

    def get_width(self, height):
        start, end = self.current_x_extents(self.pdf.y, height)
        if self.pdf.x > start and self.pdf.x < end:
            start = self.pdf.x
        res = end - start - 2 * self.pdf.c_margin
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
    def __init__(
        self,
        pdf,
        *args,
        ncols: int = 1,
        gutter: float = 10,
        balance: bool = False,
        **kwargs,
    ):
        super().__init__(pdf, *args, **kwargs)
        self.cur_column = 0
        self.ncols = ncols
        self.gutter = gutter
        self.balance = balance
        total_w = self.right - self.left
        self.col_width = (total_w - (self.ncols - 1) * self.gutter) / self.ncols
        # We calculate the column extents once in advance, and store them for lookup.
        c_left = self.left
        self.cols = [(c_left, c_left + self.col_width)]
        for i in range(1, ncols):  # pylint: disable=unused-variable
            c_left += self.col_width + self.gutter
            self.cols.append((c_left, c_left + self.col_width))
        self._first_page_top = max(self.pdf.t_margin, self.pdf.y)

    def __enter__(self):
        super().__enter__()
        self._first_page_top = max(self.pdf.t_margin, self.pdf.y)
        if self.balance:
            self.cur_column = 0
            self.pdf.x = self.cols[self.cur_column][0]
        return self

    def _render_page_lines(self, text_lines, top, bottom):
        """Rendering a set of lines in one or several columns on one page."""
        balancing = False
        next_y = self.pdf.y
        if self.balance:
            # Column balancing is currently very simplistic, and only works reliably when
            # line height doesn't change much within the text block.
            # The "correct" solution would require an exact precalculation of the hight of
            # each column with the specific line heights and iterative regrouping of lines,
            # which seems excessive at this point.
            # Contribution of a more reliable but still reasonably simple algorithm welcome.
            page_bottom = bottom
            if not text_lines:
                return
            tot_height = sum(l.line.height for l in text_lines)
            col_height = tot_height / self.ncols
            avail_height = bottom - top
            if col_height < avail_height:
                balancing = True  # We actually have room to balance on this page.
                # total height divided by n
                bottom = top + col_height
                # A bit more generous: Try to keep the rightmost column the shortest.
                lines_per_column = math.ceil(len(text_lines) / self.ncols) + 0.5
                mult_height = text_lines[0].line.height * lines_per_column
                if mult_height > col_height:
                    bottom = top + mult_height
                if bottom > page_bottom:
                    # Turns out we don't actually have enough room.
                    bottom = page_bottom
                    balancing = False
        for c in range(self.cur_column, self.ncols):
            if not text_lines:
                return
            if c != self.cur_column:
                self.cur_column = c
            col_left, col_right = self.current_x_extents(0, 0)
            if self.pdf.x < col_left or self.pdf.x >= col_right:
                self.pdf.x = col_left
            if balancing and c == (self.ncols - 1):
                # Give the last column more space in case the balancing is out of whack.
                bottom = self.pdf.h - self.pdf.b_margin
            last_line_height = self._render_column_lines(text_lines, top, bottom)
            if balancing:
                new_y = self.pdf.y + last_line_height
                if new_y > next_y:
                    next_y = new_y
        if balancing:
            self.pdf.y = next_y

    def render(self):
        if not self._paragraphs:
            return
        text_lines = self.collect_lines()
        if not text_lines:
            return
        page_bottom = self.pdf.h - self.pdf.b_margin
        _first_page_top = max(self.pdf.t_margin, self.pdf.y)
        self._render_page_lines(text_lines, _first_page_top, page_bottom)
        while text_lines:
            self.pdf.add_page(same=True)
            self.cur_column = 0
            self._render_page_lines(text_lines, self.pdf.y, page_bottom)

    def _do_ln(self, h=None):
        self.pdf.ln(h=h)
        self.pdf.x = self.cols[self.cur_column][0]

    def current_x_extents(self, y, height):
        left = self.cols[self.cur_column][0]
        right = self.cols[self.cur_column][1]
        return left, right


class LWrapper(NamedTuple):
    """Connects each TextLine with the Paragraph it was written to.
        This allows to access paragraph specific attributes like
        top/bottom margins when rendering the line.
    """
    line: Sequence
    paragraph: Paragraph
    first_line: bool = False
    last_line: bool = False