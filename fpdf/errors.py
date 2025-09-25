class FPDFException(Exception):
    pass


class FPDFPageFormatException(FPDFException):
    """Error is thrown when a bad page format is given"""

    def __init__(self, argument, unknown=False, one=False):
        super().__init__()
        if unknown and one:
            raise TypeError(
                "FPDF Page Format Exception cannot be both for "
                "unknown type and for wrong number of arguments"
            )
        self.argument = argument
        self.unknown = unknown
        self.one = one

    def __repr__(self):
        return (
            f"{self.__class__.__name__}"
            f"({self.argument!r}, {self.unknown!r}, {self.one!r})"
        )

    def __str__(self):
        if self.unknown:
            res = f"Unknown page format: {self.argument}"
        elif self.one:
            res = f"Only one argument given: {self.argument}. Need (height,width)"
        else:
            res = self.argument
        return f"{self.__class__.__name__ }: {res}"


class FPDFUnicodeEncodingException(FPDFException):
    """Error is thrown when a character that cannot be encoded by the chosen encoder is provided"""

    def __init__(self, text_index, character, font_name):
        super().__init__()
        self.text_index = text_index
        self.character = character
        self.font_name = font_name

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.text_index), repr(self.character), repr(self.font_name)})"

    def __str__(self):
        return (
            f'Character "{self.character}" at index {self.text_index} in text is outside the range of characters'
            f' supported by the font used: "{self.font_name}".'
            " Please consider using a Unicode font."
        )


class ComplianceError(FPDFException):
    """Base class for standards-compliance violations (PDF/A, PDF/X, etc.)."""


class PDFAComplianceError(ComplianceError):
    """Raised when an operation would produce a PDF that violates the selected PDF/A profile."""
