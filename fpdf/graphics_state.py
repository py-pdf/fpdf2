class GraphicsStateMixin:
    """Mixin class for managing a stack of graphics state variables.

    To the subclassing library and its users, the variables look like
    normal instance attributes. But by the magic of properties, we can
    push and pop levels as needed, and users will always see and modify
    just the current version.

    This class is mixed in by fpdf.FPDF(), and is not meant to be used
    directly by user code.
    """

    def __init__(self):
        self.__statestack = [
            dict(
                draw_color="0 G",
                fill_color="0 g",
                text_color="0 g",
                underline=False,
                font_style="",
                font_stretching=100,
                font_family="",
                font_size_pt=0,
                font_size=0,
                dash_pattern="[] 0 d",
            ),
        ]

    def _push_local_stack(self):
        self.__statestack.append(self.__statestack[-1].copy())

    def _pop_local_stack(self):
        del self.__statestack[-1]

    @property
    def draw_color(self):
        return self.__statestack[-1]["draw_color"]

    @draw_color.setter
    def draw_color(self, v):
        self.__statestack[-1]["draw_color"] = v

    @property
    def fill_color(self):
        return self.__statestack[-1]["fill_color"]

    @fill_color.setter
    def fill_color(self, v):
        self.__statestack[-1]["fill_color"] = v

    @property
    def text_color(self):
        return self.__statestack[-1]["text_color"]

    @text_color.setter
    def text_color(self, v):
        self.__statestack[-1]["text_color"] = v

    @property
    def underline(self):
        return self.__statestack[-1]["underline"]

    @underline.setter
    def underline(self, v):
        self.__statestack[-1]["underline"] = v

    @property
    def font_style(self):
        return self.__statestack[-1]["font_style"]

    @font_style.setter
    def font_style(self, v):
        self.__statestack[-1]["font_style"] = v

    @property
    def font_stretching(self):
        return self.__statestack[-1]["font_stretching"]

    @font_stretching.setter
    def font_stretching(self, v):
        self.__statestack[-1]["font_stretching"] = v

    @property
    def font_family(self):
        return self.__statestack[-1]["font_family"]

    @font_family.setter
    def font_family(self, v):
        self.__statestack[-1]["font_family"] = v

    @property
    def font_size_pt(self):
        return self.__statestack[-1]["font_size_pt"]

    @font_size_pt.setter
    def font_size_pt(self, v):
        self.__statestack[-1]["font_size_pt"] = v

    @property
    def font_size(self):
        return self.__statestack[-1]["font_size"]

    @font_size.setter
    def font_size(self, v):
        self.__statestack[-1]["font_size"] = v

    @property
    def dash_pattern(self):
        return self.__statestack[-1]["dash_pattern"]

    @dash_pattern.setter
    def dash_pattern(self, v):
        self.__statestack[-1]["dash_pattern"] = v
