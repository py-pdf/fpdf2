import base64, zlib
from io import BytesIO
from math import ceil
from urllib.request import urlopen
from pathlib import Path
import logging

try:
    from PIL import Image, TiffImagePlugin
    from PIL import ImageCms

    try:
        from PIL.Image import Resampling

        RESAMPLE = Resampling.LANCZOS
    except ImportError:  # For Pillow < 9.1.0
        # pylint: disable=no-member
        RESAMPLE = Image.ANTIALIAS
except ImportError:
    Image = None

from .errors import FPDFException


LOGGER = logging.getLogger(__name__)
SUPPORTED_IMAGE_FILTERS = ("AUTO", "FlateDecode", "DCTDecode", "JPXDecode")

# fmt: off
TIFFBitRevTable = [
    0x00, 0x80, 0x40, 0xC0, 0x20, 0xA0, 0x60, 0xE0, 0x10, 0x90,
    0x50, 0xD0, 0x30, 0xB0, 0x70, 0xF0, 0x08, 0x88, 0x48, 0xC8,
    0x28, 0xA8, 0x68, 0xE8, 0x18, 0x98, 0x58, 0xD8, 0x38, 0xB8,
    0x78, 0xF8, 0x04, 0x84, 0x44, 0xC4, 0x24, 0xA4, 0x64, 0xE4,
    0x14, 0x94, 0x54, 0xD4, 0x34, 0xB4, 0x74, 0xF4, 0x0C, 0x8C,
    0x4C, 0xCC, 0x2C, 0xAC, 0x6C, 0xEC, 0x1C, 0x9C, 0x5C, 0xDC,
    0x3C, 0xBC, 0x7C, 0xFC, 0x02, 0x82, 0x42, 0xC2, 0x22, 0xA2,
    0x62, 0xE2, 0x12, 0x92, 0x52, 0xD2, 0x32, 0xB2, 0x72, 0xF2,
    0x0A, 0x8A, 0x4A, 0xCA, 0x2A, 0xAA, 0x6A, 0xEA, 0x1A, 0x9A,
    0x5A, 0xDA, 0x3A, 0xBA, 0x7A, 0xFA, 0x06, 0x86, 0x46, 0xC6,
    0x26, 0xA6, 0x66, 0xE6, 0x16, 0x96, 0x56, 0xD6, 0x36, 0xB6,
    0x76, 0xF6, 0x0E, 0x8E, 0x4E, 0xCE, 0x2E, 0xAE, 0x6E, 0xEE,
    0x1E, 0x9E, 0x5E, 0xDE, 0x3E, 0xBE, 0x7E, 0xFE, 0x01, 0x81,
    0x41, 0xC1, 0x21, 0xA1, 0x61, 0xE1, 0x11, 0x91, 0x51, 0xD1,
    0x31, 0xB1, 0x71, 0xF1, 0x09, 0x89, 0x49, 0xC9, 0x29, 0xA9,
    0x69, 0xE9, 0x19, 0x99, 0x59, 0xD9, 0x39, 0xB9, 0x79, 0xF9,
    0x05, 0x85, 0x45, 0xC5, 0x25, 0xA5, 0x65, 0xE5, 0x15, 0x95,
    0x55, 0xD5, 0x35, 0xB5, 0x75, 0xF5, 0x0D, 0x8D, 0x4D, 0xCD,
    0x2D, 0xAD, 0x6D, 0xED, 0x1D, 0x9D, 0x5D, 0xDD, 0x3D, 0xBD,
    0x7D, 0xFD, 0x03, 0x83, 0x43, 0xC3, 0x23, 0xA3, 0x63, 0xE3,
    0x13, 0x93, 0x53, 0xD3, 0x33, 0xB3, 0x73, 0xF3, 0x0B, 0x8B,
    0x4B, 0xCB, 0x2B, 0xAB, 0x6B, 0xEB, 0x1B, 0x9B, 0x5B, 0xDB,
    0x3B, 0xBB, 0x7B, 0xFB, 0x07, 0x87, 0x47, 0xC7, 0x27, 0xA7,
    0x67, 0xE7, 0x17, 0x97, 0x57, 0xD7, 0x37, 0xB7, 0x77, 0xF7,
    0x0F, 0x8F, 0x4F, 0xCF, 0x2F, 0xAF, 0x6F, 0xEF, 0x1F, 0x9F,
    0x5F, 0xDF, 0x3F, 0xBF, 0x7F, 0xFF,
]
# fmt: on


