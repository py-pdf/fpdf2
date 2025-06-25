"""
This module provides support for embedding and rendering various color font formats
in PDF documents using Type 3 fonts. It defines classes and utilities to handle
different color font technologies, including:

- COLRv0 and COLRv1 (OpenType color vector fonts)
- CBDT/CBLC (bitmap color fonts)
- SBIX (bitmap color fonts)
- SVG (fonts with embedded SVG glyphs)
"""

import logging
from io import BytesIO
from typing import TYPE_CHECKING, List, Tuple, Union

from fontTools.ttLib.tables.BitmapGlyphMetrics import BigGlyphMetrics, SmallGlyphMetrics
from fontTools.ttLib.tables.C_O_L_R_ import table_C_O_L_R_
from fontTools.ttLib.tables.otTables import CompositeMode, Paint, PaintFormat

from .drawing import (
    DeviceRGB,
    GlyphPathPen,
    GraphicsContext,
    GraphicsStyle,
    PaintedPath,
    Transform,
)
from .enums import BlendMode

if TYPE_CHECKING:
    from .fonts import TTFFont
    from .fpdf import FPDF


LOGGER = logging.getLogger(__name__)


class Type3FontGlyph:
    # RAM usage optimization:
    __slots__ = (
        "obj_id",
        "glyph_id",
        "unicode",
        "glyph_name",
        "glyph_width",
        "glyph",
        "_glyph_bounds",
    )
    obj_id: int
    glyph_id: int
    unicode: Tuple
    glyph_name: str
    glyph_width: int
    glyph: str
    _glyph_bounds: Tuple[int, int, int, int]

    def __init__(self):
        pass

    def __hash__(self):
        return self.glyph_id


class Type3Font:

    def __init__(self, fpdf: "FPDF", base_font: "TTFFont"):
        self.i = 1
        self.type = "type3"
        self.fpdf = fpdf
        self.base_font = base_font
        self.upem = self.base_font.ttfont["head"].unitsPerEm
        self.scale = 1000 / self.upem
        self.images_used = set()
        self.graphics_style_used = set()
        self.glyphs: List[Type3FontGlyph] = []

    def get_notdef_glyph(self, glyph_id) -> Type3FontGlyph:
        notdef = Type3FontGlyph()
        notdef.glyph_id = glyph_id
        notdef.unicode = glyph_id
        notdef.glyph_name = ".notdef"
        notdef.glyph_width = (
            self.base_font.cw[0x00]
            if self.base_font.cw[0x00]
            else self.base_font.ttfont["hmtx"].metrics[".notdef"][0]
        )
        notdef.glyph = f"{round(notdef.glyph_width * self.scale + 0.001)} 0 d0"
        return notdef

    def get_space_glyph(self, glyph_id) -> Type3FontGlyph:
        space = Type3FontGlyph()
        space.glyph_id = glyph_id
        space.unicode = 0x20
        space.glyph_name = "space"
        space.glyph_width = (
            self.base_font.cw[0x20]
            if self.base_font.cw[0x20]
            else self.base_font.ttfont["hmtx"].metrics[".notdef"][0]
        )
        space.glyph = f"{round(space.glyph_width * self.scale + 0.001)} 0 d0"
        return space

    def load_glyphs(self):
        for glyph, char_id in self.base_font.subset.items():
            if not self.glyph_exists(glyph.glyph_name):
                if char_id == 0x20 or glyph.glyph_name == "space":
                    self.glyphs.append(self.get_space_glyph(char_id))
                    continue
                if self.glyph_exists(".notdef"):
                    self.add_glyph(".notdef", char_id)
                    continue
                self.glyphs.append(self.get_notdef_glyph(char_id))
                continue
            self.add_glyph(glyph.glyph_name, char_id)

    def add_glyph(self, glyph_name, char_id):
        g = Type3FontGlyph()
        g.glyph_id = char_id
        g.unicode = char_id
        g.glyph_name = glyph_name
        self.load_glyph_image(g)
        self.glyphs.append(g)

    @classmethod
    def get_target_ppem(cls, font_size_pt: int) -> int:
        # Calculating the target ppem:
        # https://learn.microsoft.com/en-us/typography/opentype/spec/ttch01#display-device-characteristics
        # ppem = point_size * dpi / 72
        # The default PDF dpi resolution is 72 dpi - and we have the 72 dpi hardcoded on our scale factor,
        # so we can simplify the calculation.
        return font_size_pt

    def load_glyph_image(self, glyph: Type3FontGlyph):
        raise NotImplementedError("Method must be implemented on child class")

    def glyph_exists(self, glyph_name: str) -> bool:
        raise NotImplementedError("Method must be implemented on child class")


