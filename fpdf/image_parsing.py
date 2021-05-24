import zlib
from io import BytesIO
from urllib.request import urlopen

from PIL import Image

from .errors import FPDFException


SUPPORTED_IMAGE_FILTERS = ("AUTO", "FlateDecode", "DCTDecode", "JPXDecode")


def load_resource(filename, reason="image"):
    """Load external file"""
    # if a bytesio instance is passed in, use it as is.
    if isinstance(filename, BytesIO):
        return filename
    # by default loading from network is allowed for all images
    if reason == "image":
        if filename.startswith(("http://", "https://")):
            f = BytesIO(urlopen(filename).read())
        else:
            with open(filename, "rb") as fl:
                f = BytesIO(fl.read())
        return f
    raise FPDFException(f'Unknown resource loading reason "{reason}"')


def get_img_info(img, image_filter="AUTO"):
    """
    Args:
        img: `BytesIO` or `PIL.Image.Image` instance
        image_filter (str): one of the SUPPORTED_IMAGE_FILTERS
    """
    if not isinstance(img, Image.Image):
        img = Image.open(img)
    if image_filter == "AUTO":
        # Very simple logic for now:
        image_filter = "DCTDecode" if img.format == "JPEG" else "FlateDecode"
    if img.mode not in ["L", "LA", "RGB", "RGBA"]:
        img = img.convert("RGBA")
    w, h = img.size
    info = {}
    if img.mode == "L":
        dpn, bpc, colspace = 1, 8, "DeviceGray"
        info["data"] = _to_data(img, image_filter)
    elif img.mode == "LA":
        dpn, bpc, colspace = 1, 8, "DeviceGray"
        alpha_channel = slice(1, None, 2)
        info["data"] = _to_data(img, image_filter, remove_slice=alpha_channel)
        info["smask"] = _to_data(img, image_filter, select_slice=alpha_channel)
    elif img.mode == "RGB":
        dpn, bpc, colspace = 3, 8, "DeviceRGB"
        info["data"] = _to_data(img, image_filter)
    else:  # RGBA image
        dpn, bpc, colspace = 3, 8, "DeviceRGB"
        alpha_channel = slice(3, None, 4)
        info["data"] = _to_data(img, image_filter, remove_slice=alpha_channel)
        info["smask"] = _to_data(img, image_filter, select_slice=alpha_channel)

    dp = f"/Predictor 15 /Colors {dpn} /BitsPerComponent {bpc} /Columns {w}"

    info.update(
        {
            "w": w,
            "h": h,
            "cs": colspace,
            "bpc": bpc,
            "f": image_filter,
            "dp": dp,
            "pal": "",
            "trns": "",
        }
    )

    return info


def _to_data(img, image_filter, **kwargs):
    if image_filter == "FlateDecode":
        return _to_zdata(img, **kwargs)
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
    channels_count = len(data) // (img.size[0] * img.size[1])
    loop_incr = img.size[0] * channels_count + 1
    i = 0
    while i < len(data):
        data[i:i] = b"\0"
        i += loop_incr
    return zlib.compress(data)
