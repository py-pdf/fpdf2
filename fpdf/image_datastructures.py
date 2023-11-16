from dataclasses import dataclass, field
from typing import Dict

from .enums import Align


class ImageInfo(dict):
    """Information about an image used in the PDF document (base class).
    We subclass this to distinguish between raster and vector images."""

    @property
    def width(self):
        "Intrinsic image width"
        return self["w"]

    @property
    def height(self):
        "Intrinsic image height"
        return self["h"]

    @property
    def rendered_width(self):
        "Only available if the image has been placed on the document"
        return self["rendered_width"]

    @property
    def rendered_height(self):
        "Only available if the image has been placed on the document"
        return self["rendered_height"]

    def __str__(self):
        d = {k: ("..." if k in ("data", "smask") else v) for k, v in self.items()}
        return f"self.__class__.__name__({d})"

    def scale_inside_box(self, x, y, w, h):
        """
        Make an image fit within a bounding box, maintaining its proportions.
        In the reduced dimension it will be centered within the available space.
        """
        ratio = self.width / self.height
        if h * ratio < w:
            new_w = h * ratio
            new_h = h
            x += (w - new_w) / 2
        else:  # => too wide, limiting width:
            new_h = w / ratio
            new_w = w
            y += (h - new_h) / 2
        return x, y, new_w, new_h

    @staticmethod
    def x_by_align(x, w, pdf, keep_aspect_ratio):
        if keep_aspect_ratio:
            raise ValueError(
                "FPDF.image(): 'keep_aspect_ratio' cannot be used with an enum value provided to `x`"
            )
        x = Align.coerce(x)
        if x == Align.C:
            return (pdf.w - w) / 2
        if x == Align.R:
            return pdf.w - w - pdf.r_margin
        if x == Align.L:
            return pdf.l_margin
        raise ValueError(f"Unsupported 'x' value passed to .image(): {x}")


class RasterImageInfo(ImageInfo):
    "Information about a raster image used in the PDF document"

    def size_in_document_units(self, w, h, scale=1):
        if w == 0 and h == 0:  # Put image at 72 dpi
            w = self["w"] / scale
            h = self["h"] / scale
        elif w == 0:
            w = h * self["w"] / self["h"]
        elif h == 0:
            h = w * self["h"] / self["w"]
        return w, h


class VectorImageInfo(ImageInfo):
    "Information about a vector image used in the PDF document"
    # pass


@dataclass
class ImageCache:
    # Map image identifiers to dicts describing the raster images
    images: Dict[str, dict] = field(default_factory=dict)
    # Map icc profiles (bytes) to their index (number)
    icc_profiles: Dict[bytes, int] = field(default_factory=dict)
    # Must be one of SUPPORTED_IMAGE_FILTERS values
    image_filter: str = "AUTO"

    def reset_usages(self):
        for img in self.images.values():
            img["usages"] = 0