class SVGColorFont(Type3Font):
    """Support for SVG OpenType vector color fonts."""

    def glyph_exists(self, glyph_name: str) -> bool:
        glyph_id = self.base_font.ttfont.getGlyphID(glyph_name)
        return any(
            svg_doc.startGlyphID <= glyph_id <= svg_doc.endGlyphID
            for svg_doc in self.base_font.ttfont["SVG "].docList
        )

    def load_glyph_image(self, glyph: Type3FontGlyph) -> None:
        glyph_id = self.base_font.ttfont.getGlyphID(glyph.glyph_name)
        glyph_svg_data = None
        for svg_doc in self.base_font.ttfont["SVG "].docList:
            if svg_doc.startGlyphID <= glyph_id <= svg_doc.endGlyphID:
                glyph_svg_data = svg_doc.data.encode("utf-8")
                break
        if not glyph_svg_data:
            raise ValueError(
                f"Glyph {glyph.glyph_name} (ID: {glyph_id}) not found in SVG font."
            )
        bio = BytesIO(glyph_svg_data)
        bio.seek(0)
        _, img, _ = self.fpdf.preload_image(bio, None)
        w = round(self.base_font.ttfont["hmtx"].metrics[glyph.glyph_name][0] + 0.001)
        img.base_group.transform = Transform.scaling(self.scale, self.scale)
        output_stream = self.fpdf.draw_vector_glyph(img.base_group, self)
        glyph.glyph = f"{round(w * self.scale)} 0 d0\n" "q\n" f"{output_stream}\n" "Q"
        glyph.glyph_width = w


class CustomGraphicsContextItem:
    """A custom graphics context item that renders a string command in the PDF context."""

    def __init__(self, item):
        self._item = item

    # pylint: disable=unused-argument
    def render(self, gsd_registry, style, last_item, first_point):
        return self._item, None, None


