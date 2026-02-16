# pyright: reportUnknownVariableType=false
from dataclasses import dataclass, field
from typing import Any, Literal, TypeAlias, TypeGuard, TypedDict

try:
    from typing import NotRequired
except ImportError:  # pragma: no cover - py<3.11 fallback
    from typing_extensions import NotRequired

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
    rendered_width: NotRequired[float]
    rendered_height: NotRequired[float]


class RasterImageInfo(ImageInfo):
    """Information about a raster image used in the PDF document."""

    data: bytes
    cs: str
    dpn: int
    bpc: int
    f: ImageFilter
    dp: str
    inverted: bool
    i: int
    usages: int
    iccp: NotRequired[bytes | None]
    iccp_i: NotRequired[int | None]
    pal: NotRequired[bytes | None]
    smask: NotRequired[bytes | None]
    obj_id: NotRequired[int | None]
    image_mask: NotRequired[bool]
    decode: NotRequired[str]


class ImageXObjectInfo(TypedDict):
    """Subset of image info fields used to build an image XObject."""

    w: float
    h: float
    cs: str
    bpc: int
    f: ImageFilter
    dp: str
    data: bytes
    iccp_i: NotRequired[int | None]
    pal: NotRequired[bytes | None]
    inverted: NotRequired[bool]
    smask: NotRequired[bytes | None]
    image_mask: NotRequired[bool]
    decode: NotRequired[str]
    obj_id: NotRequired[int | None]


class VectorImageInfo(ImageInfo):
    """Information about a vector image used in the PDF document."""

    data: NotRequired[Any]


def is_vector_image_info(
    info: RasterImageInfo | VectorImageInfo,
) -> TypeGuard[VectorImageInfo]:
    return "cs" not in info


def scale_inside_box(
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


def size_in_document_units(
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


@dataclass
class ImageCache:
    # Map image identifiers to dicts describing raster images
    images: dict[str, RasterImageInfo] = field(default_factory=dict)
    # Map icc profiles (bytes) to their index (number)
    icc_profiles: dict[bytes, int] = field(default_factory=dict)
    # Must be one of SUPPORTED_IMAGE_FILTERS values
    image_filter: ImageFilter = "AUTO"

    def reset_usages(self) -> None:
        for img in self.images.values():
            img["usages"] = 0
