import logging

from typing import List, Tuple, TYPE_CHECKING
from io import BytesIO
from fontTools.ttLib.tables.BitmapGlyphMetrics import BigGlyphMetrics, SmallGlyphMetrics

from .image_datastructures import RasterImageInfo, VectorImageInfo



if TYPE_CHECKING:
    from .fpdf import FPDF
    from .fonts import TTFFont


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

    @classmethod
    def get_notdef_glyph(cls, glyph_id) -> Type3FontGlyph:
        notdef = Type3FontGlyph()
        notdef.glyph_id = glyph_id
        notdef.unicode = 0
        notdef.glyph_name = ".notdef"
        notdef.glyph_width = 0
        notdef.glyph = "0 0 d0"
        return notdef

    def get_space_glyph(self, glyph_id) -> Type3FontGlyph:
        space = Type3FontGlyph()
        space.glyph_id = glyph_id
        space.unicode = 0x20
        space.glyph_name = "space"
        space.glyph_width = self.base_font.desc.missing_width
        space.glyph = f"{space.glyph_width} 0 d0"
        return space

    def load_glyphs(self):
        for glyph, char_id in self.base_font.subset.items():
            if not self.glyph_exists(glyph.glyph_name):
                # print(f"notdef id {char_id} name {glyph.glyph_name}")
                if char_id == 0x20:
                    self.glyphs.append(self.get_space_glyph(char_id))
                else:
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

    def load_glyph_image(self, glyph: Type3FontGlyph):
        x_min, y_min, x_max, y_max, _, glyph_bitmap = self.read_glyph_data(
            glyph.glyph_name
        )
        bio = BytesIO(glyph_bitmap)
        bio.seek(0)
        _, img, info = self.fpdf.preload_image(bio, None)
        if isinstance(info, VectorImageInfo):
            w = round(
                self.base_font.ttfont["hmtx"].metrics[glyph.glyph_name][0] * self.scale
                + 0.001
            )
            # _, _, path = img.transform_to_rect_viewport(self.fpdf.k, None, None, align_viewbox=False)
            _, _, path = img.transform_to_page_viewport(
                pdf=self.fpdf, align_viewbox=False
            )
            output_stream = self.fpdf.draw_vector_glyph(path, self)
            glyph.glyph = (
                f"{w} 0 d0\n"
                "q\n"
                # f"1 0 0 1 {x_min * self.scale} {y_min * self.scale} cm\n"
                f"{output_stream}\n"
                "Q"
            )
            glyph.glyph_width = x_max
        elif isinstance(info, RasterImageInfo):
            glyph.glyph = (
                f"{x_max * self.scale} 0 d0\n"
                "q\n"
                f"{x_max * self.scale} 0 0 {(-y_min + y_max) * self.scale} {x_min * self.scale} {y_min * self.scale} cm\n"
                f"/I{info['i']} Do\nQ"
            )
            glyph.glyph_width = x_max
            self.images_used.add(info["i"])

    def glyph_exists(self, glyph_name: str) -> bool:
        raise NotImplementedError("Method must be implemented on child class")

    def read_glyph_data(self, glyph_name):
        raise NotImplementedError("Method must be implemented on child class")


class SVGColorFont(Type3Font):

    def glyph_exists(self, glyph_name):
        glyph_id = self.base_font.ttfont.getGlyphID(glyph_name)
        return any(
            svg_doc.startGlyphID <= glyph_id <= svg_doc.endGlyphID
            for svg_doc in self.base_font.ttfont["SVG "].docList
        )

    def read_glyph_data(self, glyph_name: str) -> BytesIO:
        glyph_id = self.base_font.ttfont.getGlyphID(glyph_name)
        glyph_svg_data = None
        for svg_doc in self.base_font.ttfont["SVG "].docList:
            if svg_doc.startGlyphID <= glyph_id <= svg_doc.endGlyphID:
                glyph_svg_data = svg_doc.data.encode("utf-8")

        x_min, y_min, x_max, y_max = self.get_glyph_bounds(glyph_name)
        x_min = round(x_min)  # * self.upem / ppem)
        y_min = round(y_min)  # * self.upem / ppem)
        x_max = round(x_max)  # * self.upem / ppem)
        y_max = round(y_max)  # * self.upem / ppem)

        return x_min, y_min, x_max, y_max, x_max, glyph_svg_data

    def get_glyph_bounds(self, glyph_name: str) -> Tuple[int, int, int, int]:
        glyph_id = self.base_font.ttfont.getGlyphID(glyph_name)
        x, y, w, h = self.base_font.hbfont.get_glyph_extents(glyph_id)
        # convert from HB's x/y_bearing + extents to xMin, yMin, xMax, yMax
        y += h
        h = -h
        w += x
        h += y
        # print(f"harfbuzz values: {x}, {y}, {w}, {h}")
        return x, y, w, h