class COLRFont(Type3Font):
    """
    Support for COLRv0 and COLRv1 OpenType color vector fonts.
    https://learn.microsoft.com/en-us/typography/opentype/spec/colr

    COLRv0 is a sequence of glyphs layers with color specification
    and they are built one on top of the other.

    COLRv1 allows for more complex color glyphs by including gradients,
    transformations, and composite operations.

    This class handles both versions of the COLR table by using the
    drawing API to render the glyphs as vector graphics.

    Current limitations:
    - COLRv1 variable fonts are not supported yet.
    - Gradients (linear and radial) are not yet supported by the drawing API,
      so we render only the first color stop of the gradient.
    - Composite paint is not yet implemented.
    """

    def __init__(self, fpdf: "FPDF", base_font: "TTFFont"):
        super().__init__(fpdf, base_font)
        colr_table: table_C_O_L_R_ = self.base_font.ttfont["COLR"]
        self.colrv0_glyphs = []
        self.colrv1_glyphs = []
        self.version = colr_table.version
        if colr_table.version == 0:
            self.colrv0_glyphs = colr_table.ColorLayers
        else:
            self.colrv0_glyphs = colr_table._decompileColorLayersV0(colr_table.table)
            self.colrv1_glyphs = {
                glyph.BaseGlyph: glyph
                for glyph in colr_table.table.BaseGlyphList.BaseGlyphPaintRecord
            }
        self.palette = None
        if "CPAL" in self.base_font.ttfont:
            # hardcoding the first palette for now
            print(
                f"This font has {len(self.base_font.ttfont['CPAL'].palettes)} palettes"
            )
            palette = self.base_font.ttfont["CPAL"].palettes[0]
            self.palette = [
                (
                    color.red / 255,
                    color.green / 255,
                    color.blue / 255,
                    color.alpha / 255,
                )
                for color in palette
            ]

    def glyph_exists(self, glyph_name: str) -> bool:
        return glyph_name in self.colrv0_glyphs or glyph_name in self.colrv1_glyphs

    def load_glyph_image(self, glyph: Type3FontGlyph) -> None:
        w = round(self.base_font.ttfont["hmtx"].metrics[glyph.glyph_name][0] + 0.001)
        # print(glyph.glyph_name, glyph.unicode)
        if glyph.glyph_name in self.colrv0_glyphs:
            glyph_layers = self.base_font.ttfont["COLR"].ColorLayers[glyph.glyph_name]
            img = self.draw_glyph_colrv0(glyph_layers)
        else:
            img = self.draw_glyph_colrv1(glyph.glyph_name)
        img.transform = Transform.scaling(self.scale, -self.scale)
        output_stream = self.fpdf.draw_vector_glyph(img, self)
        glyph.glyph = f"{round(w * self.scale)} 0 d0\n" "q\n" f"{output_stream}\n" "Q"
        glyph.glyph_width = w

    def get_color(self, color_index: int, alpha=1) -> DeviceRGB:
        # TO DO : A palette entry index value of 0xFFFF is a special case indicating
        # that the text foreground color (defined by the application) should be used,
        # and must not be treated as an actual index into the CPAL ColorRecord array.
        r, g, b, a = self.palette[color_index]
        a *= alpha
        return DeviceRGB(r, g, b, a)

    def draw_glyph_colrv0(self, layers):
        gc = GraphicsContext()
        for layer in layers:
            path = PaintedPath()
            glyph_set = self.base_font.ttfont.getGlyphSet()
            pen = GlyphPathPen(path, glyphSet=glyph_set)
            glyph = glyph_set[layer.name]
            glyph.draw(pen)
            path.style.fill_color = self.get_color(layer.colorID)
            path.style.stroke_color = self.get_color(layer.colorID)
            gc.add_item(path)
        return gc

    def draw_glyph_colrv1(self, glyph_name):
        gc = GraphicsContext()
        glyph = self.colrv1_glyphs[glyph_name]
        self.draw_colrv1_paint(glyph.Paint, gc)
        return gc

    def draw_colrv1_paint(self, paint: Paint, gc: GraphicsContext):
        if paint.Format == PaintFormat.PaintColrLayers:  # 1
            layer_list = self.base_font.ttfont["COLR"].table.LayerList
            for layer in range(
                paint.FirstLayerIndex, paint.FirstLayerIndex + paint.NumLayers
            ):
                self.draw_colrv1_paint(layer_list.Paint[layer], gc)
        elif paint.Format == PaintFormat.PaintSolid:  # 2
            color = self.get_color(paint.PaletteIndex, paint.Alpha)
            path = get_last_painted_path(gc)
            if path:
                path.style.fill_color = color
                path.style.stroke_color = color
        elif paint.Format == PaintFormat.PaintVarSolid:  # 3
            raise NotImplementedError("Variable fonts are not yet supported.")
        elif paint.Format == PaintFormat.PaintLinearGradient:  # 4
            # TO DO: add linear gradient support after adding it on the drawing api.
            # In the meantime, we will render the first color stop only.
            color = self.get_color(
                paint.ColorLine.ColorStop[0].PaletteIndex,
                paint.ColorLine.ColorStop[0].Alpha,
            )
            path = get_last_painted_path(gc)
            path.style.fill_color = color
            path.style.stroke_color = color
        elif paint.Format == PaintFormat.PaintVarLinearGradient:  # 5
            raise NotImplementedError("Variable fonts are not yet supported.")
        elif paint.Format == PaintFormat.PaintRadialGradient:  # 6
            # TO DO: add radial gradient support after adding it on the drawing api.
            # In the meantime, we will render the first color stop only.
            color = self.get_color(
                paint.ColorLine.ColorStop[0].PaletteIndex,
                paint.ColorLine.ColorStop[0].Alpha,
            )
            path = get_last_painted_path(gc)
            path.style.fill_color = color
            path.style.stroke_color = color
        elif paint.Format == PaintFormat.PaintVarRadialGradient:  # 7
            raise NotImplementedError("Variable fonts are not yet supported.")
        elif paint.Format == PaintFormat.PaintSweepGradient:  # 8
            print(paint.Format)
            raise NotImplementedError
        elif paint.Format == PaintFormat.PaintVarSweepGradient:  # 9
            raise NotImplementedError("Variable fonts are not yet supported.")
        elif paint.Format == PaintFormat.PaintGlyph:  # 10
            path = PaintedPath()
            glyph_set = self.base_font.ttfont.getGlyphSet()
            pen = GlyphPathPen(path, glyphSet=glyph_set)
            glyph = glyph_set[paint.Glyph]
            glyph.draw(pen)
            gc.add_item(path)
            self.draw_colrv1_paint(paint.Paint, gc)
        elif paint.Format == PaintFormat.PaintColrGlyph:  # 11
            print(paint.Format)
            raise NotImplementedError
        elif paint.Format == PaintFormat.PaintTransform:  # 12
            path = PaintedPath()
            transform = Transform(
                paint.Transform.xx,
                paint.Transform.yx,
                paint.Transform.xy,
                paint.Transform.yy,
                paint.Transform.dx,
                paint.Transform.dy,
            )
            gc.add_item(CustomGraphicsContextItem(f"q {transform.render(None)[0]} "))
            self.draw_colrv1_paint(paint.Paint, gc)
            gc.add_item(CustomGraphicsContextItem("Q "))
        elif paint.Format == PaintFormat.PaintVarTransform:  # 13
            raise NotImplementedError("Variable fonts are not yet supported.")
        elif paint.Format == PaintFormat.PaintTranslate:  # 14
            transform = Transform.translation(paint.dx, paint.dy)
            gc.add_item(CustomGraphicsContextItem(f"q {transform.render(None)[0]} "))
            self.draw_colrv1_paint(paint.Paint, gc)
            gc.add_item(CustomGraphicsContextItem("Q "))
        elif paint.Format == PaintFormat.PaintVarTranslate:  # 15
            raise NotImplementedError("Variable fonts are not yet supported.")
        elif paint.Format == PaintFormat.PaintScale:  # 16
            transform = Transform.scaling(paint.scaleX, paint.scaleY)
            gc.add_item(CustomGraphicsContextItem(f"q {transform.render(None)[0]} "))
            self.draw_colrv1_paint(paint.Paint, gc)
            gc.add_item(CustomGraphicsContextItem("Q "))
        elif paint.Format == PaintFormat.PaintVarScale:  # 17
            raise NotImplementedError("Variable fonts are not yet supported.")
        elif paint.Format == PaintFormat.PaintScaleAroundCenter:  # 18
            print(paint.centerX, paint.centerY, paint.scaleX, paint.scaleY)
            transform = (
                Transform.translation(paint.centerX, -paint.centerY)
                .scale(paint.scaleX, paint.scaleY)
                .translate(-paint.centerX, paint.centerY)
            )
            gc.add_item(CustomGraphicsContextItem(f"q {transform.render(None)[0]} "))
            self.draw_colrv1_paint(paint.Paint, gc)
            gc.add_item(CustomGraphicsContextItem("Q "))
        elif paint.Format == PaintFormat.PaintVarScaleAroundCenter:  # 19
            raise NotImplementedError("Variable fonts are not yet supported.")
        elif paint.Format == PaintFormat.PaintScaleUniform:  # 20
            print(paint.Format)
            raise NotImplementedError
        elif paint.Format == PaintFormat.PaintVarScaleUniform:  # 21
            raise NotImplementedError("Variable fonts are not yet supported.")
        elif paint.Format == PaintFormat.PaintScaleUniformAroundCenter:  # 22
            print(paint.Format)
            raise NotImplementedError
        elif paint.Format == PaintFormat.PaintVarScaleUniformAroundCenter:  # 23
            raise NotImplementedError("Variable fonts are not yet supported.")
        elif paint.Format == PaintFormat.PaintRotate:  # 24
            print(paint.Format)
            raise NotImplementedError
        elif paint.Format == PaintFormat.PaintVarRotate:  # 25
            raise NotImplementedError("Variable fonts are not yet supported.")
        elif paint.Format == PaintFormat.PaintRotateAroundCenter:  # 26
            print(paint.Format)
            raise NotImplementedError
        elif paint.Format == PaintFormat.PaintVarRotateAroundCenter:  # 27
            raise NotImplementedError("Variable fonts are not yet supported.")
        elif paint.Format == PaintFormat.PaintSkew:  # 28
            print(paint.Format)
            raise NotImplementedError
        elif paint.Format == PaintFormat.PaintVarSkew:  # 29
            raise NotImplementedError("Variable fonts are not yet supported.")
        elif paint.Format == PaintFormat.PaintSkewAroundCenter:  # 30
            print(paint.Format)
            raise NotImplementedError
        elif paint.Format == PaintFormat.PaintVarSkewAroundCenter:  # 31
            raise NotImplementedError("Variable fonts are not yet supported.")
        elif paint.Format == PaintFormat.PaintComposite:  # 32
            print(paint.CompositeMode)

            # DEST_OVER = Source paint is drawn over the backdrop paint (Inverted SRC_OVER)

            # blend_mode = get_blend_mode(paint.CompositeMode)
            # TO DO: complete implementation of the composite paint.
            # Composite has 2 elements to drawn:
            # - Brackdrop paint is the "background" - the element to draw first. it has by default
            #   composite mode "SRC_OVER" (no compositing with other elements - just draw)
            # - Source paint is the new element being drawn and it blends with the backdrop using a composite mode.
            #   The composite operators are on fontTools.ttLib.tables.otTables.CompositeMode
            #   https://www.w3.org/TR/compositing-1/
            self.draw_colrv1_paint(paint.BackdropPaint, gc)
            # path = get_last_painted_path(gc)
            # path.style.blend_mode = get_blend_mode(CompositeMode.SRC_OVER)
            self.draw_colrv1_paint(paint.SourcePaint, gc)
            # path.style.blend_mode = get_blend_mode(paint.CompositeMode)
            # gc.style.blend_mode = blend_mode
        else:
            raise NotImplementedError(f"Unknown PaintFormat: {paint.Format}")


