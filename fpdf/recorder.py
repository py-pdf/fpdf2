"""
A wrapper class to allow rewinding/replaying changes made to a FPDF instance.

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.
"""

import types
import warnings
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Callable

from .deprecation import get_stack_level
from .errors import FPDFException

if TYPE_CHECKING:
    from .fpdf import FPDF

# One recorded call: function + positional args + keyword args
CallRecord = tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any]]


class FPDFRecorder:
    """
    The class is aimed to be used as wrapper around fpdf.FPDF:

        pdf = FPDF()
        recorder = FPDFRecorder(pdf)

    Its aim is dual:
      * allow to **rewind** to the state of the FPDF instance passed to its constructor,
        reverting all changes made to its internal state
      * allow to **replay** again all the methods calls performed
        on the recorder instance between its creation and the last call to rewind()

    Note that method can be called on a FPDFRecorder instance using its .pdf attribute
    so that they are not recorded & replayed later, on a call to .replay().

    Note that using this class means to duplicate the FPDF `bytearray` buffer:
    when generating large PDFs, doubling memory usage may be troublesome.
    """

    page_break_triggered: bool

    def __init__(self, pdf: "FPDF", accept_page_break: bool = True) -> None:
        self.pdf = pdf
        self._initial: dict[str, Any] = deepcopy(vars(self.pdf))
        self._calls: list[CallRecord] = []
        if not accept_page_break:
            self.accept_page_break = False

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self.pdf, name)
        if callable(attr):
            return CallRecorder(attr, self._calls)
        return attr

    def rewind(self) -> None:
        pdf_dict = vars(self.pdf)
        pdf_dict.clear()
        pdf_dict.update(self._initial)
        self._initial = deepcopy(pdf_dict)

    def replay(self) -> None:
        for call in self._calls:
            func, args, kwargs = call
            try:
                result = func(*args, **kwargs)
                if isinstance(result, types.GeneratorType):
                    warnings.warn(
                        "Detected usage of a context manager inside an unbreakable() section, which is not supported",
                        stacklevel=get_stack_level(),
                    )
                # The results of other methods can also be invalidated: .pages_count, page_no(), get_x() / get_y(), will_page_break()
            except Exception as error:
                raise FPDFException(
                    f"Failed to replay FPDF call: {func}(*{args}, **{kwargs})"
                ) from error
        self._calls = []


class CallRecorder:
    def __init__(self, func: Callable[..., Any], calls: list[CallRecord]) -> None:
        self._func: Callable[..., Any] = func
        self._calls: list[CallRecord] = calls

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        self._calls.append((self._func, args, kwargs))
        return self._func(*args, **kwargs)