def load_image(filename):
    """
    This method is used to load external resources, such as images.
    It is automatically called when resource added to document by `fpdf.FPDF.image()`.
    It always return a BytesIO buffer.
    """
    # if a bytesio instance is passed in, use it as is.
    if isinstance(filename, BytesIO):
        return filename
    if isinstance(filename, Path):
        filename = str(filename)
    # by default loading from network is allowed for all images
    if filename.startswith(("http://", "https://")):
        # disabling bandit & semgrep rules as permitted schemes are whitelisted:
        # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
        with urlopen(filename) as url_file:  # nosec B310
            return BytesIO(url_file.read())
    elif filename.startswith("data:"):
        return _decode_base64_image(filename)
    with open(filename, "rb") as local_file:
        return BytesIO(local_file.read())


def _decode_base64_image(base64Image):
    "Decode the base 64 image string into an io byte stream."
    imageData = base64Image.split("base64,")[1]
    decodedData = base64.b64decode(imageData)
    return BytesIO(decodedData)


def is_iccp_valid(iccp, filename):
    "Checks the validity of an ICC profile"
    try:
        profile = ImageCms.getOpenProfile(BytesIO(iccp))
    except ImageCms.PyCMSError:
        LOGGER.info("Invalid ICC Profile in file %s", filename)
        return False
    color_space = profile.profile.xcolor_space.strip()
    if color_space not in ("GRAY", "RGB"):
        LOGGER.info(
            "Unsupported color space %s in ICC Profile of file %s - cf. issue #711",
            color_space,
            filename,
        )
        return False
    return True


