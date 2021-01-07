"""put_catalog_test.py"""

import unittest
import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.join(".."))
)

import fpdf
import test
from test.utilities import relative_path_to, calculate_hash_of_file, set_doc_date_0


def document_operations(doc):
    set_doc_date_0(doc)
    doc.add_page()
    doc.set_font("Arial", size=12)
    doc.cell(w=72, h=0, border=1, ln=2, txt="hello world", fill=0, link="")


known_good_hashes = {
    "zoom_fullpage": "e8e2142ca350d826a595d76af6b43a18",
    "zoom_fullwidth": "eccfd6346d72bf484dd04aa974a0452c",
    "zoom_real": "4fe8735f67e5ccfb646d8931e2097f34",
    "zoom_default": "e8e2142ca350d826a595d76af6b43a18",
    "layout_single": "6028e1b1bbee49790978cb8fb0ec7cde",
    "layout_continuous": "e8e2142ca350d826a595d76af6b43a18",
    "layout_two": "9d1ef647bb3604b57be27324320c8917",
    "layout_default": "747d91e99c9915e10c12719d20c525d9",
}


class CatalogDisplayModeTest(unittest.TestCase):
    """This test executes some possible inputs to FPDF#set_display_mode."""

    def test_setting_all_zoom(self):
        for zoom_input in ["fullpage", "fullwidth", "real", "default"]:
            doc = fpdf.FPDF()
            document_operations(doc)

            doc.set_display_mode(zoom=zoom_input, layout="continuous")

            output = relative_path_to("continuous " + zoom_input + " output.pdf")
            doc.output(output)
            # print(calculate_hash_of_file(output), 'zoom_' + zoom_input)
            known_good_hash = known_good_hashes["zoom_" + zoom_input]
            self.assertEqual(known_good_hash, calculate_hash_of_file(output))
            os.unlink(output)
            del doc

    def test_setting_all_layout(self):
        for layout_input in ["single", "continuous", "two", "default"]:
            doc = fpdf.FPDF()
            document_operations(doc)

            doc.set_display_mode(zoom="default", layout=layout_input)

            output = relative_path_to("default " + layout_input + " output.pdf")
            doc.output(output)
            # print(calculate_hash_of_file(output), 'layout_' + layout_input)
            known_good_hash = known_good_hashes["layout_" + layout_input]
            self.assertEqual(known_good_hash, calculate_hash_of_file(output))
            os.unlink(output)
            del doc


if __name__ == "__main__":
    unittest.main()

## Development of demo mostly done as written above.
# hashes were printed as above then manipulated into a dictionary with text
# editor wizardry.
