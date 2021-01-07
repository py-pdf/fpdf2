# -*- coding: utf-8 -*-

"""FPDF Error classes"""

# this module is unwriteable without tests


class FPDFException(Exception):
    pass


class FPDFPageFormatException(FPDFException):
    # """Error is thrown when a bad page format is given"""
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
        inputs = [self.argument, self.unknown, self.one]
        arguments = ", ".join(list(map(repr, inputs)))
        return "".join([self.__class__.__name__, "(", arguments, ")"])

    def __str__(self):
        out = self.__class__.__name__ + ": "
        if self.unknown:
            return out + "Unknown page format: " + self.argument
        if self.one:
            return (
                out + "Only one argument given: %s. Need (height,width)" % self.argument
            )
        return out + self.argument
