import base64, zlib
from io import BytesIO
from math import ceil
from urllib.request import urlopen

try:
    from PIL import Image, TiffImagePlugin

    try:
        from PIL.Image import Resampling

        RESAMPLE = Resampling.LANCZOS
    except ImportError:  # For Pillow < 9.1.0
        RESAMPLE = Image.ANTIALIAS
except ImportError:
    Image = None

from .errors import FPDFException


SUPPORTED_IMAGE_FILTERS = ("AUTO", "FlateDecode", "DCTDecode", "JPXDecode")


def load_image(filename):
    """
    This method is used to load external resources, such as images.
    It is automatically called when resource added to document by `FPDF.image()`.
    It always return a BytesIO buffer.
    """
    # if a bytesio instance is passed in, use it as is.
    if isinstance(filename, BytesIO):
        return filename
    # by default loading from network is allowed for all images
    if filename.startswith(("http://", "https://")):
        # disabling bandit rule as permitted schemes are whitelisted:
        with urlopen(filename) as url_file:  # nosec B310
            return BytesIO(url_file.read())
    elif filename.startswith("data"):
        return _decode_base64_image(filename)
    with open(filename, "rb") as local_file:
        return BytesIO(local_file.read())


def _decode_base64_image(base64Image):
    "Decode the base 64 image string into an io byte stream."
    imageData = base64Image.split("base64,")[1]
    decodedData = base64.b64decode(imageData)
    return BytesIO(decodedData)


def get_img_info(img, image_filter="AUTO", dims=None):
    """
    Args:
        img: `BytesIO` or `PIL.Image.Image` instance
        image_filter (str): one of the SUPPORTED_IMAGE_FILTERS
    """
    if Image is None:
        raise EnvironmentError("Pillow not available - fpdf2 cannot insert images")

    if not isinstance(img, Image.Image):
        img = Image.open(img)

    if dims:
        img = img.resize(dims, resample=RESAMPLE)

    if image_filter == "AUTO":
        # Very simple logic for now:
        if img.format == "JPEG":
            image_filter = "DCTDecode"
        elif img.mode == "1":
            image_filter = "CCITTFaxDecode"
        else:
            image_filter = "FlateDecode"

    if img.mode in ("P", "PA") and image_filter != "FlateDecode":
        img = img.convert("RGBA")

    if img.mode not in ("1", "L", "LA", "RGB", "RGBA", "P", "PA"):
        img = img.convert("RGBA")

    w, h = img.size
    info = {}
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
        inverted = False
        # copied from img2pdf
        if (
            img.format == "TIFF"
            and img.info["compression"] == "group4"
            and len(img.tag_v2[TiffImagePlugin.STRIPOFFSETS]) == 1
            and len(img.tag_v2[TiffImagePlugin.STRIPBYTECOUNTS]) == 1
        ):
            photo = img.tag_v2[TiffImagePlugin.PHOTOMETRIC_INTERPRETATION]
            if photo == 0:
                inverted = True
        dp = f"/BlackIs1 {str(inverted).lower()} /Columns {w} /K -1 /Rows {h}"

    info.update(
        {
            "w": w,
            "h": h,
            "cs": colspace,
            "bpc": bpc,
            "f": image_filter,
            "dp": dp,
        }
    )

    return info

class temp_attr:
    """
    Copied verbatim from img2pdf

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
    Copied verbatim from img2pdf
    """
    # If Pillow is passed an invalid compression argument it will ignore it;
    # make sure the image actually got compressed.
    if img.info["compression"] != "group4":
        raise ValueError(
            "Image not compressed with CCITT Group 4 but with: %s"
            % img.info["compression"]
        )

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

    #logger.debug("TIFF strip_offsets: %d" % offset)
    #logger.debug("TIFF strip_bytes: %d" % length)

    return offset, length


def transcode_monochrome(imgdata):
    """
    Convert the open PIL.Image imgdata to compressed CCITT Group4 data.

    Copied verbatim from img2pdf
    """

    #logger.debug("Converting monochrome to CCITT Group4")

    # Convert the image to Group 4 in memory. If libtiff is not installed and
    # Pillow is not compiled against it, .save() will raise an exception.
    newimgio = BytesIO()

    # we create a whole new PIL image or otherwise it might happen with some
    # input images, that libtiff fails an assert and the whole process is
    # killed by a SIGABRT:
    #   https://gitlab.mister-muffin.de/josch/img2pdf/issues/46
    im = Image.frombytes(imgdata.mode, imgdata.size, imgdata.tobytes())

    # Since version 8.3.0 Pillow limits strips to 64 KB. Since PDF only
    # supports single strip CCITT Group4 payloads, we have to coerce it back
    # into putting everything into a single strip. Thanks to Andrew Murray for
    # the hack.
    #
    # Since version 8.4.0 Pillow allows us to modify the strip size explicitly
    tmp_strip_size = (imgdata.size[0] + 7) // 8 * imgdata.size[1]
    if hasattr(TiffImagePlugin, "STRIP_SIZE"):
        # we are using Pillow 8.4.0 or later
        with temp_attr(TiffImagePlugin, "STRIP_SIZE", tmp_strip_size):
            im.save(newimgio, format="TIFF", compression="group4")
    else:
        # only needed for Pillow 8.3.x but works for versions before that as
        # well
        pillow__getitem__ = TiffImagePlugin.ImageFileDirectory_v2.__getitem__

        def __getitem__(self, tag):
            overrides = {
                TiffImagePlugin.ROWSPERSTRIP: imgdata.size[1],
                TiffImagePlugin.STRIPBYTECOUNTS: [tmp_strip_size],
                TiffImagePlugin.STRIPOFFSETS: [0],
            }
            return overrides.get(tag, pillow__getitem__(self, tag))

        with temp_attr(
            TiffImagePlugin.ImageFileDirectory_v2, "__getitem__", __getitem__
        ):
            im.save(newimgio, format="TIFF", compression="group4")

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