def get_img_info(filename, img=None, image_filter="AUTO", dims=None):
    """
    Args:
        filename: in a format that can be passed to load_image
        img: optional `bytes`, `BytesIO` or `PIL.Image.Image` instance
        image_filter (str): one of the SUPPORTED_IMAGE_FILTERS
    """
    if Image is None:
        raise EnvironmentError("Pillow not available - fpdf2 cannot insert images")

    is_pil_img = True
    jpeg_inverted = False  # flag to check whether a cmyk image is jpeg or not, if set to True the decode array is inverted in output.py
    img_raw_data = None
    if not img or isinstance(img, (Path, str)):
        img_raw_data = load_image(filename)
        img = Image.open(img_raw_data)
        is_pil_img = False
    elif not isinstance(img, Image.Image):
        if isinstance(img, bytes):
            img = BytesIO(img)
        img_raw_data = img
        img = Image.open(img_raw_data)
        is_pil_img = False

    img_altered = False
    if dims:
        img = img.resize(dims, resample=RESAMPLE)
        img_altered = True

    if image_filter == "AUTO":
        # Very simple logic for now:
        if img.format == "JPEG":
            image_filter = "DCTDecode"
        elif img.mode == "1" and hasattr(Image.core, "libtiff_support_custom_tags"):
            # The 2nd condition prevents from running in a bug sometimes,
            # cf. test_transcode_monochrome_and_libtiff_support_custom_tags()
            image_filter = "CCITTFaxDecode"
        else:
            image_filter = "FlateDecode"

    if img.mode in ("P", "PA") and image_filter != "FlateDecode":
        img = img.convert("RGBA")

    if img.mode not in ("1", "L", "LA", "RGB", "RGBA", "P", "PA", "CMYK"):
        img = img.convert("RGBA")
        img_altered = True

    w, h = img.size
    info = {}

    iccp = None
    if "icc_profile" in img.info:
        if is_iccp_valid(img.info["icc_profile"], filename):
            iccp = img.info["icc_profile"]

    if img_raw_data is not None and not img_altered:
        # if we can use the original image bytes directly we do (JPEG and group4 TIFF only):
        if img.format == "JPEG" and image_filter == "DCTDecode":
            if img.mode in ("RGB", "RGBA"):
                dpn, bpc, colspace = 3, 8, "DeviceRGB"
            elif img.mode == "CMYK":
                dpn, bpc, colspace = 4, 8, "DeviceCMYK"
                jpeg_inverted = True
            if img.mode == "L":
                dpn, bpc, colspace = 1, 8, "DeviceGray"
            img_raw_data.seek(0)
            return {
                "data": img_raw_data.read(),
                "w": w,
                "h": h,
                "cs": colspace,
                "iccp": iccp,
                "dpn": dpn,
                "bpc": bpc,
                "f": image_filter,
                "inverted": jpeg_inverted,
                "dp": f"/Predictor 15 /Colors {dpn} /Columns {w}",
            }
        # We can directly copy the data out of a CCITT Group 4 encoded TIFF, if it
        # only contains a single strip
        if (
            img.format == "TIFF"
            and image_filter == "CCITTFaxDecode"
            and img.info["compression"] == "group4"
            and len(img.tag_v2[TiffImagePlugin.STRIPOFFSETS]) == 1
            and len(img.tag_v2[TiffImagePlugin.STRIPBYTECOUNTS]) == 1
        ):
            photo = img.tag_v2[TiffImagePlugin.PHOTOMETRIC_INTERPRETATION]
            inverted = False
            if photo == 0:
                inverted = True
            elif photo != 1:
                raise ValueError(
                    f"unsupported photometric interpretation for g4 tiff: {photo}"
                )
            offset, length = ccitt_payload_location_from_pil(img)
            img_raw_data.seek(offset)
            ccittrawdata = img_raw_data.read(length)
            fillorder = img.tag_v2.get(TiffImagePlugin.FILLORDER)
            if fillorder is None or fillorder == 1:
                # no FillOrder or msb-to-lsb: nothing to do
                pass
            elif fillorder == 2:
                # lsb-to-msb: reverse bits of each byte
                ccittrawdata = bytearray(ccittrawdata)
                for i, n in enumerate(ccittrawdata):
                    ccittrawdata[i] = TIFFBitRevTable[n]
                ccittrawdata = bytes(ccittrawdata)
            else:
                raise ValueError(f"unsupported FillOrder: {fillorder}")
            dpn, bpc, colspace = 1, 1, "DeviceGray"
            return {
                "data": ccittrawdata,
                "w": w,
                "h": h,
                "iccp": None,
                "dpn": dpn,
                "cs": colspace,
                "bpc": bpc,
                "f": image_filter,
                "inverted": jpeg_inverted,
                "dp": f"/BlackIs1 {str(not inverted).lower()} /Columns {w} /K -1 /Rows {h}",
            }

    # garbage collection
    img_raw_data = None

    if img.mode == "1":
        dpn, bpc, colspace = 1, 1, "DeviceGray"
        info["data"] = _to_data(img, image_filter)
    elif img.mode == "L":
        dpn, bpc, colspace = 1, 8, "DeviceGray"
        info["data"] = _to_data(img, image_filter)
    elif img.mode == "LA":
        dpn, bpc, colspace = 1, 8, "DeviceGray"
        alpha_channel = slice(1, None, 2)
        info["data"] = _to_data(img, image_filter, remove_slice=alpha_channel)
        if _has_alpha(img, alpha_channel) and image_filter not in (
            "DCTDecode",
            "JPXDecode",
        ):
            info["smask"] = _to_data(img, image_filter, select_slice=alpha_channel)
    elif img.mode == "P":
        dpn, bpc, colspace = 1, 8, "Indexed"
        info["data"] = _to_data(img, image_filter)
        info["pal"] = img.palette.palette

        # check if the P image has transparency
        if img.info.get("transparency", None) is not None and image_filter not in (
            "DCTDecode",
            "JPXDecode",
        ):
            # convert to RGBA to get the alpha channel for creating the smask
            info["smask"] = _to_data(
                img.convert("RGBA"), image_filter, select_slice=slice(3, None, 4)
            )
    elif img.mode == "PA":
        dpn, bpc, colspace = 1, 8, "Indexed"
        info["pal"] = img.palette.palette
        alpha_channel = slice(1, None, 2)
        info["data"] = _to_data(img, image_filter, remove_slice=alpha_channel)
        if _has_alpha(img, alpha_channel) and image_filter not in (
            "DCTDecode",
            "JPXDecode",
        ):
            info["smask"] = _to_data(img, image_filter, select_slice=alpha_channel)
    elif img.mode == "CMYK":
        dpn, bpc, colspace = 4, 8, "DeviceCMYK"
        info["data"] = _to_data(img, image_filter)
    elif img.mode == "RGB":
        dpn, bpc, colspace = 3, 8, "DeviceRGB"
        info["data"] = _to_data(img, image_filter)
    else:  # RGBA image
        dpn, bpc, colspace = 3, 8, "DeviceRGB"
        alpha_channel = slice(3, None, 4)
        info["data"] = _to_data(img, image_filter, remove_slice=alpha_channel)
        if _has_alpha(img, alpha_channel) and image_filter not in (
            "DCTDecode",
            "JPXDecode",
        ):
            info["smask"] = _to_data(img, image_filter, select_slice=alpha_channel)

    dp = f"/Predictor 15 /Colors {dpn} /Columns {w}"

    if img.mode == "1":
        dp = f"/BlackIs1 true /Columns {w} /K -1 /Rows {h}"

    if not is_pil_img:
        img.close()

    info.update(
        {
            "w": w,
            "h": h,
            "cs": colspace,
            "iccp": iccp,
            "bpc": bpc,
            "dpn": dpn,
            "f": image_filter,
            "inverted": jpeg_inverted,
            "dp": dp,
        }
    )

    return info


class temp_attr:
    """
    temporary change the attribute of an object using a context manager
    """

    def __init__(self, obj, field, value):
        self.obj = obj
        self.field = field
        self.value = value

    def __enter__(self):
        self.exists = False
        if hasattr(self.obj, self.field):
            self.exists = True
            self.old_value = getattr(self.obj, self.field)
        setattr(self.obj, self.field, self.value)

    def __exit__(self, exctype, excinst, exctb):
        if self.exists:
            setattr(self.obj, self.field, self.old_value)
        else:
            delattr(self.obj, self.field)


