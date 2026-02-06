"""
Usage documentation at: <https://py-pdf.github.io/fpdf2/TextRegion.html>
"""

import math
from abc import ABC, abstractmethod
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    NamedTuple,
    Optional,
    Sequence,
    Type,
    Union,
    cast,
)

from .enums import Align, WrapMode, XPos, YPos
from .errors import FPDFException
from .image_datastructures import (
    is_vector_image_info,
    RasterImageInfo,
    VectorImageInfo,
)
from .image_parsing import preload_image
from .line_break import FORM_FEED, MultiLineBreak
from .util import get_scale_factor

if TYPE_CHECKING:
    from .fpdf import FPDF
    from .line_break import Fragment, TextLine
    from .svg import SVGObject
    from .util import ImageData

# Since Python doesn't have "friend classes"...
# pylint: disable=protected-access


class Extents(NamedTuple):
    left: float
    right: float


class TextRegionMixin(ABC):
    """Mix-in to be added to FPDF() in order to support text regions."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.__current_text_region: Optional["TextRegion"] = None
        self.clear_text_region()
        super().__init__(*args, **kwargs)

    def register_text_region(
        self, region: Union["TextRegion", "ParagraphCollectorMixin"]
    ) -> None:
        self.__current_text_region = cast("TextRegion", region)

    def is_current_text_region(
        self, region: Union["TextRegion", "ParagraphCollectorMixin"]
    ) -> bool:
        return self.__current_text_region == region

    def clear_text_region(self) -> None:
        self.__current_text_region = None


class LineWrapper(NamedTuple):
    """Connects each TextLine with the Paragraph it was written to.
    This allows to access paragraph specific attributes like
    top/bottom margins when rendering the line.
    """

    line: "TextLine"
    paragraph: "Paragraph"
    first_line: bool = False
    last_line: bool = False


class Bullet:
    def __init__(
        self,
        bullet_fragments: Sequence["Fragment"],
        text_line: Optional["TextLine"],
        bullet_r_margin: float,
    ) -> None:
        self.fragments: Sequence["Fragment"] = bullet_fragments
        self.text_line = text_line
        self.r_margin = bullet_r_margin
        self.rendered_flag: bool = False

    def get_fragments_width(self) -> float:
        fragments_width: float = 0
        for frag in self.fragments:
            fragments_width += frag.get_width()
        return fragments_width


class Paragraph:
    def __init__(
        self,
        region: Union["TextRegion", "ParagraphCollectorMixin"],
        text_align: Optional[str | Align] = None,
        line_height: Optional[float] = None,
        top_margin: float = 0,
        bottom_margin: float = 0,
        indent: float = 0,
        bullet_r_margin: Optional[float] = None,
        bullet_string: str = "",
        skip_leading_spaces: bool = False,
        wrapmode: Optional[WrapMode] = None,
        first_line_indent: float = 0,
    ):
        self._region = region
        self.pdf: "FPDF" = region.pdf
        self.text_align: Optional[Align] = None
        if text_align:
            text_align_conv: Align = Align.coerce(text_align)
            if text_align_conv not in (Align.L, Align.C, Align.R, Align.J):
                raise ValueError(
                    f"Text_align must be 'LEFT', 'CENTER', 'RIGHT', or 'JUSTIFY', not '{text_align_conv.value}'."
                )
            self.text_align = text_align_conv
        if line_height is None:
            self.line_height = region.line_height
        else:
            self.line_height = line_height
        self.top_margin = top_margin
        self.bottom_margin = bottom_margin
        self.indent = indent
        self.skip_leading_spaces = skip_leading_spaces
        if wrapmode is None:
            self.wrapmode = self._region.wrapmode
        else:
            self.wrapmode = WrapMode.coerce(wrapmode)
        self._text_fragments: list["Fragment"] = []
        if bullet_r_margin is None:
            # Default value of 2 to be multiplied by the conversion factor
            # for bullet_r_margin is given in mm
            bullet_r_margin = 2 * get_scale_factor("mm") / self.pdf.k
        if bullet_string:
            bullet_frags_and_tl = self.generate_bullet_frags_and_tl(
                bullet_string, bullet_r_margin
            )
            assert isinstance(bullet_frags_and_tl, tuple)
            self.bullet: Optional[Bullet] = Bullet(
                bullet_frags_and_tl[0], bullet_frags_and_tl[1], bullet_r_margin
            )
        else:
            self.bullet = None
        self.first_line_indent = first_line_indent

    def __str__(self) -> str:
        return (
            f"Paragraph(text_align={self.text_align}, line_height={self.line_height}, top_margin={self.top_margin},"
            f" bottom_margin={self.bottom_margin}, skip_leading_spaces={self.skip_leading_spaces}, wrapmode={self.wrapmode},"
            f" #text_fragments={len(self._text_fragments)})"
        )

    def __enter__(self) -> "Paragraph":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self._region.end_paragraph()

    def write(self, text: str, link: Optional[str | int] = None) -> None:
        if not self.pdf.font_family:
            raise FPDFException("No font set, you need to call set_font() beforehand")
        normalized_string = self.pdf.normalize_text(text).replace("\r", "")
        # YYY _preload_font_styles() should accept a "link" argument.
        fragments = (
            self.pdf._preload_font_styles(  # pyright: ignore[reportPrivateUsage]
                normalized_string, markdown=False
            )
        )
        if link:
            for frag in fragments:
                frag.link = link
        self._text_fragments.extend(fragments)

    def generate_bullet_frags_and_tl(
        self, bullet_string: str, bullet_r_margin: float
    ) -> Optional[tuple[Sequence["Fragment"], Optional["TextLine"]]]:
        if not bullet_string:
            return None
        bullet_string = self.pdf.normalize_text(bullet_string)
        if not self.pdf.font_family:
            raise FPDFException("No font set, you need to call set_font() beforehand")
        bullet_fragments = (
            self.pdf._preload_font_styles(  # pyright: ignore[reportPrivateUsage]
                bullet_string, markdown=False
            )
        )
        fragments_width: float = 0
        for frag in bullet_fragments:
            fragments_width += frag.get_width()
        bullet_line_break = MultiLineBreak(
            bullet_fragments,
            max_width=self._region.get_width,
            margins=(
                self.pdf.c_margin + (self.indent - fragments_width - bullet_r_margin),
                self.pdf.c_margin,
            ),
            align=self.text_align or self._region.text_align or Align.L,
            wrapmode=self.wrapmode,
            line_height=self.line_height,
            skip_leading_spaces=self.skip_leading_spaces
            or self._region.skip_leading_spaces,
        )
        bullet_text_line = bullet_line_break.get_line()
        return bullet_fragments, bullet_text_line

    def ln(self, h: Optional[float] = None) -> None:
        if not self.pdf.font_family:
            raise FPDFException("No font set, you need to call set_font() beforehand")
        if h is None:
            h = self.pdf.font_size * self.line_height
        fragment = self.pdf._preload_font_styles(  # pyright: ignore[reportPrivateUsage]
            "\n", markdown=False
        )[  # pyright: ignore[reportPrivateUsage]
            0
        ]
        fragment.graphics_state.font_size_pt = h * fragment.k
        self._text_fragments.append(fragment)

    def build_lines(self, print_sh: bool) -> list[LineWrapper]:
        text_lines: list[LineWrapper] = []
        multi_line_break = MultiLineBreak(
            self._text_fragments,
            max_width=self._region.get_width,
            margins=(self.pdf.c_margin + self.indent, self.pdf.c_margin),
            first_line_indent=self.first_line_indent,
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
        while text_line is not None:
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
        region: Union["TextRegion", "ParagraphCollectorMixin"],
        name: str,
        align: Optional[str | Align] = None,
        width: Optional[float] = None,
        height: Optional[float] = None,
        fill_width: bool = False,
        keep_aspect_ratio: bool = False,
        top_margin: float = 0,
        bottom_margin: float = 0,
        link: Optional[str | int] = None,
        title: Optional[str] = None,
        alt_text: Optional[str] = None,
    ) -> None:
        self.region = region
        self.name = name
        self.align: Optional[Align] = None
        if align:
            align_conv = Align.coerce(align)
            if align_conv not in (Align.L, Align.C, Align.R):
                raise ValueError(
                    f"Align must be 'LEFT', 'CENTER', or 'RIGHT', not '{align_conv.value}'."
                )
            self.align = align_conv
        self.width = width
        self.height = height
        self.fill_width = fill_width
        self.keep_aspect_ratio = keep_aspect_ratio
        self.top_margin = top_margin
        self.bottom_margin = bottom_margin
        self.link = link
        self.title = title
        self.alt_text = alt_text
        self.img: Optional[ImageData] = None
        self.info: Optional[RasterImageInfo | VectorImageInfo] = None
        self.line: ImageParagraph = self

    def build_line(self) -> "ImageParagraph":
        # We do double duty as a "text line wrapper" here, since all the necessary
        # information is already in the ImageParagraph object.
        self.name, self.img, self.info = preload_image(
            self.region.pdf.image_cache, self.name
        )
        return self

    def render(
        self, col_left: float, col_width: float, max_height: float
    ) -> Optional[RasterImageInfo | VectorImageInfo]:
        if self.info is None:
            raise RuntimeError(
                "ImageParagraph.build_line() must be called before render()."
            )
        is_svg = is_vector_image_info(self.info)
        native_h = h = float(0)
        if self.height:
            h = self.height
        else:
            native_h = self.info["h"] / self.region.pdf.k
        if self.width:
            w = self.width
        else:
            native_w: float = self.info["w"] / self.region.pdf.k
            if native_w > col_width or self.fill_width:
                w = col_width
            else:
                w = native_w
        if not self.height:
            h = (
                w
                * native_h
                / native_w  # pyright: ignore[reportPossiblyUnboundVariable]
            )
        if h > max_height:
            return None
        x = col_left
        if self.align:
            if self.align == Align.R:
                x += col_width - w
            elif self.align == Align.C:
                x += (col_width - w) / 2
        return_info: VectorImageInfo | RasterImageInfo
        if is_svg:
            return_info = (
                self.region.pdf._vector_image(  # pyright: ignore[reportPrivateUsage]
                    name=self.name,
                    svg=cast("SVGObject", self.img),
                    info=cast(VectorImageInfo, self.info),
                    x=x,
                    y=None,
                    w=w,
                    h=h,
                    link=self.link,
                    title=self.title,
                    alt_text=self.alt_text,
                    keep_aspect_ratio=self.keep_aspect_ratio,
                )
            )
            return return_info
        if TYPE_CHECKING:
            assert not isinstance(self.img, SVGObject) and self.img is not None
        return_info = (
            self.region.pdf._raster_image(  # pyright: ignore[reportPrivateUsage]
                name=self.name,
                img=self.img,
                info=cast(RasterImageInfo, self.info),
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
        )
        return return_info


class ParagraphCollectorMixin(ABC):
    def __init__(
        self,
        pdf: "FPDF",
        *args: Any,
        text: Optional[str] = None,
        text_align: str | Align = "LEFT",
        line_height: float = 1.0,
        print_sh: bool = False,
        skip_leading_spaces: bool = False,
        wrapmode: Optional[WrapMode] = None,
        img: Optional[str] = None,
        img_fill_width: bool = False,
        **kwargs: Any,
    ) -> None:
        self.pdf = pdf
        self.text_align = Align.coerce(text_align)  # default for auto paragraphs
        if self.text_align not in (Align.L, Align.C, Align.R, Align.J):
            raise ValueError(
                f"Text_align must be 'LEFT', 'CENTER', 'RIGHT', or 'JUSTIFY', not '{self.text_align.value}'."
            )
        self.line_height = line_height
        self.print_sh = print_sh
        self.wrapmode = (
            WrapMode.coerce(wrapmode) if wrapmode is not None else WrapMode.CHAR
        )
        self.skip_leading_spaces = skip_leading_spaces
        self._paragraphs: list[Paragraph | ImageParagraph] = []
        self._active_paragraph: Optional[str] = None
        super().__init__(pdf, *args, **kwargs)  # type: ignore[call-arg]
        if text:
            self.write(text)
        if img:
            self.image(img, fill_width=img_fill_width)

    def __enter__(self) -> "ParagraphCollectorMixin":
        if self.pdf.is_current_text_region(self):
            raise FPDFException(
                f"Unable to enter the same {self.__class__.__name__} context recursively."
            )
        self._page = self.pdf.page
        self.pdf._push_local_stack()  # pyright: ignore[reportPrivateUsage]
        self.pdf.page = 0
        self.pdf.register_text_region(self)
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.pdf.clear_text_region()
        self.pdf.page = self._page
        self.pdf._pop_local_stack()  # pyright: ignore[reportPrivateUsage]
        self.render()

    def _check_paragraph(self) -> None:
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

    def write(
        self,
        text: str,
        link: Optional[str | int] = None,  # pylint: disable=unused-argument
    ) -> None:
        self._check_paragraph()
        if isinstance(self._paragraphs[-1], Paragraph):
            self._paragraphs[-1].write(text)

    def ln(self, h: Optional[float] = None) -> None:
        self._check_paragraph()
        if isinstance(self._paragraphs[-1], Paragraph):
            self._paragraphs[-1].ln(h)

    def paragraph(
        self,
        text_align: Optional[Align] = None,
        line_height: Optional[float] = None,
        skip_leading_spaces: bool = False,
        top_margin: Optional[float] = 0,
        bottom_margin: Optional[float] = 0,
        indent: Optional[float] = 0,
        bullet_string: Optional[str] = "",
        bullet_r_margin: Optional[float] = None,
        wrapmode: Optional[WrapMode] = None,
        first_line_indent: Optional[float] = 0,
    ) -> Paragraph:
        """
        Args:
            text_align (Align, optional): the horizontal alignment of the paragraph.
            line_height (float, optional): factor by which the line spacing will be different from the font height. (Default: by region)
            top_margin (float, optional):  how much spacing is added above the paragraph.
                No spacing will be added at the top of the paragraph if the current y position is at (or above) the
                top margin of the page. (Default: 0.0)
            bottom_margin (float, optional): those two values determine how much spacing is added below the paragraph.
                No spacing will be added at the bottom if it would result in overstepping the bottom margin of the page. (Default: 0.0)
            indent (float, optional): determines the indentation of the paragraph. (Default: 0.0)
            bullet_string (str, optional): determines the fragments and text lines of the bullet. (Default: "")
            bullet_r_margin (float, optional): determines the spacing between the bullet and the bulleted line
            skip_leading_spaces (float, optional): removes all space characters at the beginning of each line. (Default: False)
            wrapmode (WrapMode): determines the way text wrapping is handled. (Default: None)
            first_line_indent (float, optional): left spacing before first line of text in paragraph.
        """
        if self._active_paragraph == "EXPLICIT":
            raise FPDFException("Unable to nest paragraphs.")
        p = Paragraph(
            region=self,
            text_align=text_align or self.text_align,
            line_height=line_height,
            skip_leading_spaces=skip_leading_spaces or self.skip_leading_spaces,
            wrapmode=wrapmode,
            top_margin=top_margin or 0,
            bottom_margin=bottom_margin or 0,
            indent=indent or 0,
            first_line_indent=first_line_indent or 0,
            bullet_string=bullet_string or "",
            bullet_r_margin=bullet_r_margin,
        )
        self._paragraphs.append(p)
        self._active_paragraph = "EXPLICIT"
        return p

    def end_paragraph(self) -> None:
        if not self._active_paragraph:
            raise FPDFException("No active paragraph to end.")
        # self._paragraphs[-1].write("\n")
        self._active_paragraph = None

    def image(
        self,
        name: str,
        align: Optional[str | Align] = None,
        width: Optional[float] = None,
        height: Optional[float] = None,
        fill_width: bool = False,
        keep_aspect_ratio: bool = False,
        top_margin: float = 0,
        bottom_margin: float = 0,
        link: Optional[str | int] = None,
        title: Optional[str] = None,
        alt_text: Optional[str] = None,
    ) -> None:
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

    @abstractmethod
    def render(self) -> None: ...

    @abstractmethod
    def get_width(self, height: float) -> float: ...


class TextRegion(ParagraphCollectorMixin):
    """Abstract base class for all text region subclasses."""

    def current_x_extents(self, y: float, height: float) -> tuple[float, float]:
        """
        Return the horizontal extents of the current line.
        Columnar regions simply return the boundaries of the column.
        Regions with non-vertical boundaries need to check how the largest
        font-height in the current line actually fits in there.
        For that reason we include the current y and the line height.
        """
        raise NotImplementedError()

    def _render_image_paragraph(
        self, paragraph: ImageParagraph
    ) -> Optional[RasterImageInfo | VectorImageInfo]:
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

    def _render_column_lines(
        self,
        text_lines: list[ImageParagraph | LineWrapper],
        top: float,
        bottom: float,
    ) -> float:
        if not text_lines:
            return 0  # no rendered height
        self.pdf.y = top
        prev_line_height: float = 0
        last_line_height: Optional[float] = None
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
                cur_paragraph = tl_wrapper.paragraph
                cur_bullet = cur_paragraph.bullet
                for frag in text_line.fragments:
                    if frag.characters:
                        text_rendered = True
                        break
                if (
                    text_rendered
                    and tl_wrapper.first_line
                    and not cur_bullet
                    and cur_paragraph.top_margin
                    # Do not render margin on top of page:
                    and self.pdf.y > self.pdf.t_margin
                ):
                    self.pdf.y += cur_paragraph.top_margin
                if self.pdf.y + text_line.height > bottom:
                    # => page break
                    last_line_height = prev_line_height
                    break
                prev_line_height = last_line_height or 0
                last_line_height = text_line.height
                col_left, col_right = self.current_x_extents(self.pdf.y, 0)
                if self.pdf.x < col_left or self.pdf.x >= col_right:
                    self.pdf.x = col_left
                self.pdf.x += cur_paragraph.indent
                if cur_bullet and not cur_bullet.rendered_flag:
                    bullet_indent_shift = (
                        cur_bullet.get_fragments_width() + cur_bullet.r_margin
                    )
                    self.pdf.x -= bullet_indent_shift
                    assert cur_bullet.text_line is not None
                    self.pdf._render_styled_text_line(  # pyright: ignore[reportPrivateUsage]
                        cur_bullet.text_line,
                        h=cur_bullet.text_line.height,
                        border=0,
                        new_x=XPos.LEFT,
                        new_y=YPos.TOP,
                        fill=False,
                    )
                    cur_bullet.rendered_flag = True
                    self.pdf.x += bullet_indent_shift
                # Don't check the return, we never render past the bottom here.
                self.pdf.x += text_line.indent
                self.pdf._render_styled_text_line(  # pyright: ignore[reportPrivateUsage]
                    text_line,
                    h=text_line.height,
                    border=0,
                    new_x=XPos.LEFT,
                    new_y=YPos.NEXT,
                    fill=False,
                )
                self.pdf.x -= text_line.indent
                self.pdf.x -= cur_paragraph.indent
                if tl_wrapper.last_line:
                    margin = cur_paragraph.bottom_margin
                    if margin and text_rendered and (self.pdf.y + margin) < bottom:
                        self.pdf.y += cur_paragraph.bottom_margin
                rendered_lines += 1
                if text_line.trailing_form_feed:  # column break
                    break
        if rendered_lines:
            del text_lines[:rendered_lines]
        return last_line_height or 0

    def collect_lines(self) -> list[ImageParagraph | LineWrapper]:
        text_lines: list[ImageParagraph | LineWrapper] = []
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

    def render(self) -> None:
        raise NotImplementedError()

    def get_width(self, height: float) -> float:
        start, end = self.current_x_extents(self.pdf.y, height)
        if self.pdf.x > start and self.pdf.x < end:
            start = self.pdf.x
        res = end - start
        return res


class TextColumnarMixin(ABC):
    """Enable a TextRegion to perform page breaks"""

    pdf: "FPDF"

    def __init__(
        self,
        pdf: "FPDF",
        *args: Any,
        l_margin: Optional[float] = None,
        r_margin: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.l_margin = pdf.l_margin if l_margin is None else l_margin
        left = self.l_margin
        self.r_margin = pdf.r_margin if r_margin is None else r_margin
        right = pdf.w - self.r_margin
        self._set_left_right(left, right)

    def _set_left_right(self, left: Optional[float], right: Optional[float]) -> None:
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
        pdf: "FPDF",
        *args: Any,
        ncols: int = 1,
        gutter: float = 10,
        balance: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(pdf, *args, **kwargs)
        self._cur_column = 0
        self._ncols = ncols
        self.balance = balance
        total_w = self.extents.right - self.extents.left
        col_width = (total_w - (ncols - 1) * gutter) / ncols
        # We calculate the column extents once in advance, and store them for lookup.
        c_left = self.extents.left
        self._cols = [Extents(c_left, c_left + col_width)]
        for _ in range(1, ncols):
            c_left += col_width + gutter
            self._cols.append(Extents(c_left, c_left + col_width))
        self._first_page_top = max(self.pdf.t_margin, self.pdf.y)

    def __enter__(self) -> "TextColumns":
        super().__enter__()
        self._first_page_top = max(self.pdf.t_margin, self.pdf.y)
        if self.balance:
            self._cur_column = 0
            self.pdf.x = self._cols[self._cur_column].left
        return self

    def new_column(self) -> None:
        "End the current column and continue at the top of the next one."
        if self._paragraphs and isinstance(self._paragraphs[-1], Paragraph):
            self._paragraphs[-1].write(FORM_FEED)
        else:
            self.write(FORM_FEED)

    def _render_page_lines(
        self,
        text_lines: list[ImageParagraph | LineWrapper],
        top: float,
        bottom: float,
    ) -> None:
        """Rendering a set of lines in one or several columns on one page."""
        balancing = False
        next_y = self.pdf.y
        if self.balance:
            # Column balancing is currently very simplistic, and only works reliably when
            # line height doesn't change much within the text block.
            # The "correct" solution would require an exact precalculation of the height of
            # each column with the specific line heights and iterative regrouping of lines,
            # which seems excessive at this point.
            # Contribution of a more reliable but still reasonably simple algorithm welcome.
            page_bottom = bottom
            if not text_lines:
                return
            tot_height = sum(l.line.height or 0 for l in text_lines)
            col_height = tot_height / self._ncols
            avail_height = bottom - top
            if col_height < avail_height:
                balancing = True  # We actually have room to balance on this page.
                # total height divided by n
                bottom = top + col_height
                # A bit more generous: Try to keep the rightmost column the shortest.
                lines_per_column = math.ceil(len(text_lines) / self._ncols) + 0.5
                first_line_height = text_lines[0].line.height or 0
                mult_height = first_line_height * lines_per_column
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
            self._render_column_lines(text_lines, top, bottom)
            if self.pdf.y > next_y:
                next_y = self.pdf.y
        self.pdf.y = next_y

    def render(self) -> None:
        if not self._paragraphs:
            return
        text_lines = self.collect_lines()
        if not text_lines:
            return
        page_bottom = self.pdf.h - self.pdf.b_margin
        first_page_top = max(self.pdf.t_margin, self.pdf.y)
        self._render_page_lines(text_lines, first_page_top, page_bottom)
        # Note: text_lines is progressively emptied by ._render_column_lines()
        while text_lines:
            page_break = self.pdf._perform_page_break_if_need_be(  # pyright: ignore[reportPrivateUsage]
                self.pdf.h
            )
            if not page_break:
                # Can happen when rendering a footer in the wrong place - cf. issue #1222
                break
            self._cur_column = 0
            self._render_page_lines(text_lines, self.pdf.y, page_bottom)

    def current_x_extents(self, y: float, height: float) -> tuple[float, float]:
        left, right = self._cols[self._cur_column]
        return left, right
