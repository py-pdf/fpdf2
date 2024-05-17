import math
from typing import NamedTuple, Sequence, List, NewType

from .errors import FPDFException
from .enums import Align, XPos, YPos, WrapMode
from .image_datastructures import VectorImageInfo
from .image_parsing import preload_image
from .line_break import MultiLineBreak, FORM_FEED

# Since Python doesn't have "friend classes"...
# pylint: disable=protected-access


class Extents(NamedTuple):
    left: float
    right: float


class TextRegionMixin:
    """Mix-in to be added to FPDF() in order to support text regions."""

    def __init__(self, *args, **kwargs):
        self.clear_text_region()
        super().__init__(*args, **kwargs)

    def register_text_region(self, region):
        self.__current_text_region = region

    def is_current_text_region(self, region):
        return self.__current_text_region == region

    def clear_text_region(self):
        self.__current_text_region = None


# forward declaration for LineWrapper.
Paragraph = NewType("Paragraph", None)


class LineWrapper(NamedTuple):
    """Connects each TextLine with the Paragraph it was written to.
    This allows to access paragraph specific attributes like
    top/bottom margins when rendering the line.
    """

    line: Sequence
    paragraph: Paragraph
    first_line: bool = False
    last_line: bool = False


class Paragraph:  # pylint: disable=function-redefined
    def __init__(
        self,
        region,
        text_align=None,
        line_height=None,
        top_margin: float = 0,
        bottom_margin: float = 0,
        skip_leading_spaces: bool = False,
        wrapmode: WrapMode = None,
    ):
        self._region = region
        self.pdf = region.pdf
        if text_align:
            text_align = Align.coerce(text_align)
            if text_align not in (Align.L, Align.C, Align.R, Align.J):
                raise ValueError(
                    f"Text_align must be 'LEFT', 'CENTER', 'RIGHT', or 'JUSTIFY', not '{text_align.value}'."
                )
        self.text_align = text_align
        if line_height is None:
            self.line_height = region.line_height
        else:
            self.line_height = line_height
        self.top_margin = top_margin
        self.bottom_margin = bottom_margin
        self.skip_leading_spaces = skip_leading_spaces
        if wrapmode is None:
            self.wrapmode = self._region.wrapmode
        else:
            self.wrapmode = WrapMode.coerce(wrapmode)
        self._text_fragments = []

    def __str__(self):
        return (
            f"Paragraph(text_align={self.text_align}, line_height={self.line_height}, top_margin={self.top_margin},"
            f" bottom_margin={self.bottom_margin}, skip_leading_spaces={self.skip_leading_spaces}, wrapmode={self.wrapmode},"
            f" #text_fragments={len(self._text_fragments)})"
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._region.end_paragraph()

    def write(self, text: str, link=None):
        if not self.pdf.font_family:
            raise FPDFException("No font set, you need to call set_font() beforehand")
        normalized_string = self.pdf.normalize_text(text).replace("\r", "")
        # YYY _preload_font_styles() should accept a "link" argument.
        fragments = self.pdf._preload_font_styles(normalized_string, markdown=False)
        if link:
            for frag in fragments:
                frag.link = link
        self._text_fragments.extend(fragments)

    def ln(self, h=None):
        if not self.pdf.font_family:
            raise FPDFException("No font set, you need to call set_font() beforehand")
        if h is None:
            h = self.pdf.font_size * self.line_height
        fragment = self.pdf._preload_font_styles("\n", markdown=False)[0]
        fragment.graphics_state["font_size_pt"] = h * fragment.k
        self._text_fragments.append(fragment)

    def build_lines(self, print_sh) -> List[LineWrapper]:
        text_lines = []
        multi_line_break = MultiLineBreak(
            self._text_fragments,
            max_width=self._region.get_width,
            margins=(self.pdf.c_margin, self.pdf.c_margin),
            align=self.text_align or self._region.text_align or Align.L,
            print_sh=print_sh,
            wrapmode=self.wrapmode,
            line_height=self.line_height,
            skip_leading_spaces=self.skip_leading_spaces
            or self._region.skip_leading_spaces,
        )
        self._text_fragments = []
        text_line = multi_line_break.get_line()
        first_line = True
        while (text_line) is not None:
            text_lines.append(LineWrapper(text_line, self, first_line=first_line))
            first_line = False
            text_line = multi_line_break.get_line()
        if text_lines:
            last = text_lines[-1]
            last = LineWrapper(
                last.line, self, first_line=last.first_line, last_line=True
            )
            text_lines[-1] = last
        return text_lines


class ImageParagraph:
    def __init__(
        self,
        region,
        name,
        align=None,
        width: float = None,
        height: float = None,
        fill_width: bool = False,
        keep_aspect_ratio=False,
        top_margin=0,
        bottom_margin=0,
        link=None,
        title=None,
        alt_text=None,
    ):
        self.region = region
        self.name = name
        if align:
            align = Align.coerce(align)
            if align not in (Align.L, Align.C, Align.R):
                raise ValueError(
                    f"Align must be 'LEFT', 'CENTER', or 'RIGHT', not '{align.value}'."
                )
        self.align = align
        self.width = width
        self.height = height
        self.fill_width = fill_width
        self.keep_aspect_ratio = keep_aspect_ratio
        self.top_margin = top_margin
        self.bottom_margin = bottom_margin
        self.link = link
        self.title = title
        self.alt_text = alt_text
        self.img = self.info = None

    def build_line(self):
        # We do double duty as a "text line wrapper" here, since all the necessary
        # information is already in the ImageParagraph object.
        self.name, self.img, self.info = preload_image(
            self.region.pdf.image_cache, self.name
        )
        return self

    def render(self, col_left, col_width, max_height):
        if not self.img:
            raise RuntimeError(
                "ImageParagraph.build_line() must be called before render()."
            )
        is_svg = isinstance(self.info, VectorImageInfo)

        # pylint: disable=possibly-used-before-assignment
        if self.height:
            h = self.height
        else:
            native_h = self.info["h"] / self.region.pdf.k
        if self.width:
            w = self.width
        else:
            native_w = self.info["w"] / self.region.pdf.k
            if native_w > col_width or self.fill_width:
                w = col_width
            else:
                w = native_w
        if not self.height:
            h = w * native_h / native_w
        if h > max_height:
            return None
        x = col_left
        if self.align:
            if self.align == Align.R:
                x += col_width - w
            elif self.align == Align.C:
                x += (col_width - w) / 2
        if is_svg:
            return self.region.pdf._vector_image(
                svg=self.img,
                info=self.info,
                x=x,
                y=None,
                w=w,
                h=h,
                link=self.link,
                title=self.title,
                alt_text=self.alt_text,
                keep_aspect_ratio=self.keep_aspect_ratio,
            )
        return self.region.pdf._raster_image(
            name=self.name,
            img=self.img,
            info=self.info,
            x=x,
            y=None,
            w=w,
            h=h,
            link=self.link,
            title=self.title,
            alt_text=self.alt_text,
            dims=None,
            keep_aspect_ratio=self.keep_aspect_ratio,
        )


class ParagraphCollectorMixin:
    def __init__(
        self,
        pdf,
        *args,
        text=None,
        text_align="LEFT",
        line_height: float = 1.0,
        print_sh: bool = False,
        skip_leading_spaces: bool = False,
        wrapmode: WrapMode = None,
        img=None,
        img_fill_width=False,
        **kwargs,
    ):
        self.pdf = pdf
        self.text_align = Align.coerce(text_align)  # default for auto paragraphs
        if self.text_align not in (Align.L, Align.C, Align.R, Align.J):
            raise ValueError(
                f"Text_align must be 'LEFT', 'CENTER', 'RIGHT', or 'JUSTIFY', not '{self.text_align.value}'."
            )
        self.line_height = line_height
        self.print_sh = print_sh
        self.wrapmode = WrapMode.coerce(wrapmode)
        self.skip_leading_spaces = skip_leading_spaces
        self._paragraphs = []
        self._active_paragraph = None
        super().__init__(pdf, *args, **kwargs)
        if text:
            self.write(text)
        if img:
            self.image(img, fill_width=img_fill_width)

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
            p = Paragraph(
                region=self,
                text_align=self.text_align,
                skip_leading_spaces=self.skip_leading_spaces,
            )
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
        text_align=None,
        line_height=None,
        skip_leading_spaces: bool = False,
        top_margin=0,
        bottom_margin=0,
        wrapmode: WrapMode = None,
    ):
        if self._active_paragraph == "EXPLICIT":
            raise FPDFException("Unable to nest paragraphs.")
        p = Paragraph(
            region=self,
            text_align=text_align or self.text_align,
            line_height=line_height,
            skip_leading_spaces=skip_leading_spaces or self.skip_leading_spaces,
            wrapmode=wrapmode,
            top_margin=top_margin,
            bottom_margin=bottom_margin,
        )
        self._paragraphs.append(p)
        self._active_paragraph = "EXPLICIT"
        return p

    def end_paragraph(self):
        if not self._active_paragraph:
            raise FPDFException("No active paragraph to end.")
        # self._paragraphs[-1].write("\n")
        self._active_paragraph = None

    def image(
        self,
        name,
        align=None,
        width: float = None,
        height: float = None,
        fill_width: bool = False,
        keep_aspect_ratio=False,
        top_margin=0,
        bottom_margin=0,
        link=None,
        title=None,
        alt_text=None,
    ):
        if self._active_paragraph == "EXPLICIT":
            raise FPDFException("Unable to nest paragraphs.")
        if self._active_paragraph:
            self.end_paragraph()
        p = ImageParagraph(
            self,
            name,
            align=align,
            width=width,
            height=height,
            fill_width=fill_width,
            keep_aspect_ratio=keep_aspect_ratio,
            top_margin=top_margin,
            bottom_margin=bottom_margin,
            link=link,
            title=title,
            alt_text=alt_text,
        )
        self._paragraphs.append(p)


