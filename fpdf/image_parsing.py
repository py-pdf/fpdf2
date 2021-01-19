import zlib
from io import BytesIO
from urllib.request import urlopen

from PIL import Image

from .errors import FPDFException


def load_resource(filename, reason="image"):
    """Load external file"""
    # if a bytesio instance is passed in, use it as is.
    if isinstance(filename, BytesIO):
        return filename
    # by default loading from network is allowed for all images
    if reason == "image":
        if filename.startswith("http://") or filename.startswith("https://"):
            f = BytesIO(urlopen(filename).read())
        else:
            with open(filename, "rb") as fl:
                f = BytesIO(fl.read())
        return f
    raise FPDFException(f'Unknown resource loading reason "{reason}"')


def get_img_info(img):
    """
    Args:
        input_img: `BytesIO` or `PIL.Image.Image` instance
    """
    if not isinstance(img, Image.Image):
        img = Image.open(img)
    if img.mode not in ["L", "LA", "RGBA"]:
        img = img.convert("RGBA")
    w, h = img.size
    info = {}
    if img.mode == "L":
        dpn, bpc, colspace = 1, 8, "DeviceGray"
        info["data"] = to_zdata(img)
    elif img.mode == "LA":
        dpn, bpc, colspace = 1, 8, "DeviceGray"
        alpha_channel = slice(1, None, 2)
        info["data"] = to_zdata(img, remove_slice=alpha_channel)
        info["smask"] = to_zdata(img, select_slice=alpha_channel)
    else:  # RGBA image
        dpn, bpc, colspace = 3, 8, "DeviceRGB"
        alpha_channel = slice(3, None, 4)
        info["data"] = to_zdata(img, remove_slice=alpha_channel)
        info["smask"] = to_zdata(img, select_slice=alpha_channel)

    dp = f"/Predictor 15 /Colors {dpn} /BitsPerComponent {bpc} /Columns {w}"

    info.update(
        {
            "w": w,
            "h": h,
            "cs": colspace,
            "bpc": bpc,
            "f": "FlateDecode",
            "dp": dp,
            "pal": "",
            "trns": "",
        }
    )

    return info


def to_zdata(img, remove_slice=None, select_slice=None):
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
