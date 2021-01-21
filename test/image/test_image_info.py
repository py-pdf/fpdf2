import unittest
import sys
import os
import pickle
import fpdf
from io import BytesIO

from PIL import Image

# python -m unittest test.image.image_info.ImageParsingTest

from test.utilities import relative_path_to


class ImageParsingTest(unittest.TestCase):
    def break_down_filename(self, image):
        """
        filename:                               g04i2c08.png
                                                || ||||
        test feature (in this case gamma) ------+| ||||
        parameter of test (here gamma-value) ----+ ||||
        interlaced or non-interlaced --------------+|||
        color-type (numerical) ---------------------+||
        color-type (descriptive) --------------------+|
        bit-depth ------------------------------------|
        """
        return {
            "test_feature": image[0].lower(),
            "parameter_ot": image[1:3].lower(),
            "noninterlace": image[3].lower() != "i",
            "colortype_nm": int(image[4], 10),
            "colortype_ds": image[5].lower(),
            "n_bits_depth": int(image[6:8], 10),
        }

    def test_get_img_info(self):
        img_dir = "png_test_suite/"
        images = sorted(os.listdir(relative_path_to(img_dir))[:20])

        def isok(image):
            return image.endswith(".png") and not image.startswith("x")

        images = [image for image in images if isok(image)]
        # expln = [self.break_down_filename(name) for name in images]

        paths = [os.path.join(relative_path_to(img_dir), i) for i in images]
        blobs = [BytesIO(get_contents(path)) for path in paths]
        # modes = [Image.open(blob).mode for blob in blobs]

        infos = [fpdf.image_parsing.get_img_info(blob) for blob in blobs]

        short_keys = ["f", "h", "bpc", "w", "cs", "trns", "dp", "pal"]

        for info, image in zip(infos, images):
            short_info = {k: v for k, v in info.items() if k in short_keys}
            if image == "g25n2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "bgbn4a08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "f03n0g08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s09n3p02.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 9,
                        "w": 9,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 9",
                    },
                )
            elif image == "cs3n2c16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s40n3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 40,
                        "w": 40,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 40",
                    },
                )
            elif image == "cdhn2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 8,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "bgan6a16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basi3p01.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "cs8n3p08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "ct1n0g04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "cdun2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basi3p02.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "ps1n0g08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s04n3p01.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 4,
                        "w": 4,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 4",
                    },
                )
            elif image == "s33n3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 33,
                        "w": 33,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 33",
                    },
                )
            elif image == "z03n2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "f02n2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basi0g08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "oi1n0g16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s03n3p01.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 3,
                        "w": 3,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 3",
                    },
                )
            elif image == "oi4n2c16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "f99n0g04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basi0g16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "g07n0g16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s32i3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "tm3n3p02.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "ccwn2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "tbwn3p08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "cdfn2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 8,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 8",
                    },
                )
            elif image == "ps2n2c16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s35n3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 35,
                        "w": 35,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 35",
                    },
                )
            elif image == "s39i3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 39,
                        "w": 39,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 39",
                    },
                )
            elif image == "s05n3p02.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 5,
                        "w": 5,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 5",
                    },
                )
            elif image == "cdsn2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 8,
                        "w": 8,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 8",
                    },
                )
            elif image == "tbgn3p08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "tbrn2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "f01n0g08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "f03n2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s36n3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 36,
                        "w": 36,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 36",
                    },
                )
            elif image == "s06i3p02.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 6,
                        "w": 6,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 6",
                    },
                )
            elif image == "bgai4a16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "g05n0g16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "z00n2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "g04n2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s01n3p01.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 1,
                        "w": 1,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 1",
                    },
                )
            elif image == "oi9n0g16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "tbgn2c16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "cten0g04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "tp0n0g08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "exif2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "tbbn2c16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s36i3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 36,
                        "w": 36,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 36",
                    },
                )
            elif image == "cs8n2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "ps2n0g08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "f04n0g08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s33i3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 33,
                        "w": 33,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 33",
                    },
                )
            elif image == "s35i3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 35,
                        "w": 35,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 35",
                    },
                )
            elif image == "oi2n2c16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "cs5n2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "bggn4a16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s38i3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 38,
                        "w": 38,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 38",
                    },
                )
            elif image == "ps1n2c16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "cthn0g04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "oi1n2c16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "ch2n3p08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "g03n2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s34i3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 34,
                        "w": 34,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 34",
                    },
                )
            elif image == "tp0n2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "tp0n3p08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "cm9n0g04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s39n3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 39,
                        "w": 39,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 39",
                    },
                )
            elif image == "basi3p08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basi2c16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basn0g02.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "pp0n2c16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "f01n2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "ctgn0g04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "tp1n3p08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s05i3p02.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 5,
                        "w": 5,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 5",
                    },
                )
            elif image == "g10n2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "g03n3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basn0g04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s08i3p02.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 8,
                        "w": 8,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 8",
                    },
                )
            elif image == "basn6a08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "f04n2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "cs3n3p08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "tbbn0g04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s02n3p01.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 2,
                        "w": 2,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 2",
                    },
                )
            elif image == "s06n3p02.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 6,
                        "w": 6,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 6",
                    },
                )
            elif image == "bgwn6a08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basi0g04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basi4a08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "ctzn0g04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "oi2n0g16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s03i3p01.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 3,
                        "w": 3,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 3",
                    },
                )
            elif image == "f00n0g08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "ch1n3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "bgai4a08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basn0g16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basi3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s40i3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 40,
                        "w": 40,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 40",
                    },
                )
            elif image == "tbyn3p08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basi0g02.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basn2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "f00n2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s04i3p01.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 4,
                        "w": 4,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 4",
                    },
                )
            elif image == "basn0g08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "bgan6a08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s38n3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 38,
                        "w": 38,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 38",
                    },
                )
            elif image == "s09i3p02.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 9,
                        "w": 9,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 9",
                    },
                )
            elif image == "tbwn0g16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "g07n2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basn0g01.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "g05n3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "g05n2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s34n3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 34,
                        "w": 34,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 34",
                    },
                )
            elif image == "basn3p02.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basi6a08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basn3p01.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "oi9n2c16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basn4a16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "g10n3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "bgyn6a16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "f02n0g08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basn3p08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "ctjn0g04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "pp0n6a08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basi0g01.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s02i3p01.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 2,
                        "w": 2,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 2",
                    },
                )
            elif image == "ct0n0g04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s08n3p02.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 8,
                        "w": 8,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 8",
                    },
                )
            elif image == "basi6a16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "cm7n0g04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "ccwn3p08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "z06n2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basi4a16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "z09n2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s01i3p01.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 1,
                        "w": 1,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 1",
                    },
                )
            elif image == "g25n3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s07i3p02.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 7,
                        "w": 7,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 7",
                    },
                )
            elif image == "oi4n0g16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "g03n0g16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "g04n0g16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "g25n0g16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basi2c08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s37i3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 37,
                        "w": 37,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 37",
                    },
                )
            elif image == "s32n3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "cm0n0g04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basn3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basn2c16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s37n3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 37,
                        "w": 37,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 37",
                    },
                )
            elif image == "g07n3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "cs5n3p08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "tbbn3p08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basn4a08.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "g10n0g16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "basn6a16.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "s07n3p02.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 7,
                        "w": 7,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 7",
                    },
                )
            elif image == "ctfn0g04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceGray",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns 32",
                    },
                )
            elif image == "g04n3p04.png":
                self.assertEqual(
                    short_info,
                    {
                        "bpc": 8,
                        "f": "FlateDecode",
                        "h": 32,
                        "w": 32,
                        "cs": "DeviceRGB",
                        "trns": "",
                        "pal": "",
                        "dp": "/Predictor 15 /Colors 3 /BitsPerComponent 8 /Columns 32",
                    },
                )

    def test_get_img_info_data_rgba(self):
        path = os.path.join(relative_path_to("png_test_suite/"), "basi3p02.png")
        blob = BytesIO(get_contents(path))
        info = fpdf.image_parsing.get_img_info(blob)
        self.assertEqual(
            info["data"],
            b"x\x9c\xed\x941\n\x000\x08\x03\xf3\xffO\xdbM\xea APD\x08dQ\x0eo\x08\x08\xc0<\x16\x07\x0f\xfe\x94y\t\n\xfc\x8cL\x02\xce\x0f\x94\x19\xd7\x12PA[\x99\xc9U\tv\xfeO\xe0%X\xefC\x02\xce\xdf\xff\xa6\xf7\x05me&W%`\xfc\x03\x80,\xfb=",
        )
        self.assertEqual(
            info["smask"], b"x\x9cc\xf8O\x000\x8c*\x18U0\xaa`\xa4*\x00\x00?h\xfc."
        )

    def test_get_img_info_data_gray(self):
        path = os.path.join(relative_path_to("png_test_suite/"), "basi0g08.png")
        blob = BytesIO(get_contents(path))
        info = fpdf.image_parsing.get_img_info(blob)
        self.assertEqual(
            info["data"],
            b"x\x9cc``dbfaec\xe7\xe0\xe4\xe2\xe6\xe1\xe5\xe3\x17\x10\x14\x12\x16\x11\x15\x13\x97\x90\x94\x92\x96\x91\x95\x93gPPTRVQUS\xd7\xd0\xd4\xd2\xd6\xd1\xd5\xd370426153\xb7\xb0\xb4\xb2\xb6\xb1\xb5\xb3gpptrvqus\xf7\xf0\xf4\xf2\xf6\xf1\xf5\xf3\x0f\x08\x0c\n\x0e\t\r\x0b\x8f\x88\x8c\x8a\x8e\x89\x8d\x8bgHHLJNIMK\xcf\xc8\xcc\xca\xce\xc9\xcd\xcb/(,*.)-+\xaf\xa8\xac\xaa\xae\xa9\xad\xabghhljnimk\xef\xe8\xec\xea\xee\xe9\xed\xeb\x9f0q\xd2\xe4)S\xa7M\x9f1s\xd6\xec9s\xe7\xcdgX\xb0p\xd1\xe2%K\x97-_\xb1r\xd5\xea5k\xd7\xad\xdf\xb0q\xd3\xe6-[\xb7m\xdf\xb1s\xd7\xee={\xf7\xedg8p\xf0\xd0\xe1#G\x8f\x1d?q\xf2\xd4\xe93g\xcf\x9d\xbfp\xf1\xd2\xe5+W\xaf]\xbfq\xf3\xd6\xed;w\xef\xddgx\xf0\xf0\xd1\xe3'O\x9f=\x7f\xf1\xf2\xd5\xeb7o\xdf\xbd\xff\xf0\xf1\xd3\xe7/_\xbf}\xff\xf1\xf3\xd7\xef?\x7f\xff\xfdg\xf8\xf7\xf7\xcf\xef_?\x7f|\xff\xf6\xf5\xcb\xe7O\x1f?\xbc\x7f\xf7\xf6\xcd\xebW/_<\x7f\xf6\xf4\xc9\xe3G\x0f\x1f\xdcg\xb8w\xf7\xce\xed[7o\\\xbfv\xf5\xca\xe5K\x17/\x9c?w\xf6\xcc\xe9S'O\x1c?v\xf4\xc8\xe1C\x07\x0f\xecg\xd8\xb7w\xcf\xee];wl\xdf\xb6u\xcb\xe6M\x1b7\xac_\xb7v\xcd\xeaU+W,_\xb6t\xc9\xe2E\x0b\x17\xccg\x987w\xce\xecY3gL\x9f6u\xca\xe4I\x13'\xf4\xf7\xf5\xf6twuv\xb4\xb7\xb5\xb64756\xd43\xd4\xd5\xd6TWUV\x94\x97\x95\x96\x14\x17\x15\x16\xe4\xe7\xe5\xe6dgef\xa4\xa7\xa5\xa6$'%&\xc43\xc4\xc5\xc6DGEF\x84\x87\x85\x86\x04\x07\x05\x06\xf8\xfb\xf9\xfax{yz\xb8\xbb\xb9\xba8;9:\xd83\xd8\xd9\xdaX[YZ\x98\x9b\x99\x9a\x18\x1b\x19\x1a\xe8\xeb\xe9\xeahkij\xa8\xab\xa9\xaa(+)*\xc83\xc8\xc9\xcaHKIJ\x88\x8b\x89\x8a\x08\x0b\t\n\xf0\xf3\xf1\xf2psqr\xb0\xb3\xb1\xb2031202\xe0O\r\n\x8a\x0c\xf8S\x83\x83#\x03\xfe\xd4\x90\x90\xc8\x80?5442\xe0O\r\x0b\x162\xe0O\r\x07\x0e2\xe0O\r\x0f\x1e2\xe0O\r\xff\xfe2\xe0O\r\xf7\xee2\xe0O\r\xfb\xf62\xe0O\r\xf3\xe62\xe0O\ru\xb5\x0c\xf8SC\\,\x03\xfe\xd4`g\xcb\x80?5\xc8\xc92\xe0O\rL\xcc\x00\x17\xb3\xfc\x18",
        )


def get_contents(path):
    with open(path, "rb") as f:
        return f.read()