class CBDTColorFont(Type3Font):
    """Support for CBDT+CBLC bitmap color fonts."""

    # Only looking at the first strike - Need to look all strikes available on the CBLC table first?
    def glyph_exists(self, glyph_name: str) -> bool:
        return glyph_name in self.base_font.ttfont["CBDT"].strikeData[0]

    def load_glyph_image(self, glyph: Type3FontGlyph) -> None:
        ppem = self.base_font.ttfont["CBLC"].strikes[0].bitmapSizeTable.ppemX
        g = self.base_font.ttfont["CBDT"].strikeData[0][glyph.glyph_name]
        glyph_bitmap = g.data[9:]
        metrics = g.metrics
        if isinstance(metrics, SmallGlyphMetrics):
            x_min = round(metrics.BearingX * self.upem / ppem)
            y_min = round((metrics.BearingY - metrics.height) * self.upem / ppem)
            x_max = round(metrics.width * self.upem / ppem)
            y_max = round(metrics.BearingY * self.upem / ppem)
        elif isinstance(metrics, BigGlyphMetrics):
            x_min = round(metrics.horiBearingX * self.upem / ppem)
            y_min = round((metrics.horiBearingY - metrics.height) * self.upem / ppem)
            x_max = round(metrics.width * self.upem / ppem)
            y_max = round(metrics.horiBearingY * self.upem / ppem)
        else:  # fallback scenario: use font bounding box
            x_min = self.base_font.ttfont["head"].xMin
            y_min = self.base_font.ttfont["head"].yMin
            x_max = self.base_font.ttfont["head"].xMax
            y_max = self.base_font.ttfont["head"].yMax

        bio = BytesIO(glyph_bitmap)
        bio.seek(0)
        _, _, info = self.fpdf.preload_image(bio, None)
        w = round(self.base_font.ttfont["hmtx"].metrics[glyph.glyph_name][0] + 0.001)
        glyph.glyph = (
            f"{round(w * self.scale)} 0 d0\n"
            "q\n"
            f"{(x_max - x_min)* self.scale} 0 0 {(-y_min + y_max)*self.scale} {x_min*self.scale} {y_min*self.scale} cm\n"
            f"/I{info['i']} Do\nQ"
        )
        self.images_used.add(info["i"])
        glyph.glyph_width = w


