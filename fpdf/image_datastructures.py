# pyright: reportUnknownVariableType=false
from dataclasses import dataclass, field
from typing import Literal, TypeAlias, cast

ImageFilter: TypeAlias = Literal[
    "AUTO",
    "FlateDecode",
    "DCTDecode",
    "JPXDecode",
    "LZWDecode",
    "CCITTFaxDecode",
]


class ImageInfo(dict[str, object]):
    """Information about an image used in the PDF document (base class).
    We subclass this to distinguish between raster and vector images."""

    @property
    def width(self) -> float:
        "Intrinsic image width"
        return cast(float, self["w"])

    @property
    def height(self) -> float:
        "Intrinsic image height"
        return cast(float, self["h"])

    @property
    def rendered_width(self) -> float:
        "Only available if the image has been placed on the document"
        return cast(float, self["rendered_width"])

    @property
    def rendered_height(self) -> float:
        "Only available if the image has been placed on the document"
        return cast(float, self["rendered_height"])

    def __str__(self) -> str:
        d = {
            k: ("..." if k in ("data", "iccp", "smask") else v) for k, v in self.items()
        }
        return f"self.__class__.__name__({d})"

    def scale_inside_box(
        self, x: float, y: float, w: float, h: float
    ) -> tuple[float, float, float, float]:
        """
        Make an image fit within a bounding box, maintaining its proportions.
        In the reduced dimension it will be centered within the available space.
        """
        img_w: float = self["w"]  # type: ignore
        img_h: float = self["h"]  # type: ignore
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


class RasterImageInfo(ImageInfo):
    "Information about a raster image used in the PDF document"

    def size_in_document_units(
        self, w: float, h: float, scale: float = 1
    ) -> tuple[float, float]:
        img_w: float = self["w"]  # type: ignore
        img_h: float = self["h"]  # type: ignore
        if w == 0 and h == 0:  # Put image at 72 dpi
            w = img_w / scale
            h = img_h / scale
        elif w == 0:
            w = h * img_w / img_h
        elif h == 0:
            h = w * img_h / img_w
        return w, h


class VectorImageInfo(ImageInfo):
    "Information about a vector image used in the PDF document"

    # pass


@dataclass
class ImageCache:
    # Map image identifiers to dicts describing raster or vector images
    images: dict[str, RasterImageInfo | VectorImageInfo] = field(default_factory=dict)
    # Map icc profiles (bytes) to their index (number)
    icc_profiles: dict[bytes, int] = field(default_factory=dict)
    # Must be one of SUPPORTED_IMAGE_FILTERS values
    image_filter: ImageFilter = "AUTO"

    def reset_usages(self) -> None:
        for img in self.images.values():
            img["usages"] = 0
