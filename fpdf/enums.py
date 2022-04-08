from enum import IntEnum


class DocumentState(IntEnum):
    UNINITIALIZED = 0
    READY = 1  # page not started yet
    GENERATING_PAGE = 2
    CLOSED = 3  # EOF printed


class TextMode(IntEnum):
    "Values described in PDF spec section 'Text Rendering Mode'"
    FILL = 0
    STROKE = 1
    FILL_STROKE = 2
    INVISIBLE = 3
    FILL_CLIP = 4
    STROKE_CLIP = 5
    FILL_STROKE_CLIP = 6
    CLIP = 7


class XPos(IntEnum):
    """
    Positional values in horizontal direction for use after printing text.
        LEFT    - left end of the cell
        RIGHT   - right end of the cell (default)
        START   - start of actual text
        END     - end of actual text
        WCONT   - for write() to continue next (slightly left of END)
        CENTER  - center of actual text
        LMARGIN - left page margin (start of printable area)
        RMARGIN - right page margin (end of printable area)
    """

    LEFT = 1  # self.x
    RIGHT = 2  # self.x + w
    START = 3  # left end of actual text
    END = 4  # right end of actual text
    WCONT = 5  # continuation point for write()
    CENTER = 6  # center of actual text
    LMARGIN = 7  # self.l_margin
    RMARGIN = 8  # self.w - self.r_margin


class YPos(IntEnum):
    """
    Positional values in vertical direction for use after printing text.
        TOP     - top of the first line (default)
        LAST    - top of the last line (same as TOP for single-line text)
        NEXT    - top of next line (bottom of current text)
        TMARGIN - top page margin (start of printable area)
        BMARGIN - bottom page margin (end of printable area)
    """

    TOP = 1  # self.y
    LAST = 2  # top of last line (TOP for single lines)
    NEXT = 3  # LAST + h
    TMARGIN = 4  # self.t_margin
    BMARGIN = 5  # self.h - self.b_margin