def ccitt_payload_location_from_pil(img):
    """
    returns the byte offset and length of the CCITT payload in the original TIFF data
    """
    # assert(img.info["compression"] == "group4")

    # Read the TIFF tags to find the offset(s) of the compressed data strips.
    strip_offsets = img.tag_v2[TiffImagePlugin.STRIPOFFSETS]
    strip_bytes = img.tag_v2[TiffImagePlugin.STRIPBYTECOUNTS]

    # PIL always seems to create a single strip even for very large TIFFs when
    # it saves images, so assume we only have to read a single strip.
    # A test ~10 GPixel image was still encoded as a single strip. Just to be
    # safe check throw an error if there is more than one offset.
    if len(strip_offsets) != 1 or len(strip_bytes) != 1:
        raise NotImplementedError(
            "Transcoding multiple strips not supported by the PDF format"
        )

    (offset,), (length,) = strip_offsets, strip_bytes

    return offset, length


def transcode_monochrome(img):
    """
    Convert the open PIL.Image imgdata to compressed CCITT Group4 data.

    """
    # Convert the image to Group 4 in memory. If libtiff is not installed and
    # Pillow is not compiled against it, .save() will raise an exception.
    newimgio = BytesIO()

    # we create a whole new PIL image or otherwise it might happen with some
    # input images, that libtiff fails an assert and the whole process is
    # killed by a SIGABRT:
    img2 = Image.frombytes(img.mode, img.size, img.tobytes())

    # Since version 8.3.0 Pillow limits strips to 64 KB. Since PDF only
    # supports single strip CCITT Group4 payloads, we have to coerce it back
    # into putting everything into a single strip. Thanks to Andrew Murray for
    # the hack.
    #
    # Since version 8.4.0 Pillow allows us to modify the strip size explicitly
    tmp_strip_size = (img.size[0] + 7) // 8 * img.size[1]
    if hasattr(TiffImagePlugin, "STRIP_SIZE"):
        # we are using Pillow 8.4.0 or later
        with temp_attr(TiffImagePlugin, "STRIP_SIZE", tmp_strip_size):
            img2.save(newimgio, format="TIFF", compression="group4")
    else:
        # only needed for Pillow 8.3.x but works for versions before that as
        # well
        pillow__getitem__ = TiffImagePlugin.ImageFileDirectory_v2.__getitem__

        def __getitem__(self, tag):
            overrides = {
                TiffImagePlugin.ROWSPERSTRIP: img.size[1],
                TiffImagePlugin.STRIPBYTECOUNTS: [tmp_strip_size],
                TiffImagePlugin.STRIPOFFSETS: [0],
            }
            return overrides.get(tag, pillow__getitem__(self, tag))

        with temp_attr(
            TiffImagePlugin.ImageFileDirectory_v2, "__getitem__", __getitem__
        ):
            img2.save(newimgio, format="TIFF", compression="group4")

    # Open new image in memory
    newimgio.seek(0)
    newimg = Image.open(newimgio)

    offset, length = ccitt_payload_location_from_pil(newimg)

    newimgio.seek(offset)
    return newimgio.read(length)


def _to_data(img, image_filter, **kwargs):
    if image_filter == "FlateDecode":
        return _to_zdata(img, **kwargs)

    if image_filter == "CCITTFaxDecode":
        return transcode_monochrome(img)

    if img.mode == "LA":
        img = img.convert("L")

    if img.mode == "RGBA":
        img = img.convert("RGB")

    if image_filter == "DCTDecode":
        compressed_bytes = BytesIO()
        img.save(compressed_bytes, format="JPEG")
        return compressed_bytes.getvalue()

    if image_filter == "JPXDecode":
        compressed_bytes = BytesIO()
        img.save(compressed_bytes, format="JPEG2000")
        return compressed_bytes.getvalue()

    raise FPDFException(f'Unsupported image filter: "{image_filter}"')


def _to_zdata(img, remove_slice=None, select_slice=None):
    data = bytearray(img.tobytes())
    if remove_slice:
        del data[remove_slice]
    if select_slice:
        data = data[select_slice]
    # Left-padding every row with a single zero:
    if img.mode == "1":
        row_size = ceil(img.size[0] / 8)
    else:
        channels_count = len(data) // (img.size[0] * img.size[1])
        row_size = img.size[0] * channels_count

    data_with_padding = bytearray()
    for i in range(0, len(data), row_size):
        data_with_padding.extend(b"\0")
        data_with_padding.extend(data[i : i + row_size])

    return zlib.compress(data_with_padding)


def _has_alpha(img, alpha_channel):
    alpha = bytearray(img.tobytes())[alpha_channel]
    return any(c != 255 for c in alpha)