class CBDTColorFont(Type3Font):

    # Only looking at the first strike - Need to look all strikes available on the CBLC table first?

    def glyph_exists(self, glyph_name):
        return glyph_name in self.base_font.ttfont["CBDT"].strikeData[0]

    def read_glyph_data(self, glyph_name):
        ppem = self.base_font.ttfont["CBLC"].strikes[0].bitmapSizeTable.ppemX
        glyph = self.base_font.ttfont["CBDT"].strikeData[0][glyph_name]
        glyph_bitmap = glyph.data[9:]
        metrics = glyph.metrics
        if isinstance(metrics, SmallGlyphMetrics):
            x_min = round(metrics.BearingX * self.upem / ppem)
            y_min = round((metrics.BearingY - metrics.height) * self.upem / ppem)
            x_max = round(metrics.width * self.upem / ppem)
            y_max = round(metrics.BearingY * self.upem / ppem)
            advance = round(metrics.Advance * self.upem / ppem)
        elif isinstance(metrics, BigGlyphMetrics):
            x_min = round(metrics.horiBearingX * self.upem / ppem)
            y_min = round((metrics.horiBearingY - metrics.height) * self.upem / ppem)
            x_max = round(metrics.width * self.upem / ppem)
            y_max = round(metrics.horiBearingY * self.upem / ppem)
            advance = round(metrics.horiAdvance * self.upem / ppem)
        else:  # fallback scenario: use font bounding box
            x_min = self.base_font.ttfont["head"].xMin
            y_min = self.base_font.ttfont["head"].yNin
            x_max = self.base_font.ttfont["head"].xMax
            y_max = self.base_font.ttfont["head"].yMax
            advance = self.base_font.ttfont["hmtx"].metrics[".notdef"][0]
        return x_min, y_min, x_max, y_max, advance, glyph_bitmap


class SBIXColorFont(Type3Font):

    def glyph_exists(self, glyph_name):
        ppem = list(self.base_font.ttfont["sbix"].strikes.keys())[0]
        return (
            self.base_font.ttfont["sbix"].strikes[ppem].glyphs.get(glyph_name.upper())
        )

    def read_glyph_data(self, glyph_name: str) -> BytesIO:
        # how to select the ideal ppm?
        # print(self.base_font.ttfont["sbix"].strikes.keys())
        ppem = list(self.base_font.ttfont["sbix"].strikes.keys())[0]
        # print(f"ppem {ppem}")
        # print(f'unitsPerEm {self.base_font.ttfont["head"].unitsPerEm}')
        # print(
        #    f'xMin {self.base_font.ttfont["head"].xMin} xMax {self.base_font.ttfont["head"].xMax}'
        # )
        # print(
        #    f'yMin {self.base_font.ttfont["head"].yMin} yMax {self.base_font.ttfont["head"].yMax}'
        # )
        # print(f'glyphDataFormat {self.base_font.ttfont["head"].glyphDataFormat}')

        glyph = self.base_font.ttfont["sbix"].strikes[ppem].glyphs.get(glyph_name)
        if not glyph:
            return None

        if glyph.graphicType == "dupe":
            return None
            # to do - waiting for an example to test
            # dupe_char = font.getBestCmap()[glyph.imageData]
            # return self.get_color_glyph(dupe_char)

        x_min, y_min, x_max, y_max = self.get_glyph_bounds(glyph_name)
        x_min = round(x_min * self.upem / ppem)
        y_min = round(y_min * self.upem / ppem)
        x_max = round(x_max * self.upem / ppem)
        y_max = round(y_max * self.upem / ppem)

        # graphic type 'pdf' or 'mask' are not supported
        return x_min, y_min, x_max, y_max, x_max, glyph.imageData

    def get_glyph_bounds(self, glyph_name: str) -> Tuple[int, int, int, int]:
        glyph_id = self.base_font.ttfont.getGlyphID(glyph_name)
        x, y, w, h = self.base_font.hbfont.get_glyph_extents(glyph_id)
        # convert from HB's x/y_bearing + extents to xMin, yMin, xMax, yMax
        y += h
        h = -h
        w += x
        h += y
        # print(f"harfbuzz values: {x}, {y}, {w}, {h}")
        return x, y, w, h


# pylint: disable=too-many-return-statements
def get_color_font_object(fpdf: "FPDF", base_font: "TTFFont") -> Type3Font:
    if "CBDT" in base_font.ttfont:
        LOGGER.warning("Font %s is a CBLC+CBDT color font", base_font.name)
        return CBDTColorFont(fpdf, base_font)
    if "EBDT" in base_font.ttfont:
        LOGGER.warning("%s - EBLC+EBDT color font is not supported yet", base_font.name)
        return None
    if "COLR" in base_font.ttfont:
        if base_font.ttfont["COLR"].version == 0:
            LOGGER.warning("Font %s is a COLRv0 color font", base_font.name)
            return None
        LOGGER.warning("Font %s is a COLRv1 color font", base_font.name)
        return None
    if "SVG " in base_font.ttfont:
        LOGGER.warning("Font %s is a SVG color font", base_font.name)
        return SVGColorFont(fpdf, base_font)
    if "sbix" in base_font.ttfont:
        LOGGER.warning("Font %s is a SBIX color font", base_font.name)
        return SBIXColorFont(fpdf, base_font)
    return None
