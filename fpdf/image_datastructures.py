# pyright: reportUnknownVariableType=false
from dataclasses import dataclass, field
from typing import Any, Literal, TypeAlias, TypeGuard, TypedDict

ImageFilter: TypeAlias = Literal[
    "AUTO",
    "FlateDecode",
    "DCTDecode",
    "JPXDecode",
    "LZWDecode",
    "CCITTFaxDecode",
]


class ImageInfo(TypedDict):
    """Information about an image used in the PDF document (base shape)."""

    w: float
    h: float
    rendered_width: float
    rendered_height: float


class RasterImageInfo(ImageInfo):
    """Information about a raster image used in the PDF document."""

    data: bytes
    cs: str
    dpn: int
    bpc: int
    f: ImageFilter
    dp: str
    inverted: bool
    iccp: bytes | None
    iccp_i: int | None
    pal: bytes | None
    smask: bytes | None
    i: int
    usages: int
    obj_id: int | None


class VectorImageInfo(ImageInfo):
    """Information about a vector image used in the PDF document."""

    data: Any


def is_vector_image_info(
    info: RasterImageInfo | VectorImageInfo,
) -> TypeGuard[VectorImageInfo]:
    return "cs" not in info


def scale_image_to_box(
    info: ImageInfo, x: float, y: float, w: float, h: float
) -> tuple[float, float, float, float]:
    """
    Make an image fit within a bounding box, maintaining its proportions.
    In the reduced dimension it will be centered within the available space.
    """
    img_w = info["w"]
    img_h = info["h"]
    ratio = img_w / img_h
    if h * ratio < w:
        new_w = h * ratio
        new_h = h
        x += (w - new_w) / 2
    else:  # => too wide, limiting width:
        new_h = w / ratio
        new_w = w
        y += (h - new_h) / 2
    return x, y, new_w, new_h


def raster_image_size_in_document_units(
    info: RasterImageInfo, w: float, h: float, scale: float = 1
) -> tuple[float, float]:
    img_w = info["w"]
    img_h = info["h"]
    if w == 0 and h == 0:  # Put image at 72 dpi
        w = img_w / scale
        h = img_h / scale
    elif w == 0:
        w = h * img_w / img_h
    elif h == 0:
        h = w * img_h / img_w
    return w, h


def update_raster_image_info(info: RasterImageInfo, other: RasterImageInfo) -> None:
    """Update cached image payload and pixel metadata from another parsed image info."""
    info["data"] = other["data"]
    info["w"] = other["w"]
    info["h"] = other["h"]
    info["cs"] = other["cs"]
    info["iccp"] = other["iccp"]
    info["dpn"] = other["dpn"]
    info["bpc"] = other["bpc"]
    info["f"] = other["f"]
    info["inverted"] = other["inverted"]
    info["dp"] = other["dp"]
    info["smask"] = other["smask"]
    info["pal"] = other["pal"]


@dataclass
class ImageCache:
    # Map image identifiers to cached raster image info
    images: dict[str, RasterImageInfo] = field(default_factory=dict)
    # Map icc profiles (bytes) to their index (number)
    icc_profiles: dict[bytes, int] = field(default_factory=dict)
    # Must be one of SUPPORTED_IMAGE_FILTERS values
    image_filter: ImageFilter = "AUTO"

    def reset_usages(self) -> None:
        for img in self.images.values():
            img["usages"] = 0
