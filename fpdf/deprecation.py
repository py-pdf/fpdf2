import warnings
from types import ModuleType


class WarnOnDeprecatedModuleAttributes(ModuleType):
    def __call__(self):
        raise TypeError(
            # pylint: disable=implicit-str-concat
            "You tried to instantied the fpdf module."
            " You probably want to import the FPDF class instead:"
            " from fpdf import FPDF"
        )

    def __getattr__(self, name):
        if name in ("FPDF_CACHE_DIR", "FPDF_CACHE_MODE"):
            warnings.warn(
                # pylint: disable=implicit-str-concat
                "fpdf.FPDF_CACHE_DIR & fpdf.FPDF_CACHE_MODE"
                " have been deprecated in favour of"
                " FPDF(font_cache_dir=...)",
                DeprecationWarning,
                stacklevel=2,
            )
            return None
        return super().__getattribute__(name)

    def __setattr__(self, name, value):
        if name in ("FPDF_CACHE_DIR", "FPDF_CACHE_MODE"):
            warnings.warn(
                # pylint: disable=implicit-str-concat
                "fpdf.FPDF_CACHE_DIR & fpdf.FPDF_CACHE_MODE"
                " have been deprecated in favour of"
                " FPDF(font_cache_dir=...)",
                DeprecationWarning,
                stacklevel=2,
            )
            return
        super().__setattr__(name, value)
