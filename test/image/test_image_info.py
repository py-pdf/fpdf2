import json
import os
from io import BytesIO

import fpdf

from test.utilities import relative_path_to


class TestImageParsing:
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

        with open(relative_path_to("image_info.json")) as f:
            expected = json.load(f)

        for info, image in zip(infos, images):
            short_info = {k: v for k, v in info.items() if k in short_keys}
            assert short_info == expected[image]

    def test_get_img_info_data_rgba(self):
        path = os.path.join(relative_path_to("png_test_suite/"), "basi3p02.png")
        blob = BytesIO(get_contents(path))
        info = fpdf.image_parsing.get_img_info(blob)
        assert (
            info["data"]
            == b"x\x9c\xed\x941\n\x000\x08\x03\xf3\xffO\xdbM\xea APD\x08dQ\x0eo\x08\x08\xc0<\x16\x07\x0f\xfe\x94y\t\n\xfc\x8cL\x02\xce\x0f\x94\x19\xd7\x12PA[\x99\xc9U\tv\xfeO\xe0%X\xefC\x02\xce\xdf\xff\xa6\xf7\x05me&W%`\xfc\x03\x80,\xfb="
        )
        assert info["smask"] == b"x\x9cc\xf8O\x000\x8c*\x18U0\xaa`\xa4*\x00\x00?h\xfc."

    def test_get_img_info_data_gray(self):
        path = os.path.join(relative_path_to("png_test_suite/"), "basi0g08.png")
        blob = BytesIO(get_contents(path))
        info = fpdf.image_parsing.get_img_info(blob)
        assert (
            info["data"]
            == b"x\x9cc``dbfaec\xe7\xe0\xe4\xe2\xe6\xe1\xe5\xe3\x17\x10\x14\x12\x16\x11\x15\x13\x97\x90\x94\x92\x96\x91\x95\x93gPPTRVQUS\xd7\xd0\xd4\xd2\xd6\xd1\xd5\xd370426153\xb7\xb0\xb4\xb2\xb6\xb1\xb5\xb3gpptrvqus\xf7\xf0\xf4\xf2\xf6\xf1\xf5\xf3\x0f\x08\x0c\n\x0e\t\r\x0b\x8f\x88\x8c\x8a\x8e\x89\x8d\x8bgHHLJNIMK\xcf\xc8\xcc\xca\xce\xc9\xcd\xcb/(,*.)-+\xaf\xa8\xac\xaa\xae\xa9\xad\xabghhljnimk\xef\xe8\xec\xea\xee\xe9\xed\xeb\x9f0q\xd2\xe4)S\xa7M\x9f1s\xd6\xec9s\xe7\xcdgX\xb0p\xd1\xe2%K\x97-_\xb1r\xd5\xea5k\xd7\xad\xdf\xb0q\xd3\xe6-[\xb7m\xdf\xb1s\xd7\xee={\xf7\xedg8p\xf0\xd0\xe1#G\x8f\x1d?q\xf2\xd4\xe93g\xcf\x9d\xbfp\xf1\xd2\xe5+W\xaf]\xbfq\xf3\xd6\xed;w\xef\xddgx\xf0\xf0\xd1\xe3'O\x9f=\x7f\xf1\xf2\xd5\xeb7o\xdf\xbd\xff\xf0\xf1\xd3\xe7/_\xbf}\xff\xf1\xf3\xd7\xef?\x7f\xff\xfdg\xf8\xf7\xf7\xcf\xef_?\x7f|\xff\xf6\xf5\xcb\xe7O\x1f?\xbc\x7f\xf7\xf6\xcd\xebW/_<\x7f\xf6\xf4\xc9\xe3G\x0f\x1f\xdcg\xb8w\xf7\xce\xed[7o\\\xbfv\xf5\xca\xe5K\x17/\x9c?w\xf6\xcc\xe9S'O\x1c?v\xf4\xc8\xe1C\x07\x0f\xecg\xd8\xb7w\xcf\xee];wl\xdf\xb6u\xcb\xe6M\x1b7\xac_\xb7v\xcd\xeaU+W,_\xb6t\xc9\xe2E\x0b\x17\xccg\x987w\xce\xecY3gL\x9f6u\xca\xe4I\x13'\xf4\xf7\xf5\xf6twuv\xb4\xb7\xb5\xb64756\xd43\xd4\xd5\xd6TWUV\x94\x97\x95\x96\x14\x17\x15\x16\xe4\xe7\xe5\xe6dgef\xa4\xa7\xa5\xa6$'%&\xc43\xc4\xc5\xc6DGEF\x84\x87\x85\x86\x04\x07\x05\x06\xf8\xfb\xf9\xfax{yz\xb8\xbb\xb9\xba8;9:\xd83\xd8\xd9\xdaX[YZ\x98\x9b\x99\x9a\x18\x1b\x19\x1a\xe8\xeb\xe9\xeahkij\xa8\xab\xa9\xaa(+)*\xc83\xc8\xc9\xcaHKIJ\x88\x8b\x89\x8a\x08\x0b\t\n\xf0\xf3\xf1\xf2psqr\xb0\xb3\xb1\xb2031202\xe0O\r\n\x8a\x0c\xf8S\x83\x83#\x03\xfe\xd4\x90\x90\xc8\x80?5442\xe0O\r\x0b\x162\xe0O\r\x07\x0e2\xe0O\r\x0f\x1e2\xe0O\r\xff\xfe2\xe0O\r\xf7\xee2\xe0O\r\xfb\xf62\xe0O\r\xf3\xe62\xe0O\ru\xb5\x0c\xf8SC\\,\x03\xfe\xd4`g\xcb\x80?5\xc8\xc92\xe0O\rL\xcc\x00\x17\xb3\xfc\x18"
        )


def get_contents(path):
    with open(path, "rb") as f:
        return f.read()
