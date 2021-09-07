
class Table():

    """A pdf table"""

    def __init__(self):

        self.html_content = None
        self.html_attrs = None
        self.images = None

        # self.text_content = []   # table cell contents: data[n_rows][n_cols]
        # self.image_contents  = [] #
        #
        self.width = None # width of the table
        self.table_offset = 0

        self.colwidths = [] # column widhts in pct [n_cols]
        self.header = [] # optional: header contents [n_cols]
        self.footer = [] # optional: header contents [n_cols]
        self.do_border = False

        self._cell_active = False # are we inside <td> ?

    def tr_start(self):
        """Adds an empty list of html_content (equivalent to <tr>)"""
        if self.html_content is None:
            self.html_content = [[]]
            self.html_attrs = [[]]
            self.images = [[]]
        else:
            self.html_content.append([])
            self.html_attrs.append([])
            self.images.append([])

    def tr_close(self):
        pass

    def td_start(self, attrs = None):
        """Adds a cell to html_content (equivalent to <td>)"""
        self.html_content[-1].append('')
        self.html_attrs[-1].append(attrs)
        self.images[-1].append(None)

        self._cell_active = True

    def td_close(self):
        self._cell_active = False

    def add_image(self, attrs):
        """Adds a image to the current cell - only a single image can be present in each cell"""
        if self._cell_active:
            self.images[-1][-1] = attrs


    def add_data(self, data):
        """Adds data to the current cell - if any"""

        if self._cell_active:
            self.html_content[-1][-1] += data

    def insert(self, pdf):
        """Inserts the table at the current location in the pdf"""
        print('inserting table')

