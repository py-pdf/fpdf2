from .enums import TextDirection, Duplex, PageBoundaries, PageMode
from .syntax import build_obj_dict, create_dictionary_string, Name


class ViewerPreferences:
    "Specifies the way the document shall be displayed on the screen"

    def __init__(
        self,
        hide_toolbar=False,
        hide_menubar=False,
        hide_window_u_i=False,
        fit_window=False,
        center_window=False,
        display_doc_title=False,
        non_full_screen_page_mode=PageMode.USE_NONE,
        num_copies=None,
        print_page_range=None,
        direction=None,
        duplex=None,
        view_area=None,
        view_clip=None,
        print_area=None,
        print_clip=None,
        print_scaling=None,
    ):
        self._min_pdf_version = "1.3"
        self.hide_toolbar = hide_toolbar
        """
        (`bool`)
        A flag specifying whether to hide the conforming reader’s tool bars when the document is active
        """
        self.hide_menubar = hide_menubar
        """
        (`bool`)
        A flag specifying whether to hide the conforming reader’s menu bar when the document is active
        """
        self.hide_window_u_i = hide_window_u_i
        """
        (`bool`)
        A flag specifying whether to hide user interface elements in the document’s window
        (such as scroll bars and navigation controls), leaving only the document’s contents displayed
        """
        self.fit_window = fit_window
        """
        (`bool`)
        A flag specifying whether to resize the document’s window to fit the size of the first displayed page
        """
        self.center_window = center_window
        """
        (`bool`)
        A flag specifying whether to position the document’s window in the center of the screen
        """
        self.display_doc_title = display_doc_title
        """
        (`bool`)
        A flag specifying whether the window’s title bar should display the document title
        taken from the Title entry of the document information dictionary.
        If false, the title bar should instead display the name of the PDF file containing the document.
        """
        self.non_full_screen_page_mode = non_full_screen_page_mode
        """
        (`fpdf.enums.PageMode`)
        The document’s page mode, specifying how to display the document on exiting full-screen mode
        """
        self.num_copies = num_copies
        """
        (`int`)
        The number of copies that shall be printed when the print dialog is opened for this file.
        Values outside this range shall be ignored. Default value: as defined by the conforming reader, but typically 1
        """
        self.print_page_range = print_page_range
        """
        (`list[int]`)
        The page numbers used to initialize the print dialog box when the file is printed.
        The array shall contain an even number of integers to be interpreted in pairs,
        with each pair specifying the first and last pages in a sub-range of pages to be printed.
        The first page of the PDF file shall be denoted by 1.
        """
        self.direction = direction
        """
        (`fpdf.enums.TextDirection`)
        The predominant reading order for text.
        """
        self.duplex = duplex
        """
        (`fpdf.enums.Duplex`)
        The paper handling option that shall be used when printing the file from the print dialog.
        """
        self.view_area = view_area
        """
        (`fpdf.enums.PageBoundaries`)
        The name of the page boundary representing the area of a page that shall be displayed when viewing the document on the screen.
        Default value: CropBox.
        """
        self.view_clip = view_clip
        """
        (`fpdf.enums.PageBoundaries`)
        The name of the page boundary to which the contents of a page shall be clipped when viewing the document on the screen.
        Default value: CropBox.
        """
        self.print_area = print_area
        """
        (`fpdf.enums.PageBoundaries`)
        The name of the page boundary representing the area of a page that shall be rendered when printing the document.
        Default value: CropBox.
        """
        self.print_clip = print_clip
        """
        (`fpdf.enums.PageBoundaries`)
        The name of the page boundary to which the contents of a page shall be clipped when printing the document.
        Default value: CropBox.
        """
        self.print_scaling = print_scaling
        """
        The page scaling option that shall be selected when a print dialogue is displayed for this document.
        Valid values are:

        * `"None"`, which indicates no page scaling
        * `"AppDefault"`, which indicates the interactive PDF processor’s default print scaling

        If this entry is not specified or has an unrecognised value, `AppDefault` shall be used.
        """

    def _set_min_pdf_version(self, version):
        self._min_pdf_version = max(self._min_pdf_version, version)

    @property
    def non_full_screen_page_mode(self):
        return self._non_full_screen_page_mode

    @non_full_screen_page_mode.setter
    def non_full_screen_page_mode(self, page_mode):
        self._non_full_screen_page_mode = (
            None if page_mode is None else PageMode.coerce(page_mode)
        )
        if self._non_full_screen_page_mode in (
            PageMode.FULL_SCREEN,
            PageMode.USE_ATTACHMENTS,
        ):
            raise ValueError(
                f"{self.non_full_screen_page_mode} is not a supported value for NonFullScreenPageMode"
            )

    @property
    def num_copies(self):
        return self._num_copies

    @num_copies.setter
    def num_copies(self, num_copies):
        if num_copies is not None:
            self._set_min_pdf_version("1.7")
        self._num_copies = num_copies

    @property
    def print_page_range(self):
        return self._print_page_range

    @print_page_range.setter
    def print_page_range(self, print_page_range):
        if print_page_range is not None:
            self._set_min_pdf_version("1.7")
        self._print_page_range = print_page_range

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, direction):
        self._direction = None if direction is None else TextDirection.coerce(direction)

    @property
    def display_doc_title(self):
        return self._display_doc_title

    @display_doc_title.setter
    def display_doc_title(self, display_doc_title):
        if display_doc_title:
            self._set_min_pdf_version("1.4")
        self._display_doc_title = display_doc_title

    @property
    def duplex(self):
        return self._duplex

    @duplex.setter
    def duplex(self, duplex):
        if duplex is not None:
            self._set_min_pdf_version("1.7")
        self._duplex = None if duplex is None else Duplex.coerce(duplex)

    @property
    def view_area(self):
        return self._view_area

    @view_area.setter
    def view_area(self, view_area):
        if view_area is not None:
            self._set_min_pdf_version("1.4")
        self._view_area = (
            None if view_area is None else PageBoundaries.coerce(view_area)
        )

    @property
    def view_clip(self):
        return self._view_clip

    @view_clip.setter
    def view_clip(self, view_clip):
        if view_clip is not None:
            self._set_min_pdf_version("1.4")
        self._view_clip = (
            None if view_clip is None else PageBoundaries.coerce(view_clip)
        )

    @property
    def print_area(self):
        return self._print_area

    @print_area.setter
    def print_area(self, print_area):
        if print_area is not None:
            self._set_min_pdf_version("1.4")
        self._print_area = (
            None if print_area is None else PageBoundaries.coerce(print_area)
        )

    @property
    def print_clip(self):
        return self._print_clip

    @print_clip.setter
    def print_clip(self, print_clip):
        if print_clip is not None:
            self._set_min_pdf_version("1.4")
        self._print_clip = (
            None if print_clip is None else PageBoundaries.coerce(print_clip)
        )

    @property
    def print_scaling(self):
        return self._print_scaling

    @print_scaling.setter
    def print_scaling(self, print_scaling):
        if print_scaling is None:
            self._print_scaling = None
            return
        self._set_min_pdf_version("1.6")
        if print_scaling not in ("None", "AppDefault"):
            raise ValueError(f"Invalid {print_scaling=} value provided")
        self._print_scaling = Name(print_scaling)

    def serialize(self, _security_handler=None, _obj_id=None):
        obj_dict = build_obj_dict(
            {key: getattr(self, key) for key in dir(self)},
            _security_handler=_security_handler,
            _obj_id=_obj_id,
        )
        return create_dictionary_string(obj_dict)
