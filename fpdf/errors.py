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

    def __init__(self, encoding, start, end, reason, character):
        super().__init__()
        self.encoding = encoding
        self.start = start
        self.end = end
        self.reason = reason
        self.character = character

    def __repr__(self):
        return (
            f"{self.__class__.__name__}"
            f"{repr(self.encoding), repr(self.start), repr(self.end), repr(self.reason)}"
        )

    def __str__(self):
        return f"Encoding used is {self.encoding}. Character {self.character} at position {self.start} of text is out of encoding range. Please consider using font that supports UTF-8 encoding"
