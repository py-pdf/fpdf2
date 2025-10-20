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
import math
from io import BytesIO
from typing import TYPE_CHECKING, List, Optional, Tuple, Union

from fontTools.ttLib.tables.BitmapGlyphMetrics import BigGlyphMetrics, SmallGlyphMetrics
from fontTools.ttLib.tables.C_O_L_R_ import table_C_O_L_R_
from collections import UserList

# pylint: disable=no-name-in-module
from fontTools.ttLib.tables.otTables import (
    ClipBoxFormat,
    CompositeMode,
    Paint,
    PaintFormat,
    VarAffine2x3,
    VarColorLine,
    VarColorStop,
)
from fontTools.varLib.varStore import VarStoreInstancer

from .drawing_primitives import DeviceRGB, DeviceGray, DeviceCMYK, Transform
from .drawing import (
    BoundingBox,
    ClippingPath,
    GlyphPathPen,
    GradientPaint,
    GraphicsContext,
    PaintComposite,
    PaintBlendComposite,
    PaintedPath,
)
from .enums import (
    BlendMode,
    CompositingOperation,
    GradientSpreadMethod,
    GradientUnits,
    PathPaintRule,
)
from .pattern import SweepGradient, shape_linear_gradient, shape_radial_gradient

if TYPE_CHECKING:
    from .fonts import TTFFont
    from .fpdf import FPDF

LOGGER = logging.getLogger(__name__)