class SBIXColorFont(Type3Font):
    """Support for SBIX bitmap color fonts."""

    def glyph_exists(self, glyph_name: str) -> bool:
        glyph = (
            self.base_font.ttfont["sbix"]
            .strikes[self.get_strike_index()]
            .glyphs.get(glyph_name)
        )
        return glyph and glyph.graphicType

    def get_strike_index(self) -> int:
        target_ppem = self.get_target_ppem(self.base_font.biggest_size_pt)
        ppem_list = [
            ppem
            for ppem in self.base_font.ttfont["sbix"].strikes.keys()
            if ppem >= target_ppem
        ]
        if not ppem_list:
            return max(list(self.base_font.ttfont["sbix"].strikes.keys()))
        return min(ppem_list)

    def load_glyph_image(self, glyph: Type3FontGlyph) -> None:
        ppem = self.get_strike_index()
        sbix_glyph = (
            self.base_font.ttfont["sbix"].strikes[ppem].glyphs.get(glyph.glyph_name)
        )
        if sbix_glyph.graphicType == "dupe":
            raise NotImplementedError(
                f"{glyph.glyph_name}: Dupe SBIX graphic type not implemented."
            )
            # waiting for an example to test
            # dupe_char = font.getBestCmap()[glyph.imageData]
            # return self.get_color_glyph(dupe_char)

        if sbix_glyph.graphicType not in ("jpg ", "png ", "tiff"):  # pdf or mask
            raise NotImplementedError(
                f" {glyph.glyph_name}: Invalid SBIX graphic type {sbix_glyph.graphicType}."
            )

        bio = BytesIO(sbix_glyph.imageData)
        bio.seek(0)
        _, _, info = self.fpdf.preload_image(bio, None)
        w = round(self.base_font.ttfont["hmtx"].metrics[glyph.glyph_name][0] + 0.001)
        glyf_metrics = self.base_font.ttfont["glyf"].get(glyph.glyph_name)
        x_min = glyf_metrics.xMin + sbix_glyph.originOffsetX
        x_max = glyf_metrics.xMax + sbix_glyph.originOffsetX
        y_min = glyf_metrics.yMin + sbix_glyph.originOffsetY
        y_max = glyf_metrics.yMax + sbix_glyph.originOffsetY

        glyph.glyph = (
            f"{round(w * self.scale)} 0 d0\n"
            "q\n"
            f"{(x_max - x_min) * self.scale} 0 0 {(-y_min + y_max) * self.scale} {x_min * self.scale} {y_min * self.scale} cm\n"
            f"/I{info['i']} Do\nQ"
        )
        self.images_used.add(info["i"])
        glyph.glyph_width = w


