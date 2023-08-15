import types, warnings
from copy import deepcopy

from .deprecation import get_stack_level
from .errors import FPDFException


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

    def __init__(self, pdf, accept_page_break=True):
        self.pdf = pdf
        self._initial = deepcopy(self.pdf.__dict__)
        self._calls = []
        if not accept_page_break:
            self.accept_page_break = False

    def __getattr__(self, name):
        attr = getattr(self.pdf, name)
        if callable(attr):
            return CallRecorder(attr, self._calls)
        return attr

    def rewind(self):
        self.pdf.__dict__ = self._initial
        self._initial = deepcopy(self.pdf.__dict__)

    def replay(self):
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
    def __init__(self, func, calls):
        self._func = func
        self._calls = calls

    def __call__(self, *args, **kwargs):
        self._calls.append((self._func, args, kwargs))
        return self._func(*args, **kwargs)
