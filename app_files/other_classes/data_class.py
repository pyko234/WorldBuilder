"""
This class to handle data that needs to be passed around the mainwindow
"""

class AppData:
    """
    Represents shared data between frames in the application.
    
    Attributes:
        selected_world (str): The selected database to work on or view.
        table_names (list): The names of tables within the database, allowing for schema updates.
        selected_category (str): The category selected when choosing which entry to work on.
        selected_entry_data (dict): The data of the selected entry stored as a dictionary.
        previous_entry_data (dict): The data of the previously selected entry stored as a dictionary.
        previous_frame: (obj): The reference to the previously displayed frame.
        session: (obj): The SQLAlchemy session used for various backend operations.
        url: (str): The SQLAlchemy URL for the selected database.
        edit: (bool): Indicates the mode selected, where True represents "Edit" mode and False represents "View" mode.

    Methods:
        __init__(): Initializes the AppData object by creating attributes.
    """

    def __init__(self):
        """
        Initializes the AppData object by creating attributes.

        Attributes are initialized with None to enforce typing.
        """
        self.selected_world = None
        self.table_names = []
        self.selected_category = None
        self.selected_entry_data = None
        self.previous_entry_data = None
        self.previous_frame = None
        self.session = None
        self.url = None
        self.edit = None