PAINT_VAR_MAPPING = {
    PaintFormat.PaintVarSolid: PaintFormat.PaintSolid,
    PaintFormat.PaintVarLinearGradient: PaintFormat.PaintLinearGradient,
    PaintFormat.PaintVarRadialGradient: PaintFormat.PaintRadialGradient,
    PaintFormat.PaintVarSweepGradient: PaintFormat.PaintSweepGradient,
    PaintFormat.PaintVarTransform: PaintFormat.PaintTransform,
    PaintFormat.PaintVarTranslate: PaintFormat.PaintTranslate,
    PaintFormat.PaintVarScale: PaintFormat.PaintScale,
    PaintFormat.PaintVarScaleAroundCenter: PaintFormat.PaintScaleAroundCenter,
    PaintFormat.PaintVarScaleUniform: PaintFormat.PaintScaleUniform,
    PaintFormat.PaintVarScaleUniformAroundCenter: PaintFormat.PaintScaleUniformAroundCenter,
    PaintFormat.PaintVarRotate: PaintFormat.PaintRotate,
    PaintFormat.PaintVarRotateAroundCenter: PaintFormat.PaintRotateAroundCenter,
    PaintFormat.PaintVarSkew: PaintFormat.PaintSkew,
    PaintFormat.PaintVarSkewAroundCenter: PaintFormat.PaintSkewAroundCenter,
}


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
        self.patterns_used = set()
        self.glyphs: List[Type3FontGlyph] = []

    def get_notdef_glyph(self, glyph_id) -> Type3FontGlyph:
        notdef = Type3FontGlyph()
        notdef.glyph_id = glyph_id
        notdef.unicode = glyph_id
        notdef.glyph_name = ".notdef"
        notdef.glyph_width = self.base_font.ttfont["hmtx"].metrics[".notdef"][0]
        notdef.glyph = f"{round(notdef.glyph_width * self.scale + 0.001)} 0 d0"
        return notdef

    def get_space_glyph(self, glyph_id) -> Type3FontGlyph:
        space = Type3FontGlyph()
        space.glyph_id = glyph_id
        space.unicode = 0x20
        space.glyph_name = "space"
        w = (
            self.base_font.ttfont["hmtx"].metrics["space"][0]
            if "space" in self.base_font.ttfont["hmtx"].metrics
            else self.base_font.ttfont["hmtx"].metrics[".notdef"][0]
        )
        space.glyph_width = round(w + 0.001)
        space.glyph = f"{round(space.glyph_width * self.scale + 0.001)} 0 d0"
        return space

    def load_glyphs(self):
        WHITES = {
            0x0009,
            0x000A,
            0x000C,
            0x000D,
            0x0020,
            0x00A0,
            0x1680,
            0x2000,
            0x2001,
            0x2002,
            0x2003,
            0x2004,
            0x2005,
            0x2006,
            0x2007,
            0x2008,
            0x2009,
            0x200A,
            0x202F,
            0x205F,
            0x3000,
        }
        for glyph, char_id in self.base_font.subset.items():
            if glyph.unicode in WHITES or glyph.glyph_name in ("space", "uni00A0"):
                self.glyphs.append(self.get_space_glyph(char_id))
                continue
            if not self.glyph_exists(glyph.glyph_name):
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
        _, img, _ = self.fpdf.preload_glyph_image(glyph_image_bytes=bio)
        w = round(self.base_font.ttfont["hmtx"].metrics[glyph.glyph_name][0] + 0.001)
        img.base_group.transform = Transform.scaling(self.scale, self.scale)
        output_stream = self.fpdf.draw_vector_glyph(img.base_group, self)
        glyph.glyph = f"{round(w * self.scale)} 0 d0\n" "q\n" f"{output_stream}\n" "Q"
        glyph.glyph_width = w


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
    """

    def __init__(self, fpdf: "FPDF", base_font: "TTFFont", palette_index: int = 0):
        super().__init__(fpdf, base_font)
        colr_table: table_C_O_L_R_ = self.base_font.ttfont["COLR"]
        self.colrv0_glyphs = []
        self.colrv1_glyphs = []
        self.version = colr_table.version
        self.colrv1_clip_boxes = {}
        self.colr_var_instancer = None
        self.colr_var_index_map = None
        if colr_table.version == 0:
            self.colrv0_glyphs = colr_table.ColorLayers
        else:
            try:
                self.colrv0_glyphs = (
                    colr_table._decompileColorLayersV0(colr_table.table) or {}
                )
            except (KeyError, AttributeError, TypeError, ValueError):
                self.colrv0_glyphs = {}
            colr_table_v1 = colr_table.table
            var_store = getattr(colr_table_v1, "VarStore", None)
            if var_store is not None:
                axis_tags = []
                if "fvar" in self.base_font.ttfont:
                    axis_tags = [
                        axis.axisTag for axis in self.base_font.ttfont["fvar"].axes
                    ]
                self.colr_var_instancer = VarStoreInstancer(var_store, axis_tags)
                self.colr_var_instancer.setLocation({tag: 0.0 for tag in axis_tags})
                var_index_map = getattr(colr_table_v1, "VarIndexMap", None)
                if var_index_map is not None:
                    self.colr_var_index_map = var_index_map.mapping
            self.colrv1_glyphs = {
                glyph.BaseGlyph: glyph
                for glyph in colr_table_v1.BaseGlyphList.BaseGlyphPaintRecord
            }
            clip_list = getattr(colr_table_v1, "ClipList", None)
            if clip_list is not None:
                for glyph_name, clip in getattr(clip_list, "clips", {}).items():
                    resolved = self._resolve_clip_box(clip)
                    if resolved is not None:
                        self.colrv1_clip_boxes[glyph_name] = resolved
        self.palette = None
        if "CPAL" in self.base_font.ttfont:
            num_palettes = len(self.base_font.ttfont["CPAL"].palettes)
            # Validate palette index
            if palette_index >= num_palettes:
                LOGGER.warning(
                    "Palette index %s is out of range. This font has %s palettes. Using palette 0.",
                    palette_index,
                    num_palettes,
                )
                palette_index = 0
            palette = self.base_font.ttfont["CPAL"].palettes[palette_index]
            self.palette = [
                (
                    color.red / 255,
                    color.green / 255,
                    color.blue / 255,
                    color.alpha / 255,
                )
                for color in palette
            ]

    def metric_bbox(self) -> BoundingBox:
        return BoundingBox(
            self.base_font.ttfont["head"].xMin,
            self.base_font.ttfont["head"].yMin,
            self.base_font.ttfont["head"].xMax,
            self.base_font.ttfont["head"].yMax,
        )

    def glyph_exists(self, glyph_name: str) -> bool:
        return glyph_name in self.colrv0_glyphs or glyph_name in self.colrv1_glyphs

    def load_glyph_image(self, glyph: Type3FontGlyph) -> None:
        w = round(self.base_font.ttfont["hmtx"].metrics[glyph.glyph_name][0] + 0.001)
        if glyph.glyph_name in self.colrv0_glyphs:
            glyph_layers = self.colrv0_glyphs[glyph.glyph_name]
            img = self.draw_glyph_colrv0(glyph_layers)
        else:
            if self.version < 1 or glyph.glyph_name not in self.colrv1_glyphs:
                raise NotImplementedError(
                    f"No COLRv0 layers and no COLRv1 paint found for '{glyph.glyph_name}'."
                )
            img = self.draw_glyph_colrv1(glyph.glyph_name)
        img.transform = Transform.scaling(self.scale, -self.scale)
        output_stream = self.fpdf.draw_vector_glyph(img, self)
        glyph.glyph = f"{round(w * self.scale)} 0 d0\n" "q\n" f"{output_stream}\n" "Q"
        glyph.glyph_width = w

    def get_color(self, color_index: int, alpha=1) -> DeviceRGB:
        if color_index == 0xFFFF:
            # Palette entry 0xFFFF requests the application text foreground color.
            text_color = getattr(self.fpdf, "text_color", DeviceGray(0))
            if isinstance(text_color, DeviceRGB):
                r, g, b = text_color.r, text_color.g, text_color.b
                a = 1.0 if text_color.a is None else text_color.a
            elif isinstance(text_color, DeviceGray):
                r = g = b = text_color.g
                a = 1.0 if text_color.a is None else text_color.a
            elif isinstance(text_color, DeviceCMYK):
                c, m, y, k = text_color.c, text_color.m, text_color.y, text_color.k
                r = 1.0 - min(1.0, c + k)
                g = 1.0 - min(1.0, m + k)
                b = 1.0 - min(1.0, y + k)
                a = 1.0 if text_color.a is None else text_color.a
            else:
                r = g = b = 0.0
                a = 1.0
        else:
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
            gc.add_item(item=path, _copy=False)
        return gc

    def draw_glyph_colrv1(self, glyph_name):
        gc = GraphicsContext()
        clip_path = self._build_clip_path(glyph_name)
        if clip_path is not None:
            gc.clipping_path = clip_path
        glyph = self.colrv1_glyphs[glyph_name]
        self.draw_colrv1_paint(
            paint=glyph.Paint,
            parent=gc,
            target_path=None,
            ctm=Transform.identity(),
            visited_glyphs=set(glyph_name),
        )
        return gc

    # pylint: disable=too-many-return-statements
    def draw_colrv1_paint(
        self,
        paint: Paint,
        parent: GraphicsContext,
        target_path: Optional[PaintedPath] = None,
        ctm: Optional[Transform] = None,
        visited_glyphs: Optional[set] = None,
    ) -> Tuple[GraphicsContext, Optional[PaintedPath]]:
        """
        Draw a COLRv1 Paint object into the given GraphicsContext.
        This is an implementation of the COLR version 1 rendering algorithm:
        https://learn.microsoft.com/en-us/typography/opentype/spec/colr#colr-version-1-rendering-algorithm
        """
        paint = self._unwrap_paint(paint)
        ctm: Transform = ctm or Transform.identity()

        if visited_glyphs is None:
            visited_glyphs = set()

        if paint.Format == PaintFormat.PaintColrLayers:
            layer_list = self.base_font.ttfont["COLR"].table.LayerList
            group = GraphicsContext()
            for layer in range(
                paint.FirstLayerIndex, paint.FirstLayerIndex + paint.NumLayers
            ):
                self.draw_colrv1_paint(
                    paint=layer_list.Paint[layer],
                    parent=group,
                    ctm=ctm,
                    visited_glyphs=visited_glyphs,
                )
            parent.add_item(item=group, _copy=False)
            return parent, target_path

        if paint.Format in (
            PaintFormat.PaintSolid,
            PaintFormat.PaintVarSolid,
        ):
            target_path = target_path or self.get_paint_surface()
            target_path.style.fill_color = self.get_color(
                color_index=paint.PaletteIndex, alpha=paint.Alpha
            )
            target_path.style.stroke_color = None
            target_path.style.paint_rule = PathPaintRule.FILL_NONZERO
            return parent, target_path

        if paint.Format == PaintFormat.PaintLinearGradient:
            stops = [
                (stop.StopOffset, self.get_color(stop.PaletteIndex, stop.Alpha))
                for stop in paint.ColorLine.ColorStop
            ]
            if paint.ColorLine.Extend == 2:  # REFLECT
                spread_method = GradientSpreadMethod.REFLECT
            elif paint.ColorLine.Extend == 1:  # REPEAT
                spread_method = GradientSpreadMethod.REPEAT
            else:  # PAD
                spread_method = GradientSpreadMethod.PAD
            gradient = shape_linear_gradient(
                paint.x0,
                paint.y0,
                paint.x1,
                paint.y1,
                stops,
            )
            target_path = target_path or self.get_paint_surface()
            target_path.style.fill_color = GradientPaint(
                gradient=gradient,
                units=GradientUnits.USER_SPACE_ON_USE,
                gradient_transform=ctm,
                apply_page_ctm=False,
                spread_method=spread_method,
            )
            target_path.style.stroke_color = None
            target_path.style.paint_rule = PathPaintRule.FILL_NONZERO
            return parent, target_path

        if paint.Format == PaintFormat.PaintRadialGradient:
            raw = [
                (cs.StopOffset, self.get_color(cs.PaletteIndex, cs.Alpha))
                for cs in paint.ColorLine.ColorStop
            ]
            t_min, t_max, norm_stops = _normalize_color_line(raw)
            c0 = (paint.x0, paint.y0)
            r0 = paint.r0
            c1 = (paint.x1, paint.y1)
            r1 = paint.r1
            (fx, fy) = _lerp_pt(c0, c1, t_min)
            (cx, cy) = _lerp_pt(c0, c1, t_max)
            fr = max(_lerp(r0, r1, t_min), 0.0)
            r = max(_lerp(r0, r1, t_max), 1e-6)
            if paint.ColorLine.Extend == 2:  # REFLECT
                spread_method = GradientSpreadMethod.REFLECT
            elif paint.ColorLine.Extend == 1:  # REPEAT
                spread_method = GradientSpreadMethod.REPEAT
            else:  # PAD
                spread_method = GradientSpreadMethod.PAD
            gradient = shape_radial_gradient(
                cx=cx,
                cy=cy,
                r=r,
                fx=fx,
                fy=fy,
                fr=fr,
                stops=norm_stops,
            )
            target_path = target_path or self.get_paint_surface()
            target_path.style.fill_color = GradientPaint(
                gradient=gradient,
                units=GradientUnits.USER_SPACE_ON_USE,
                gradient_transform=ctm,
                apply_page_ctm=False,
                spread_method=spread_method,
            )
            target_path.style.stroke_color = None
            target_path.style.paint_rule = PathPaintRule.FILL_NONZERO
            return parent, target_path

        if paint.Format == PaintFormat.PaintSweepGradient:  # 8
            stops = [
                (cs.StopOffset, self.get_color(cs.PaletteIndex, cs.Alpha))
                for cs in paint.ColorLine.ColorStop
            ]

            if paint.ColorLine.Extend == 2:  # REFLECT
                spread_method = GradientSpreadMethod.REFLECT
            elif paint.ColorLine.Extend == 1:  # REPEAT
                spread_method = GradientSpreadMethod.REPEAT
            else:
                spread_method = GradientSpreadMethod.PAD

            cx = paint.centerX
            cy = paint.centerY

            # COLRv1 defines sweep angles clockwise from the positive X axis.
            # We build gradients in glyph space, which later undergoes a Y-axis flip
            # when emitted to PDF coordinates. To compensate, convert the COLR angles
            # directly to mathematical radians (counter-clockwise); the subsequent flip
            # restores the expected clockwise visual direction.
            start_angle, end_angle = self._sweep_angles(
                paint.startAngle, paint.endAngle
            )

            # Build a lazy sweep gradient object (bbox-resolved at emit time)
            gradient = SweepGradient(
                cx=cx,
                cy=cy,
                start_angle=start_angle,
                end_angle=end_angle,
                stops=stops,
                spread_method=spread_method,
                segments=None,
                inner_radius_factor=0.002,
            )

            target_path = target_path or self.get_paint_surface()
            target_path.style.fill_color = GradientPaint(
                gradient=gradient,
                units=GradientUnits.USER_SPACE_ON_USE,
                gradient_transform=ctm,
                apply_page_ctm=False,
                spread_method=spread_method,
            )
            target_path.style.stroke_color = None
            target_path.style.paint_rule = PathPaintRule.FILL_NONZERO
            return parent, target_path

        if paint.Format == PaintFormat.PaintGlyph:  # 10
            glyph_set = self.base_font.ttfont.getGlyphSet()
            clipping_path = ClippingPath()
            glyph_set[paint.Glyph].draw(GlyphPathPen(clipping_path, glyphSet=glyph_set))
            clipping_path.transform = (
                clipping_path.transform or Transform.identity()
            ) @ ctm

            if getattr(paint, "Paint", None) is None:
                return parent, None

            group = GraphicsContext()
            group.clipping_path = clipping_path

            group, surface_path = self.draw_colrv1_paint(
                paint=paint.Paint,
                parent=group,
                ctm=Transform.identity(),
                visited_glyphs=visited_glyphs,
            )
            if surface_path is not None:
                group.add_item(item=surface_path, _copy=False)
            parent.add_item(item=group, _copy=False)
            return parent, None

        if paint.Format == PaintFormat.PaintColrGlyph:
            ref = getattr(paint, "Glyph", None) or getattr(paint, "GlyphID", None)
            if isinstance(ref, int):
                ref_name = self.base_font.ttfont.getGlyphName(ref)
            else:
                ref_name = ref
            if ref_name in visited_glyphs:
                LOGGER.warning("Skipping recursive COLR glyph reference '%s'", ref_name)
                return parent, target_path  # nothing to draw
            rec = self.colrv1_glyphs.get(ref_name)
            if rec is None or getattr(rec, "Paint", None) is None:
                return parent, target_path  # nothing to draw

            visited_glyphs.add(ref_name)
            try:
                group = GraphicsContext()
                clip_path = self._build_clip_path(ref_name)
                if clip_path is not None:
                    group.clipping_path = clip_path
                self.draw_colrv1_paint(
                    paint=rec.Paint,
                    parent=group,
                    ctm=ctm,
                    visited_glyphs=visited_glyphs,
                )
                parent.add_item(item=group, _copy=False)
            finally:
                visited_glyphs.remove(ref_name)
            return parent, target_path

        if paint.Format in (
            PaintFormat.PaintTransform,  # 12
            PaintFormat.PaintVarTransform,  # 13
            PaintFormat.PaintTranslate,  # 14
            PaintFormat.PaintVarTranslate,  # 15
            PaintFormat.PaintScale,  # 16
            PaintFormat.PaintVarScale,  # 17
            PaintFormat.PaintScaleAroundCenter,  # 18
            PaintFormat.PaintVarScaleAroundCenter,  # 19
            PaintFormat.PaintScaleUniform,  # 20
            PaintFormat.PaintVarScaleUniform,  # 21
            PaintFormat.PaintScaleUniformAroundCenter,  # 22
            PaintFormat.PaintVarScaleUniformAroundCenter,  # 23
            PaintFormat.PaintRotate,  # 24
            PaintFormat.PaintVarRotate,  # 25
            PaintFormat.PaintRotateAroundCenter,  # 26
            PaintFormat.PaintVarRotateAroundCenter,  # 27
            PaintFormat.PaintSkew,  # 28
            PaintFormat.PaintVarSkew,  # 29
            PaintFormat.PaintSkewAroundCenter,  # 30
            PaintFormat.PaintVarSkewAroundCenter,  # 31
        ):
            transform = self._transform_from_paint(paint)
            new_ctm = ctm @ transform
            return self.draw_colrv1_paint(
                paint=paint.Paint,
                parent=parent,
                target_path=target_path,
                ctm=new_ctm,
                visited_glyphs=visited_glyphs,
            )

        if paint.Format in (
            PaintFormat.PaintVarLinearGradient,  # 5
            PaintFormat.PaintVarRadialGradient,  # 7
            PaintFormat.PaintVarSweepGradient,
        ):  # 9
            raise NotImplementedError("Variable fonts are not yet supported.")

        if paint.Format == PaintFormat.PaintComposite:  # 32
            backdrop_node = GraphicsContext()
            _, backdrop_path = self.draw_colrv1_paint(
                paint=paint.BackdropPaint,
                parent=backdrop_node,
                ctm=ctm,
                visited_glyphs=visited_glyphs,
            )
            if backdrop_path is not None:
                backdrop_node.add_item(item=backdrop_path, _copy=False)

            source_node = GraphicsContext()
            _, source_path = self.draw_colrv1_paint(
                paint=paint.SourcePaint,
                parent=source_node,
                ctm=ctm,
                visited_glyphs=visited_glyphs,
            )
            if source_path is not None:
                source_node.add_item(item=source_path, _copy=False)

            composite_type, composite_mode = self.get_composite_mode(
                paint.CompositeMode
            )
            if composite_type == "Blend":
                parent.add_item(
                    item=PaintBlendComposite(
                        backdrop=backdrop_node,
                        source=source_node,
                        blend_mode=composite_mode,
                    ),
                    _copy=False,
                )
            elif composite_type == "Compositing":
                composite_node = PaintComposite(
                    backdrop=backdrop_node, source=source_node, operation=composite_mode
                )
                parent.add_item(item=composite_node, _copy=False)
            else:
                raise ValueError("Composite operation not supported - {composite_type}")
            return parent, None

        raise NotImplementedError(f"Unknown PaintFormat: {paint.Format}")

    @classmethod
    def _sweep_angles(cls, start_deg: float, end_deg: float) -> Tuple[float, float]:
        start_norm = math.fmod(start_deg, 360.0)
        if start_norm < 0.0:
            start_norm += 360.0
        span_deg = math.fmod(end_deg - start_deg, 360.0)
        if span_deg <= 0.0:
            span_deg += 360.0
        start_rad = math.radians(start_norm)
        end_rad = start_rad + math.radians(span_deg)
        return start_rad, end_rad

    @classmethod
    def _transform_from_paint(cls, paint: Paint) -> Transform:
        paint_format = paint.Format
        if paint_format in (PaintFormat.PaintTransform, PaintFormat.PaintVarTransform):
            transform = paint.Transform
            return Transform(
                transform.xx,
                transform.yx,
                transform.xy,
                transform.yy,
                transform.dx,
                transform.dy,
            )
        if paint_format in (PaintFormat.PaintTranslate, PaintFormat.PaintVarTranslate):
            return Transform.translation(paint.dx, paint.dy)
        if paint_format in (PaintFormat.PaintScale, PaintFormat.PaintVarScale):
            return Transform.scaling(paint.scaleX, paint.scaleY)
        if paint_format in (
            PaintFormat.PaintScaleAroundCenter,
            PaintFormat.PaintVarScaleAroundCenter,
        ):
            return Transform.scaling(paint.scaleX, paint.scaleY).about(
                paint.centerX, paint.centerY
            )
        if paint_format in (
            PaintFormat.PaintScaleUniform,
            PaintFormat.PaintVarScaleUniform,
        ):
            return Transform.scaling(paint.scale, paint.scale)
        if paint_format in (
            PaintFormat.PaintScaleUniformAroundCenter,
            PaintFormat.PaintVarScaleUniformAroundCenter,
        ):
            return Transform.scaling(paint.scale, paint.scale).about(
                paint.centerX, paint.centerY
            )
        if paint_format in (PaintFormat.PaintRotate, PaintFormat.PaintVarRotate):
            return Transform.rotation_d(paint.angle)
        if paint_format in (
            PaintFormat.PaintRotateAroundCenter,
            PaintFormat.PaintVarRotateAroundCenter,
        ):
            return Transform.rotation_d(paint.angle).about(paint.centerX, paint.centerY)
        if paint_format in (PaintFormat.PaintSkew, PaintFormat.PaintVarSkew):
            return Transform.skewing_d(-paint.xSkewAngle, paint.ySkewAngle)
        if paint_format in (
            PaintFormat.PaintSkewAroundCenter,
            PaintFormat.PaintVarSkewAroundCenter,
        ):
            return Transform.skewing_d(-paint.xSkewAngle, paint.ySkewAngle).about(
                paint.centerX, paint.centerY
            )
        raise NotImplementedError(f"Transform not implemented for {format}")

    def get_paint_surface(self) -> PaintedPath:
        """
        Creates a surface representing the whole glyph area for actions that require
        painting an infinite surface and clipping to a geometry path
        """
        paint_surface = PaintedPath()
        surface_bbox = self.metric_bbox()
        paint_surface.rectangle(
            x=surface_bbox.x0,
            y=surface_bbox.y0,
            w=surface_bbox.width,
            h=surface_bbox.height,
        )
        return paint_surface

    @classmethod
    def get_composite_mode(cls, composite_mode: CompositeMode):
        """Get the FPDF BlendMode for a given CompositeMode."""

        map_compositing_operation = {
            CompositeMode.SRC: CompositingOperation.SOURCE,
            CompositeMode.DEST: CompositingOperation.DESTINATION,
            CompositeMode.CLEAR: CompositingOperation.CLEAR,
            CompositeMode.SRC_OVER: CompositingOperation.SOURCE_OVER,
            CompositeMode.DEST_OVER: CompositingOperation.DESTINATION_OVER,
            CompositeMode.SRC_IN: CompositingOperation.SOURCE_IN,
            CompositeMode.DEST_IN: CompositingOperation.DESTINATION_IN,
            CompositeMode.SRC_OUT: CompositingOperation.SOURCE_OUT,
            CompositeMode.DEST_OUT: CompositingOperation.DESTINATION_OUT,
            CompositeMode.SRC_ATOP: CompositingOperation.SOURCE_ATOP,
            CompositeMode.DEST_ATOP: CompositingOperation.DESTINATION_ATOP,
            CompositeMode.XOR: CompositingOperation.XOR,
        }

        compositing_operation = map_compositing_operation.get(composite_mode, None)
        if compositing_operation is not None:
            return ("Compositing", compositing_operation)

        map_blend_mode = {
            CompositeMode.PLUS: BlendMode.SCREEN,  # approximation
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
        blend_mode = map_blend_mode.get(composite_mode, None)
        if blend_mode is not None:
            return ("Blend", blend_mode)

        raise NotImplementedError(f"Unknown composite mode: {composite_mode}")

    def _unwrap_paint(self, paint: Paint) -> Paint:
        mapped_format = PAINT_VAR_MAPPING.get(paint.Format)
        if mapped_format is None or self.colr_var_instancer is None:
            return paint
        return VarTableWrapper(
            paint,
            self.colr_var_instancer,
            self.colr_var_index_map,
            format_override=mapped_format,
        )

    def _build_clip_path(self, glyph_name: str) -> Optional[ClippingPath]:
        clip_box = self.colrv1_clip_boxes.get(glyph_name)
        if clip_box is None:
            return None
        x_min, y_min, x_max, y_max = clip_box
        clip_path = ClippingPath()
        clip_path.move_to(x_min, y_min)
        clip_path.rectangle(x_min, y_min, x_max - x_min, y_max - y_min)
        return clip_path

    def _resolve_clip_box(self, clip) -> Optional[tuple]:
        if clip is None:
            return None
        if (
            getattr(clip, "Format", None) == ClipBoxFormat.Variable
            and self.colr_var_instancer is not None
        ):
            clip = VarTableWrapper(
                clip,
                self.colr_var_instancer,
                self.colr_var_index_map,
            )
        if hasattr(clip, "xMin") and hasattr(clip, "xMax"):
            return (clip.xMin, clip.yMin, clip.xMax, clip.yMax)
        LOGGER.debug("Unsupported COLRv1 clip format for clip box")
        return None


class VarTableWrapper:
    def __init__(
        self,
        wrapped,
        instancer: VarStoreInstancer,
        var_index_map=None,
        format_override: Optional[int] = None,
    ):
        assert not isinstance(wrapped, VarTableWrapper)
        self._wrapped = wrapped
        self._instancer = instancer
        self._var_index_map = var_index_map
        self._format_override = format_override
        self._var_attrs = {
            attr: idx for idx, attr in enumerate(wrapped.getVariableAttrs())
        }

    def __repr__(self):
        return f"VarTableWrapper({self._wrapped!r})"

    def _get_var_index_for_attr(self, attr_name):
        offset = self._var_attrs.get(attr_name)
        if offset is None:
            return None
        base_index = self._wrapped.VarIndexBase
        if base_index == 0xFFFFFFFF:
            return base_index
        var_idx = base_index + offset
        if self._var_index_map is not None:
            try:
                var_idx = self._var_index_map[var_idx]
            except IndexError:
                pass
        return var_idx

    def _get_delta_for_attr(self, attr_name, var_idx):
        delta = self._instancer[var_idx]
        converter = self._wrapped.getConverterByName(attr_name)
        if hasattr(converter, "fromInt"):
            delta = converter.fromInt(delta)
        return delta

    def __getattr__(self, attr_name):
        if attr_name == "Format" and self._format_override is not None:
            return self._format_override

        value = getattr(self._wrapped, attr_name)

        var_idx = self._get_var_index_for_attr(attr_name)
        if var_idx is not None:
            if var_idx < 0xFFFFFFFF:
                value += self._get_delta_for_attr(attr_name, var_idx)
        elif isinstance(value, (VarAffine2x3, VarColorLine)):
            value = VarTableWrapper(value, self._instancer, self._var_index_map)
        elif (
            isinstance(value, (list, UserList))
            and value
            and isinstance(value[0], VarColorStop)
        ):
            value = [
                VarTableWrapper(item, self._instancer, self._var_index_map)
                for item in value
            ]

        return value


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
        _, _, info = self.fpdf.preload_glyph_image(glyph_image_bytes=bio)
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
        _, _, info = self.fpdf.preload_glyph_image(glyph_image_bytes=bio)
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


def get_color_font_object(
    fpdf: "FPDF", base_font: "TTFFont", palette_index: int = 0
) -> Union[Type3Font, None]:
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
        return COLRFont(fpdf, base_font, palette_index)
    if "SVG " in base_font.ttfont:
        LOGGER.debug("Font %s is a SVG color font", base_font.name)
        return SVGColorFont(fpdf, base_font)
    if "sbix" in base_font.ttfont:
        LOGGER.debug("Font %s is a SBIX color font", base_font.name)
        return SBIXColorFont(fpdf, base_font)
    return None


def _lerp(a, b, t):
    return a + (b - a) * t


def _lerp_pt(p0, p1, t):
    return (_lerp(p0[0], p1[0], t), _lerp(p0[1], p1[1], t))


def _normalize_color_line(stops):
    # stops: list[(offset, DeviceRGB)]
    s = sorted(((max(0.0, min(1.0, t)), c) for t, c in stops), key=lambda x: x[0])
    # collapse identical offsets (last wins per spec-ish behavior)
    out = []
    for t, c in s:
        if out and abs(out[-1][0] - t) < 1e-6:
            out[-1] = (t, c)
        else:
            out.append((t, c))
    t_min, t_max = out[0][0], out[-1][0]
    if t_max - t_min < 1e-6:
        # degenerate: treat as solid
        return t_min, t_max, [(0.0, out[-1][1])]
    scale = 1.0 / (t_max - t_min)
    renorm = [((t - t_min) * scale, c) for (t, c) in out]
    return t_min, t_max, renorm
