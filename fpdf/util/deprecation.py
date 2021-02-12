import warnings
from types import ModuleType


class WarnOnDeprecatedModuleAttributes(ModuleType):
    def __getattr__(self, name):
        if name in ("FPDF_CACHE_DIR", "FPDF_CACHE_MODE"):
            warnings.warn(
                "fpdf.FPDF_CACHE_DIR & fpdf.FPDF_CACHE_MODE"
                " have been deprecated in favour of"
                " FPDF(font_cache_dir=...)",
                DeprecationWarning,
                stacklevel=2,
            )
            return None
        # pylint: disable=no-member
        return super().__getattr__(self, name)

    def __setattr__(self, name, value):
        if name in ("FPDF_CACHE_DIR", "FPDF_CACHE_MODE"):
            warnings.warn(
                "fpdf.FPDF_CACHE_DIR & fpdf.FPDF_CACHE_MODE"
                " have been deprecated in favour of"
                " FPDF(font_cache_dir=...)",
                DeprecationWarning,
                stacklevel=2,
            )
            return
        return super().__setattr__(self, name, value)
