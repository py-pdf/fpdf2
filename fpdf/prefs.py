from .enums import PageMode
from .syntax import build_obj_dict, create_dictionary_string


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
    ):
        self.hide_toolbar = hide_toolbar
        "A flag specifying whether to hide the conforming reader’s tool bars when the document is active"
        self.hide_menubar = hide_menubar
        "A flag specifying whether to hide the conforming reader’s menu bar when the document is active"
        self.hide_window_u_i = hide_window_u_i
        """
        A flag specifying whether to hide user interface elements in the document’s window
        (such as scroll bars and navigation controls), leaving only the document’s contents displayed
        """
        self.fit_window = fit_window
        "A flag specifying whether to resize the document’s window to fit the size of the first displayed page"
        self.center_window = center_window
        "A flag specifying whether to position the document’s window in the center of the screen"
        self.display_doc_title = display_doc_title
        """
        A flag specifying whether the window’s title bar should display the document title
        taken from the Title entry of the document information dictionary.
        If false, the title bar should instead display the name of the PDF file containing the document.
        """
        self.non_full_screen_page_mode = PageMode.coerce(non_full_screen_page_mode)
        if self.non_full_screen_page_mode in (
            PageMode.FULL_SCREEN,
            PageMode.USE_ATTACHMENTS,
        ):
            raise ValueError(
                f"{self.non_full_screen_page_mode} is not a support value for NonFullScreenPageMode"
            )

    @property
    def non_full_screen_page_mode(self):
        "(`fpdf.enums.PageMode`) The document’s page mode, specifying how to display the document on exiting full-screen mode"
        return self._non_full_screen_page_mode

    @non_full_screen_page_mode.setter
    def non_full_screen_page_mode(self, page_mode):
        self._non_full_screen_page_mode = PageMode.coerce(page_mode)

    def serialize(self):
        obj_dict = build_obj_dict({key: getattr(self, key) for key in dir(self)})
        return create_dictionary_string(obj_dict)
