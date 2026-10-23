"""
Inline image and figure wrapping utilities for fpdf2.
"""

# pylint: disable=protected-access

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional, Union, cast

from .drawing_primitives import Transform
from .enums import Align, PDFResourceType, ResourceAccessPolicy, VAlign, XPos, YPos
from .errors import FPDFException
from .image_parsing import preload_image
from .image_datastructures import RasterImageInfo, VectorImageInfo
from .line_break import Fragment, TextLine
from .output import stream_content_for_raster_image
from .svg import SVGObject, Percent, apply_svg_transform_to_user_space_gradients
from .util import ImageType

if TYPE_CHECKING:
    from .fpdf import FPDF
    from .graphics_state import GraphicsState


# Typographic baseline and alignment metrics (consistent with fpdf._render_styled_text_line):
TEXT_BASELINE_RATIO = (
    0.8  # Ratio for baseline position: 0.5 * h + 0.3 * font_size (when h == font_size)
)
CAP_HEIGHT_RATIO = 0.7  # Top alignment with capital letter ascenders
X_HEIGHT_MID_RATIO = (
    0.2  # Mid-point ratio for lowercase character bodies (x-height center)
)


class ImageFragment(Fragment):
    """
    A special type of fragment that represents an inline image or vector graphic
    within a flowing line of text.
    """

    def __init__(
        self,
        image_name: Any,
        img: Any,
        info: Union["RasterImageInfo", "VectorImageInfo"],
        w: float,
        h: float,
        graphics_state: GraphicsState,
        k: float,
        valign: Union[VAlign, str] = VAlign.M,
        link: Optional[Union[str, int]] = None,
        alt_text: Optional[str] = None,
        title: Optional[str] = None,
    ) -> None:
        super().__init__(["\ufffc"], graphics_state, k, link=link)
        self.image_name = image_name
        self.img = img
        self.info = info
        self.w = w
        self.h = h
        self.valign = VAlign.coerce(valign) if valign else VAlign.M
        self.alt_text = alt_text
        self.title = title

    def clone(
        self, characters: Union[list[str], str] = "", link: Optional[int | str] = None
    ) -> "ImageFragment":
        clone_obj = cast(
            ImageFragment,
            super().clone(characters=characters or ["\ufffc"], link=link or self.link),
        )
        clone_obj.image_name = self.image_name
        clone_obj.img = self.img
        clone_obj.info = self.info
        clone_obj.w = self.w
        clone_obj.h = self.h
        clone_obj.valign = self.valign
        clone_obj.alt_text = self.alt_text
        clone_obj.title = self.title
        return clone_obj

    @property
    def height(self) -> float:
        return self.h

    def get_y(self, base_y: float, max_font_size: float) -> float:
        """
        Calculates the vertical top position of the image aligned with the text line.
        Ensures the top position does not extend above base_y (the line top) to prevent
        tall inline images from overlapping preceding text lines.
        """
        baseline_y = base_y + TEXT_BASELINE_RATIO * max_font_size
        if self.valign == VAlign.T:
            raw_y = baseline_y - CAP_HEIGHT_RATIO * max_font_size
        elif self.valign == VAlign.B:
            raw_y = baseline_y - self.h
        else:
            raw_y = baseline_y - (X_HEIGHT_MID_RATIO * max_font_size) - (0.5 * self.h)
        return max(base_y, raw_y)

    def get_width(
        self,
        start: int = 0,
        end: Optional[int] = None,
        chars: Optional[str] = None,
        initial_cs: bool = True,
    ) -> float:
        return self.w

    def get_character_width(
        self,
        character: str,
        print_sh: bool = False,
        initial_cs: bool = True,
    ) -> float:
        return self.w

    def render_pdf_text(
        self,
        frag_ws: float,
        current_ws: float,
        word_spacing: float,
        adjust_x: float,
        adjust_y: float,
        h: float,
    ) -> str:
        # ImageFragments do not emit text into PDF BT/ET content streams
        return ""


