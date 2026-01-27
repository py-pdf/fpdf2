# pyright: reportUnknownVariableType=false
from dataclasses import dataclass, field, fields
from typing import Any, Literal, Optional, TypeAlias, cast

ImageFilter: TypeAlias = Literal[
    "AUTO",
    "FlateDecode",
    "DCTDecode",
    "JPXDecode",
    "LZWDecode",
    "CCITTFaxDecode",
]


class LegacyImageInfo(dict[str, Any]):
    """Dict-like image info with legacy attribute access."""

    __slots__ = ("_source",)

    def __init__(self, source: "ImageInfo", initial: Optional[dict[str, Any]] = None):
        super().__init__(initial or {})
        self._source = source

    def __getitem__(self, key: str) -> Any:
        source = self._source
        if key == "w":
            return source.width
        if key == "h":
            return source.height
        if key == "rendered_width":
            return source.rendered_width
        if key == "rendered_height":
            return source.rendered_height
        if key == "usages":
            if isinstance(source, RasterImageInfo):
                return source.usage_count
        return super().__getitem__(key)

    def __setitem__(self, key: str, value: Any) -> None:
        source = self._source
        if key == "w":
            source.width = cast(float, value)
        elif key == "h":
            source.height = cast(float, value)
        elif key == "rendered_width":
            source.rendered_width = cast(float, value)
        elif key == "rendered_height":
            source.rendered_height = cast(float, value)
        elif key == "usages" and isinstance(source, RasterImageInfo):
            source.usage_count = cast(int, value)
        super().__setitem__(key, value)

    @property
    def width(self) -> float:
        return cast(float, self["w"])

    @width.setter
    def width(self, value: float) -> None:
        self["w"] = value

    @property
    def height(self) -> float:
        return cast(float, self["h"])

    @height.setter
    def height(self, value: float) -> None:
        self["h"] = value

    @property
    def rendered_width(self) -> float:
        return cast(float, self["rendered_width"])

    @rendered_width.setter
    def rendered_width(self, value: float) -> None:
        self["rendered_width"] = value

    @property
    def rendered_height(self) -> float:
        return cast(float, self["rendered_height"])

    @rendered_height.setter
    def rendered_height(self, value: float) -> None:
        self["rendered_height"] = value


@dataclass(slots=True)
class ImageInfo:
    """Information about an image used in the PDF document (base class)."""

    width: float = 0.0
    height: float = 0.0
    rendered_width: float = 0.0
    rendered_height: float = 0.0
    legacy_info: "LegacyImageInfo" = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.legacy_info = LegacyImageInfo(
            self,
            {
                "w": self.width,
                "h": self.height,
                "rendered_width": self.rendered_width,
                "rendered_height": self.rendered_height,
            },
        )

    def __str__(self) -> str:
        redacted = {"data", "icc_profile", "soft_mask", "palette", "legacy_info"}
        values = {}
        for info_field in fields(self):
            value = getattr(self, info_field.name)
            if info_field.name in redacted and value is not None:
                values[info_field.name] = "..."
            else:
                values[info_field.name] = value
        return f"{self.__class__.__name__}({values})"

    def to_legacy_dict(self) -> LegacyImageInfo:
        """Return the legacy dict-based image info with historical keys."""
        return self.legacy_info

    def scale_inside_box(
        self, x: float, y: float, w: float, h: float
    ) -> tuple[float, float, float, float]:
        """
        Make an image fit within a bounding box, maintaining its proportions.
        In the reduced dimension it will be centered within the available space.
        """
        img_w = self.width
        img_h = self.height
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


@dataclass(slots=True)
class RasterImageInfo(ImageInfo):
    "Information about a raster image used in the PDF document"

    data: bytes = b""
    color_space: str = ""
    color_components: int = 0
    bits_per_component: int = 0
    filter: ImageFilter = "AUTO"
    decode_params: str = ""
    is_inverted: bool = False
    icc_profile: Optional[bytes] = None
    icc_profile_index: Optional[int] = None
    palette: Optional[bytes] = None
    soft_mask: Optional[bytes] = None
    index: int = 0
    usage_count: int = 0
    object_id: Optional[int] = None
    _default_size_scale: Optional[float] = field(default=None, init=False, repr=False)
    _default_size: Optional[tuple[float, float]] = field(
        default=None, init=False, repr=False
    )

    def __post_init__(self) -> None:
        ImageInfo.__post_init__(self)
        legacy = self.legacy_info
        legacy["data"] = self.data
        legacy["cs"] = self.color_space
        legacy["dpn"] = self.color_components
        legacy["bpc"] = self.bits_per_component
        legacy["f"] = self.filter
        legacy["dp"] = self.decode_params
        legacy["inverted"] = self.is_inverted
        legacy["iccp"] = self.icc_profile
        legacy["iccp_i"] = self.icc_profile_index
        legacy["pal"] = self.palette
        legacy["smask"] = self.soft_mask
        legacy["i"] = self.index
        legacy["obj_id"] = self.object_id
        legacy["usages"] = self.usage_count

    def update_from(self, other: "RasterImageInfo") -> None:
        """Update this instance from another parsed image info."""
        self.data = other.data
        self.width = other.width
        self.height = other.height
        self.color_space = other.color_space
        self.icc_profile = other.icc_profile
        self.color_components = other.color_components
        self.bits_per_component = other.bits_per_component
        self.filter = other.filter
        self.is_inverted = other.is_inverted
        self.decode_params = other.decode_params
        self.soft_mask = other.soft_mask
        self.palette = other.palette
        self._default_size_scale = None
        self._default_size = None
        legacy = self.legacy_info
        legacy["w"] = self.width
        legacy["h"] = self.height
        legacy["rendered_width"] = self.rendered_width
        legacy["rendered_height"] = self.rendered_height
        legacy["data"] = self.data
        legacy["cs"] = self.color_space
        legacy["dpn"] = self.color_components
        legacy["bpc"] = self.bits_per_component
        legacy["f"] = self.filter
        legacy["dp"] = self.decode_params
        legacy["inverted"] = self.is_inverted
        legacy["iccp"] = self.icc_profile
        legacy["iccp_i"] = self.icc_profile_index
        legacy["pal"] = self.palette
        legacy["smask"] = self.soft_mask
        legacy["i"] = self.index
        legacy["obj_id"] = self.object_id
        legacy["usages"] = self.usage_count

    def to_legacy_dict(self) -> LegacyImageInfo:
        return self.legacy_info

    def size_in_document_units(
        self, w: float, h: float, scale: float = 1
    ) -> tuple[float, float]:
        img_w = self.width
        img_h = self.height
        if w == 0 and h == 0:  # Put image at 72 dpi
            if self._default_size_scale == scale and self._default_size is not None:
                return self._default_size
            w = img_w / scale
            h = img_h / scale
            self._default_size_scale = scale
            self._default_size = (w, h)
        elif w == 0:
            w = h * img_w / img_h
        elif h == 0:
            h = w * img_h / img_w
        return w, h


@dataclass(slots=True)
class VectorImageInfo(ImageInfo):
    "Information about a vector image used in the PDF document"

    data: Optional[Any] = None

    def __post_init__(self) -> None:
        ImageInfo.__post_init__(self)
        self.legacy_info["data"] = self.data

    def to_legacy_dict(self) -> LegacyImageInfo:
        return self.legacy_info


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
            img.usage_count = 0
