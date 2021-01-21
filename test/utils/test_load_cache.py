# """load_cache.py"""

import os
import pickle

import fpdf


# with open('filename.pickle', 'rb') as handle:
#     b = pickle.load(handle)

# print a == b


class TestLoadCache:
    def test_load_cache_none(self):
        result = fpdf.fpdf.load_cache(None)
        assert result is None

    def test_load_cache_pickle(self):
        a = {"hello": "world"}
        with open("filename.pickle", "wb") as handle:
            pickle.dump(a, handle, protocol=pickle.HIGHEST_PROTOCOL)

        assert fpdf.fpdf.load_cache("filename.pickle") == a
        assert fpdf.fpdf.load_cache("filename1.pickle") is None

        os.unlink("filename.pickle")