def get_color_font_object(fpdf: "FPDF", base_font: "TTFFont") -> Union[Type3Font, None]:
    if "CBDT" in base_font.ttfont:
        LOGGER.debug("Font %s is a CBLC+CBDT color font", base_font.name)
        return CBDTColorFont(fpdf, base_font)
    if "EBDT" in base_font.ttfont:
        raise NotImplementedError(
            f"{base_font.name} - EBLC+EBDT color font is not supported yet"
        )
    if "COLR" in base_font.ttfont:
        if base_font.ttfont["COLR"].version == 0:
            LOGGER.debug("Font %s is a COLRv0 color font", base_font.name)
        else:
            LOGGER.debug("Font %s is a COLRv1 color font", base_font.name)
        return COLRFont(fpdf, base_font)
    if "SVG " in base_font.ttfont:
        LOGGER.debug("Font %s is a SVG color font", base_font.name)
        return SVGColorFont(fpdf, base_font)
    if "sbix" in base_font.ttfont:
        LOGGER.debug("Font %s is a SBIX color font", base_font.name)
        return SBIXColorFont(fpdf, base_font)
    return None


def get_last_painted_path(gc: GraphicsContext) -> PaintedPath:
    """Utilitary method to return the last painted path added to a graphics context"""
    for item in reversed(gc.path_items):
        if isinstance(item, PaintedPath):
            return item
    return None  # raise ValueError("Invalid glyph")