def build_image_fragment(
    pdf: FPDF,
    name: ImageType,
    w: float = 0,
    h: float = 0,
    valign: Union[VAlign, str] = VAlign.M,
    keep_aspect_ratio: bool = True,
    link: Optional[str | int] = "",
    title: Optional[str] = None,
    alt_text: Optional[str] = None,
    resource_access_policy: Optional[ResourceAccessPolicy] = None,
) -> ImageFragment:
    """
    Preloads an image (raster or vector) and builds an ImageFragment sized to fit
    within the target line height or intrinsic aspect ratio.
    """
    if not pdf.font_family:
        raise FPDFException("No font set, you need to call set_font() beforehand")

    if resource_access_policy is None:
        resource_access_policy = pdf.resource_access_policy

    image_name, img, info = preload_image(
        pdf.image_cache,
        name,
        None,
        resource_access_policy=resource_access_policy,
        svg_limits=pdf.svg_limits,
    )

    if isinstance(info, VectorImageInfo):
        svg = cast(SVGObject, img)
        if not svg.viewbox and svg.width and svg.height:
            svg.viewbox = [float(0), float(0), svg.width, svg.height]
        if w == 0 and h == 0:
            h = pdf.font_size
            if svg.width and svg.height:
                svg_w = (
                    svg.width * pdf.epw / 100
                    if isinstance(svg.width, Percent)
                    else svg.width
                )
                svg_h = (
                    svg.height * pdf.eph / 100
                    if isinstance(svg.height, Percent)
                    else svg.height
                )
                w = h * svg_w / svg_h
            elif svg.viewbox:
                _, _, svg_w, svg_h = svg.viewbox
                w = h * svg_w / svg_h
            else:
                w = h
        elif w == 0:
            if svg.width and svg.height:
                svg_w = (
                    svg.width * pdf.epw / 100
                    if isinstance(svg.width, Percent)
                    else svg.width
                )
                svg_h = (
                    svg.height * pdf.eph / 100
                    if isinstance(svg.height, Percent)
                    else svg.height
                )
                w = h * svg_w / svg_h
            elif svg.viewbox:
                _, _, svg_w, svg_h = svg.viewbox
                w = h * svg_w / svg_h
            else:
                w = h
        elif h == 0:
            if svg.width and svg.height:
                svg_w = (
                    svg.width * pdf.epw / 100
                    if isinstance(svg.width, Percent)
                    else svg.width
                )
                svg_h = (
                    svg.height * pdf.eph / 100
                    if isinstance(svg.height, Percent)
                    else svg.height
                )
                h = w * svg_h / svg_w
            elif svg.viewbox:
                _, _, svg_w, svg_h = svg.viewbox
                h = w * svg_h / svg_w
            else:
                h = w
        elif keep_aspect_ratio:
            _, _, w, h = info.scale_inside_box(0, 0, w, h)
    else:
        if w == 0 and h == 0:
            h = pdf.font_size
            w = info.width * h / info.height
        elif w == 0 or h == 0:
            w, h = info.size_in_document_units(w, h, scale=pdf.k)
        elif keep_aspect_ratio:
            _, _, w, h = info.scale_inside_box(0, 0, w, h)

    valign = VAlign.coerce(valign)

    return ImageFragment(
        image_name=image_name,
        img=img,
        info=info,
        w=w,
        h=h,
        graphics_state=pdf._get_current_graphics_state(),  # pyright: ignore[reportPrivateUsage]
        k=pdf.k,
        valign=valign,
        link=link or None,
        alt_text=alt_text,
        title=title,
    )


def write_inline_image(
    pdf: FPDF,
    name: ImageType,
    w: float = 0,
    h: float = 0,
    valign: Union[VAlign, str] = VAlign.M,
    keep_aspect_ratio: bool = True,
    link: Optional[str | int] = "",
    title: Optional[str] = None,
    alt_text: Optional[str] = None,
    resource_access_policy: Optional[ResourceAccessPolicy] = None,
) -> bool:
    """
    Renders an inline image at the current PDF position, wrapping to the next line
    if the image width exceeds the remaining line width.
    """
    frag = build_image_fragment(
        pdf=pdf,
        name=name,
        w=w,
        h=h,
        valign=valign,
        keep_aspect_ratio=keep_aspect_ratio,
        link=link,
        title=title,
        alt_text=alt_text,
        resource_access_policy=resource_access_policy,
    )

    first_width = pdf.w - pdf.x - pdf.r_margin
    full_width = pdf.w - pdf.l_margin - pdf.r_margin
    line_height = max(pdf.font_size, frag.h)

    if frag.w > first_width and (pdf.x > pdf.l_margin + pdf.c_margin):
        pdf.ln()
        line_w = full_width
    else:
        line_w = first_width

    text_line = TextLine(
        fragments=[frag],
        text_width=frag.w,
        number_of_spaces=0,
        align=Align.L,
        height=line_height,
        max_width=line_w,
    )

    return pdf._render_styled_text_line(  # pyright: ignore[reportPrivateUsage]
        text_line,
        h=line_height,
        border=0,
        new_x=XPos.WCONT,
        new_y=YPos.TOP,
        fill=False,
        link=link,
    )


def render_inline_image(
    pdf: FPDF,
    frag: ImageFragment,
    img_x: float,
    img_y: float,
    sl: list[str],
) -> None:
    """
    Renders an inline raster or vector image (SVG) into the PDF stream or draw context.
    """
    if isinstance(frag.info, VectorImageInfo):
        # Vector image (SVG)
        svg = cast(SVGObject, frag.img)
        _, _, path = svg.transform_to_rect_viewport(
            scale=1, width=frag.w, height=frag.h, ignore_svg_top_attrs=True
        )
        if path.transform is not None:
            path.transform = path.transform @ Transform.translation(img_x, img_y)
        apply_svg_transform_to_user_space_gradients(path)
        old_x, old_y = pdf.x, pdf.y
        try:
            pdf.set_xy(0, 0)
            if frag.title or frag.alt_text:
                with pdf._marked_sequence(  # pyright: ignore[reportPrivateUsage]
                    title=frag.title, alt_text=frag.alt_text
                ):
                    pdf.draw_path(path, copy=False)
            else:
                pdf.draw_path(path, copy=False)
        finally:
            pdf.set_xy(old_x, old_y)
    else:
        # Raster image
        img_stream = stream_content_for_raster_image(
            frag.info,
            img_x,
            img_y,
            frag.w,
            frag.h,
            False,
            scale=pdf.k,
            pdf_height_to_flip=pdf.h,
        )
        if frag.title or frag.alt_text:
            with pdf._marked_sequence(  # pyright: ignore[reportPrivateUsage]
                title=frag.title, alt_text=frag.alt_text
            ):
                sl.append(img_stream)
        else:
            sl.append(img_stream)
        pdf._resource_catalog.add(  # pyright: ignore[reportPrivateUsage]
            PDFResourceType.X_OBJECT, frag.info["i"], pdf.page  # type: ignore
        )

    if frag.link:
        pdf.link(
            x=img_x,
            y=img_y,
            w=frag.w,
            h=frag.h,
            link=frag.link,
        )
