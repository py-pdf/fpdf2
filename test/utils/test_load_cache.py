import pickle

import fpdf


class TestLoadCache:
    def test_load_cache_none(self):
        result = fpdf.fpdf.load_cache(None)
        assert result is None

    def test_load_cache_pickle(self, tmp_path):
        path = tmp_path / "filename.pickle"
        a = {"hello": "world"}
        with path.open("wb") as handle:
            pickle.dump(a, handle, protocol=pickle.HIGHEST_PROTOCOL)

        assert fpdf.fpdf.load_cache(path) == a
        assert fpdf.fpdf.load_cache(path.with_name("filename1.pickle")) is None