def get_blend_mode(composite_mode: CompositeMode) -> GraphicsStyle:
    """Get the FPDF BlendMode for a given CompositeMode."""

    # TO DO: Need to add support for the following CompositeMode:
    # CLEAR = 0
    # SRC = 1
    # DEST = 2
    # SRC_OVER = 3
    # DEST_OVER = 4
    # SRC_IN = 5
    # DEST_IN = 6
    # SRC_OUT = 7
    # DEST_OUT = 8
    # SRC_ATOP = 9
    # DEST_ATOP = 10
    # XOR = 11
    # PLUS = 12

    mode_map = {
        CompositeMode.SRC_IN: BlendMode.NORMAL,  # temporary
        CompositeMode.SRC_OVER: BlendMode.NORMAL,
        CompositeMode.SCREEN: BlendMode.SCREEN,
        CompositeMode.OVERLAY: BlendMode.OVERLAY,
        CompositeMode.DARKEN: BlendMode.DARKEN,
        CompositeMode.LIGHTEN: BlendMode.LIGHTEN,
        CompositeMode.COLOR_DODGE: BlendMode.COLOR_DODGE,
        CompositeMode.COLOR_BURN: BlendMode.COLOR_BURN,
        CompositeMode.HARD_LIGHT: BlendMode.HARD_LIGHT,
        CompositeMode.SOFT_LIGHT: BlendMode.SOFT_LIGHT,
        CompositeMode.DIFFERENCE: BlendMode.DIFFERENCE,
        CompositeMode.EXCLUSION: BlendMode.EXCLUSION,
        CompositeMode.MULTIPLY: BlendMode.MULTIPLY,
        CompositeMode.HSL_HUE: BlendMode.HUE,
        CompositeMode.HSL_SATURATION: BlendMode.SATURATION,
        CompositeMode.HSL_COLOR: BlendMode.COLOR,
        CompositeMode.HSL_LUMINOSITY: BlendMode.LUMINOSITY,
    }
    blend_mode = mode_map.get(composite_mode, None)
    if not blend_mode:
        raise NotImplementedError(f"Unknown composite mode: {composite_mode}")
    # gs = GraphicsStyle()
    # gs.blend_mode = blend_mode
    return blend_mode