class TextRegion(ParagraphCollectorMixin):
    """Abstract base class for all text region subclasses."""

    def current_x_extents(self, y, height):
        """
        Return the horizontal extents of the current line.
        Columnar regions simply return the boundaries of the column.
        Regions with non-vertical boundaries need to check how the largest
        font-height in the current line actually fits in there.
        For that reason we include the current y and the line height.
        """
        raise NotImplementedError()

    def _render_image_paragraph(self, paragraph):
        if paragraph.top_margin and self.pdf.y > self.pdf.t_margin:
            self.pdf.y += paragraph.top_margin
        col_left, col_right = self.current_x_extents(self.pdf.y, 0)
        bottom = self.pdf.h - self.pdf.b_margin
        max_height = bottom - self.pdf.y
        rendered = paragraph.render(col_left, col_right - col_left, max_height)
        if rendered:
            margin = paragraph.bottom_margin
            if margin and (self.pdf.y + margin) < bottom:
                self.pdf.y += margin
        return rendered

    def _render_column_lines(self, text_lines, top, bottom):
        if not text_lines:
            return 0  # no rendered height
        self.pdf.y = top
        prev_line_height = 0
        last_line_height = None
        rendered_lines = 0
        for tl_wrapper in text_lines:
            if isinstance(tl_wrapper, ImageParagraph):
                if self._render_image_paragraph(tl_wrapper):
                    rendered_lines += 1
                else:  # not enough room for image
                    break
            else:
                text_line = tl_wrapper.line
                text_rendered = False
                for frag in text_line.fragments:
                    if frag.characters:
                        text_rendered = True
                        break
                if (
                    text_rendered
                    and tl_wrapper.first_line
                    and tl_wrapper.paragraph.top_margin
                    and self.pdf.y > self.pdf.t_margin
                ):
                    self.pdf.y += tl_wrapper.paragraph.top_margin
                else:
                    if self.pdf.y + text_line.height > bottom:
                        last_line_height = prev_line_height
                        break
                prev_line_height = last_line_height
                last_line_height = text_line.height
                col_left, col_right = self.current_x_extents(self.pdf.y, 0)
                if self.pdf.x < col_left or self.pdf.x >= col_right:
                    self.pdf.x = col_left
                # Don't check the return, we never render past the bottom here.
                self.pdf._render_styled_text_line(
                    text_line,
                    h=text_line.height,
                    border=0,
                    new_x=XPos.LEFT,
                    new_y=YPos.NEXT,
                    fill=False,
                )
                if tl_wrapper.last_line:
                    margin = tl_wrapper.paragraph.bottom_margin
                    if margin and text_rendered and (self.pdf.y + margin) < bottom:
                        self.pdf.y += tl_wrapper.paragraph.bottom_margin
                rendered_lines += 1
                if text_line.trailing_form_feed:  # column break
                    break
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
            if isinstance(paragraph, ImageParagraph):
                line = paragraph.build_line()
                text_lines.append(line)
            else:
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
        res = end - start
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
        left = self.pdf.l_margin if left is None else left
        right = (self.pdf.w - self.pdf.r_margin) if right is None else right
        if right <= left:
            raise FPDFException(
                f"{self.__class__.__name__}(): "
                f"Right limit ({right}) lower than left limit ({left})."
            )
        self.extents = Extents(left, right)


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
        self._cur_column = 0
        self._ncols = ncols
        self.balance = balance
        total_w = self.extents.right - self.extents.left
        col_width = (total_w - (ncols - 1) * gutter) / ncols
        # We calculate the column extents once in advance, and store them for lookup.
        c_left = self.extents.left
        self._cols = [Extents(c_left, c_left + col_width)]
        for i in range(1, ncols):  # pylint: disable=unused-variable
            c_left += col_width + gutter
            self._cols.append(Extents(c_left, c_left + col_width))
        self._first_page_top = max(self.pdf.t_margin, self.pdf.y)

    def __enter__(self):
        super().__enter__()
        self._first_page_top = max(self.pdf.t_margin, self.pdf.y)
        if self.balance:
            self._cur_column = 0
            self.pdf.x = self._cols[self._cur_column].left
        return self

    def new_column(self):
        if self._paragraphs:
            self._paragraphs[-1].write(FORM_FEED)
        else:
            self.write(FORM_FEED)

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
            col_height = tot_height / self._ncols
            avail_height = bottom - top
            if col_height < avail_height:
                balancing = True  # We actually have room to balance on this page.
                # total height divided by n
                bottom = top + col_height
                # A bit more generous: Try to keep the rightmost column the shortest.
                lines_per_column = math.ceil(len(text_lines) / self._ncols) + 0.5
                mult_height = text_lines[0].line.height * lines_per_column
                if mult_height > col_height:
                    bottom = top + mult_height
                if bottom > page_bottom:
                    # Turns out we don't actually have enough room.
                    bottom = page_bottom
                    balancing = False
        for c in range(self._cur_column, self._ncols):
            if not text_lines:
                return
            if c != self._cur_column:
                self._cur_column = c
            col_left, col_right = self.current_x_extents(0, 0)
            if self.pdf.x < col_left or self.pdf.x >= col_right:
                self.pdf.x = col_left
            if balancing and c == (self._ncols - 1):
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
            self._cur_column = 0
            self._render_page_lines(text_lines, self.pdf.y, page_bottom)

    def current_x_extents(self, y, height):
        left, right = self._cols[self._cur_column]
        return left, right
