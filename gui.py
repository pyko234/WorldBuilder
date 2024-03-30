import os
import io
import tkinter as tk
import backend_logic
import sys
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from database_schema import WorldBuilder
from PIL import Image, ImageTk


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


class UniversalHandler:
    """
        Handle scrollevents in a way that works cross-platform
    """
    @staticmethod
    def handle_scroll_event(event):
        """
        Handle scroll events for the canvas widget.
        """
        move = 0
        if sys.platform.startswith("linux"):
            # Linux platform
            if event.num == 4:
                move = -1
            elif event.num == 5:
                move = 1
        else:
            # Windows platform
            move = int(-1 * (event.delta / 120))

        # Identify the widget under the cursor
        widget = event.widget.winfo_containing(event.x_root, event.y_root)

        # Iterate through widget parents to find first instance of widget with 'yview_scroll'
        while widget is not None:

            # If the widget has yview_scroll attribute
            if not hasattr(widget, 'yview_scroll'):
            
                # Update the widget
                widget = widget.master

                # Skip the rest of the loop
                continue

            # If listbox is current widget name
            if 'listbox' in str(widget).split('!')[-1]:
                
                # If listbox size is not greater than listbox height
                if not widget.size() > int(widget.cget("height")):
                    
                    # Update the widget
                    widget = widget.master
                    
                    # Skip the rest of the loop
                    continue
            
            # Scroll the widget
            widget.yview_scroll(move, "units")

            # Stop the loop
            break


    @staticmethod
    def bind_scroll_event(parent_window):
        """
        Bind scroll events to the parent window.
        """
        if sys.platform.startswith("linux"):
            parent_window.bind("<Button-4>", UniversalHandler.handle_scroll_event)
            parent_window.bind("<Button-5>", UniversalHandler.handle_scroll_event)
        else:
            parent_window.bind("<MouseWheel>", UniversalHandler.handle_scroll_event)

    @staticmethod
    def get_db_path():
        """
        Return database path based on platform
        """
        if sys.platform.startswith("linux"):
            return os.path.expanduser("~/.local/share/WorldBuilder/db")
        else:
            return os.path.expanduser("~/AppData/Local/WorldBuilder/db")


class WorldSelectionFrame(tk.Frame):
    """
    Represents a frame for selecting a world and choosing between edit and view modes.

    Args:
        parent (tk.Widget): The parent widget to which this frame belongs.
        controller (tk.Widget): The controller responsible for managing the application flow.
        app_data (AppData): An instance of the AppData class containing application-wide data.

    Attributes:
        controller (tk.Widget): The controller widget responsible for managing application flow.
        app_data (AppData): An instance of the AppData class containing application-wide data.
        worlds (dict): A dictionary containing world names mapped to their respective data.
        world_var (tk.StringVar): Variable to hold the selected world name.
        edit_var (tk.StringVar): Variable to hold the selected mode (Edit/View).

    Methods:
        proceed(): Proceeds to the next step based on the selected world and edit mode.
        get_worlds(): Retrieves the available worlds and their corresponding database URLs.
        create_new(): Creates a new database for a new world.
    """

    def __init__(self, parent, controller, app_data):
        """
        Initialize the frame for selecting a world and choosing between edit and view modes.

        Args:
            parent (tk.Widget): The parent widget to which this frame belongs.
            controller (tk.Widget): The controller responsible for managing the application flow.
            app_data (AppData): An instance of the AppData class containing application-wide data.

        Attributes:
            controller (tk.Widget): The controller widget responsible for managing application flow.
            app_data (AppData): An instance of the AppData class containing application-wide data.
            worlds (dict): A dictionary containing world names mapped to their respective data.
            world_var (tk.StringVar): Variable to hold the selected world name.
            edit_var (tk.StringVar): Variable to hold the selected mode (Edit/View).
        """

        # Create a frame
        tk.Frame.__init__(self, parent)

        # Save the controller and app_data to the class
        self.controller = controller
        self.app_data = app_data

        # Retrieve available worlds
        self.worlds = self.get_worlds()

        # Variable to hold the selected world name
        self.world_var = tk.StringVar()

        # Extract world names from the dictionary keys and set the default value
        world_names = list(self.worlds.keys())
        self.world_var.set(world_names[0])

        # Variable to hold the selected mode (Edit/View)
        self.edit_var = tk.StringVar()
        self.edit_var.set("Edit")

        # Label and Dropdown for selecting a world
        world_label = ttk.Label(self, text="Select World:")
        world_label.pack(padx=10, pady=10)
        world_dropdown = ttk.Combobox(self, values=world_names, textvariable=self.world_var, state="readonly")
        world_dropdown.pack(padx=10, pady=10)

        # Radio buttons for selecting edit or view mode
        edit_view_frame = ttk.Frame(self)
        edit_view_frame.pack(padx=10, pady=10)
        view_radio = ttk.Radiobutton(edit_view_frame, text="Edit", variable=self.edit_var, value="Edit")
        view_radio.pack(padx=10, pady=10)
        edit_radio = ttk.Radiobutton(edit_view_frame, text="View", variable=self.edit_var, value="View")
        edit_radio.pack(padx=10, pady=10)

        # Button to proceed
        proceed_button = ttk.Button(self, text="Proceed", command=self.proceed)
        proceed_button.pack(padx=10, pady=10)

        # Button to create a new world
        create_button = ttk.Button(self, text='Create New World', command=self.create_new)
        create_button.pack(padx=10, pady=10)

    def proceed(self):
        """
        Proceeds to the next step based on the selected world and edit mode.

        Retrieves the selected world name and edit mode from the UI elements.
        Sets the edit mode in the application data accordingly.
        Retrieves the database URL for the selected world from the application data.
        Creates a session with the database URL.
        Updates the selected world in the application data.
        Shows the WorldOverviewFrame.

        Note:
            The WorldOverviewFrame is responsible for displaying an overview of the selected world.

        Returns:
            None
        """

        # Get the selected world and edit mode from UI elements
        selected_world = self.world_var.get()
        edit_mode = self.edit_var.get()
        
        # Set the edit mode in the app_data
        if edit_mode == "Edit":
            self.app_data.edit = True
        else:
            self.app_data.edit = False

        # Get the URL for the selected world from the application data
        database_url = self.worlds[selected_world]
        self.app_data.url = database_url

        # Create a session with the database URL
        self.app_data.session = backend_logic.create_session_by_url(database_url)
        self.app_data.selected_world = selected_world

        # Handle the selected world and edit mode
        self.controller.show_frame(WorldOverviewFrame)

    def get_worlds(self):
        """
        Retrieves the available worlds and their corresponding database URLs.

        Searches for database files in the 'db' directory relative to the script's location.
        Constructs database URLs for the found database files.
        Creates a session with each database URL to query the world names.
        Returns a dictionary mapping world names to their database URLs.

        Returns:
            dict: A dictionary containing world names as keys and their corresponding database URLs as values.
                  If no worlds are found, an empty dictionary is returned.
        """

        path = Path(UniversalHandler.get_db_path())

        # Initialize an empty dictionary to story world names and their database URLs
        names = {}

        # Iterate through files in the 'db' directory
        for file in os.listdir(path):

            # Check if the file is a database file
            if file.endswith("_database.db"):

                # Construct the database URL
                database_url = f"sqlite:///{path / file}"

                # Create a session with the current database URL
                session = backend_logic.create_session_by_url(database_url)

                # Query the first world entry in the database
                world_entry = session.query(WorldBuilder.World).first()
                
                # If a world entry exists, add it to the dictionary
                if world_entry:
                    names[world_entry.name] = database_url

        return names
    
    def create_new(self):
        """
        Creates a new database for a new world.

        Generates a new database URL by invoking the 'create_database' function from the backend logic module.
        If the database URL is successfully created:
            - Establishes a session with the new database URL using 'create_session_by_url'.
            - Navigates to the WorldOverviewFrame to display the newly created world.

        If the database URL creation fails, no action is taken.

        Note:
            The 'create_database' function is responsible for creating the new database file.

        Returns:
            None
        """

        # Generate a new database URL by creating a new database file
        database_url = backend_logic.create_database()

        # If the database URL is successfully created
        if database_url:

            # Establish a session with the new database URL
            self.app_data.session = backend_logic.create_session_by_url(database_url)

            # Navigate to the WorldOverviewFrame to display the newly created world
            self.controller.show_frame(WorldOverviewFrame)
        

class WorldOverviewFrame(tk.Frame):
    """
        Represents a frame for providing an overview of a selected world, including entry categories and entries.

        Args:
            parent (tk.Widget): The parent widget to which this frame belongs.
            controller (tk.Widget): The controller responsible for managing the application flow.
            app_data (AppData): An instance of the AppData class containing application-wide data.

        Attributes:
            controller (tk.Widget): The controller widget responsible for managing application flow.
            app_data (AppData): An instance of the AppData class containing application-wide data.
            label_text_var (tk.StringVar): Variable to hold the text for displaying the selected world name.
            listbox_dict (dict): A dictionary mapping category names to their respective listbox widgets.

        Methods:
            create_dynamic_category_widgets(): Creates dynamic category widgets based on available tables in the database.
            update_label_text(): Updates the label text to display the selected world name.
            update_listboxes(): Updates the listboxes with entry names for each category.
            on_double_click(event, table_name): Handles double-click events on listbox items to view or edit entry details.
            select_map(): Opens a file dialog to select an image file for the world map.
            save_image(image_data): Saves the selected image data as the world map in the database.
            view_map(): Retrieves and displays the world map from the database in a new window.
    """

    def __init__(self, parent, controller, app_data):
        """
            Initializes the WorldOverviewFrame instance.

            Args:
                parent (tk.Widget): The parent widget to which this frame belongs.
                controller (tk.Widget): The controller responsible for managing the application flow.
                app_data (AppData): An instance of the AppData class containing application-wide data.

            Attributes:
                parent (tk.Widget): The parent widget to which this frame belongs.
                controller (tk.Widget): The controller responsible for managing the application flow.
                app_data (AppData): An instance of the AppData class containing application-wide data.
                label_text_var (tk.StringVar): Variable to hold the text for displaying the selected world name.

            Note:
                This method sets up the GUI elements for displaying information about the selected world,
                including buttons for selecting and viewing the world map, and options for navigating back
                or creating a new entry.
        """

        # Create the frame and pass attributes
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.controller = controller
        self.app_data = app_data
        self.map_photo = None

        # Create StringVar for World Label
        self.label_text_var = tk.StringVar()
        self.label_text_var.set(self.app_data.selected_world)
        label = tk.Label(self, text=self.label_text_var.get())
        label.pack(pady=10)

        # Create Select Map button if mode is edit
        if self.app_data.edit:
            select_map_button = tk.Button(self, text='Select Map', command=self.select_map)
            select_map_button.pack(pady=10)

        # View Map button
        self.view_map_button = tk.Button(self, text='View World Map', command=self.view_map)
        self.view_map_button.pack(pady=10)

        # Check if world map exists
        if not backend_logic.veiw_world_map(app_data.session, app_data.url):
            
            # Diable button
            self.view_map_button.config(state=tk.DISABLED)

        # Entries label
        selection_label = tk.Label(self, text="Entries:")
        selection_label.pack(pady=10)

        # Create category widgets dynamically using create dynamic category widgets method
        self.create_dynamic_category_widgets()

        # Create a frame to hold the button widgets at the bottom of the main frame
        button_frame = tk.Frame(self)
        button_frame.pack(side="bottom", pady=20)

        # Back button, returns to WorldSelectionFrame
        back_button = ttk.Button(button_frame, text="Back", command=lambda: self.controller.show_frame(WorldSelectionFrame))
        back_button.pack(side=tk.LEFT, padx=20)
 
        # Create Entry button, if mode is edit
        if self.app_data.edit:
            create_button = ttk.Button(button_frame, text="Create New Entry", command=lambda: self.controller.show_frame(NewEntrySelectCategoryFrame))
            create_button.pack(side=tk.RIGHT, padx=20)

    def create_dynamic_category_widgets(self):
        """
            Dynamically creates widgets for displaying categories and entries.

            Retrieves table names from the application data session.
            Constructs frames, labels, and listboxes for each category.
            Binds double-click events on listboxes to handle entry selection.

            Note:
                This method is called to populate the frame with dynamic widgets representing categories and entries.

            Returns:
                None
        """

        if not self.app_data.session:
            return

        table_names = backend_logic.get_table_names(self.app_data.session)
        self.app_data.table_names = table_names

        num_columns = 3

        # Canvas widget to allow scrolling
        canvas_frame = tk.Frame(self)
        canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame)
        self.canvas.pack(side="left", fill="both", expand=True, padx=5)

        # Create frame to hold frames created below and create the scrollable window
        category_frames = tk.Frame(self.canvas)

        # Scroll bar widget packed to the right
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")

        # Configure the scrollbar and canvas
        self.canvas.config(yscrollcommand=scrollbar.set)

        # Bind events
        category_frames.bind("<Configure>", lambda event, canvas=self.canvas: self.on_canvas_configure(canvas))
        self.canvas.bind('<Configure>', self.on_canvas_resize)

        # Create the window within the canvas    
        self.canvas_window = self.canvas.create_window((0, 0), window=category_frames, anchor="nw")

        # Create listbox dictionary to hold the entry listboxes
        self.listbox_dict = {}

        for i in range(0, len(table_names), num_columns):
            category_frame = tk.Frame(category_frames)
            category_frame.pack(fill='both', side=tk.TOP, pady=10)

            for x in range(i, min(i + num_columns, len(table_names))):
                individual_frame = tk.Frame(category_frame)
                individual_frame.pack(side=tk.LEFT, fill='both', expand=True)  # Adjusted packing

                label = tk.Label(individual_frame, text=table_names[x].replace('_', ' ').title())
                label.pack(side=tk.TOP)

                listbox = tk.Listbox(individual_frame, height=10)
                listbox.pack(side=tk.TOP, padx=10, fill='both', expand=True)  # Adjusted packing

                listbox.bind('<Double-1>', lambda event, table_name=table_names[x]: self.on_double_click(event, table_name))

                self.listbox_dict[table_names[x]] = listbox
    

        # Update the listboxes within the frame
        self.update_listboxes()

    def update_listboxes(self):
        """
        Update the listboxes with entries retrieved from the database.

        Retrieves entry names for each table from the database using the session and URL
        stored in the AppData instance. Iterates over each table name and corresponding
        listbox in the dictionary of listboxes. For each table name, retrieves entry names
        using backend_logic.get_entry_names() and inserts them into the corresponding listbox.

        Returns:
            None
        """
        # Iterate through tables and listboxes in the frame
        for table_name, listbox in self.listbox_dict.items():

            # Retrieve entries for current table
            entries = backend_logic.get_entry_names(self.app_data.session, table_name, self.app_data.url)
            
            # Check if entries has data
            if entries:

                # Iterate through the entries
                for entry in entries:

                    # Insert the entry into the listbox
                    listbox.insert(tk.END, entry)

    def on_double_click(self, event, table_name):
        """
        Handle double-click events on listbox items.

        Retrieves the selected item from the event and uses it to get data for the entry
        from the database using backend_logic.get_data_for_entry(). Updates the selected
        entry data and category in the AppData instance. If in edit mode, navigates to the
        EditEntryFrame; otherwise, navigates to the ViewEntryFrame.

        Args:
            event (tk.Event): The event object representing the double-click event.
            table_name (str): The name of the table associated with the listbox.

        Returns:
            None
        """

        # Retrieve the entry that was double clicked
        selected_item = event.widget.get(event.widget.curselection())

        # Retrieve the data for the entry
        data = backend_logic.get_data_for_entry(self.app_data.session, selected_item, self.app_data.url)

        # Store the data in the app_data class
        self.app_data.selected_entry_data = data
        self.app_data.selected_category = table_name

        # Check for edit mode; if True pass the EditEntryFrame
        if self.app_data.edit:
            self.controller.show_frame(EditEntryFrame)
        
        # if False pass the ViewEntryFrame
        else:
            self.controller.show_frame(ViewEntryFrame)

    def select_map(self):
        """
        Opens a file dialog for the user to select a map image file. If a file is selected,
        reads the file, converts it to bytes, and calls the save_image method to handle the
        image data persistence.

        This method allows users to select an image that represents a world map, which is
        then stored in the application's backend storage system for later retrieval and display.

        Returns:
            None
        """

        # Open a file dialog to select an image file
        file_path = filedialog.askopenfilename()

        # Check for file
        if file_path:

            # Read the image file and convert it to bytes
            with open(file_path, 'rb') as file:
                image_data = file.read()

            # Display the selected image
            self.save_image(image_data)
        
        # Enable view map button
        self.view_map_button.config(state=tk.NORMAL)
    
    def save_image(self, image_data):
        """
        Saves the provided image data to the backend storage system.

        Args:
            image_data (bytes): The image data to be saved.

        This method invokes the add_world_map function from the backend logic module,
        passing the image data along with the current session and database URL stored
        in the application data.

        Returns:
            None
        """

        # Save the image using the add_world_map function
        backend_logic.add_world_map(self.app_data.session, image_data, self.app_data.url)

    def view_map(self):
        """
        Retrieves map data from the database, converts it to an image, and displays it in a new window.

        This method fetches map data from the backend logic module using the current session and database URL
        stored in the application data. It then converts the data to an image using the PIL library. Next, it creates
        a new window titled "World Map" using Tkinter's Toplevel widget. The image is displayed in the new window
        using a Tkinter Label widget.

        Returns:
            None
        """

        # Get map data from database
        map_data = backend_logic.veiw_world_map(self.app_data.session, self.app_data.url)
        
        # Convert data to image
        image = Image.open(io.BytesIO(map_data))

        # Create new window titled World Map
        map_window = tk.Toplevel(self.parent)
        map_window.title("World Map")

        # Reference image as tk.PhotoImage and save as class object to aviod garbage collection
        self.map_photo = ImageTk.PhotoImage(image)
        
        # Display photo in map window 
        label = tk.Label(map_window, image=self.map_photo)
        label.pack()

    def frame_width(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, canvas):
        """
        Adjusts the scroll region of the canvas when the size of the canvas window changes.
        """
        canvas.configure(scrollregion=canvas.bbox("all"))

    def on_canvas_resize(self, event):
        """
        Adjusts the size of the canvas window when the size of the canvas changes.
        """
        self.canvas.itemconfig(self.canvas_window, width=event.width)


class NewEntrySelectCategoryFrame(tk.Frame):
    """
    A Tkinter Frame subclass for selecting a category for a new entry within an application.

    This frame displays a list of categories to the user and allows them to select one for a new entry.
    The categories are displayed in a ListBox widget, and there are buttons for selection and navigation.

    Attributes:
        controller (misc): The controlling entity which manages frame transitions and data sharing between frames.
        app_data (object): An object that holds application-wide data, including available categories.
        listbox (tk.Listbox): The ListBox widget displaying the category options to the user.
    """

    def __init__(self, parent, controller, app_data):
        """
        Initializes the NewEntrySelectCategoryFrame with a parent widget, a controller, and application data.

        Args:
            parent (tk.Widget): The parent widget.
            controller (misc): The application's main controller that manages frame transitions and data sharing.
            app_data (object): An object containing application-wide data, such as available categories.

        The frame includes a label prompting the user to select a category, a ListBox for category selection,
        and 'Select' and 'Back' buttons for actions and navigation.
        """

        # Create frame and store the controller and AppData
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.app_data = app_data

        # Prompt label
        top_label = tk.Label(self, text='Please select a category for the new entry:')
        top_label.pack()

        # Listbox for selecting entry type
        self.listbox = tk.Listbox(self, height=len(self.app_data.table_names))
        self.listbox.pack()

        # Iterate through table names and add to listbox
        for item in self.app_data.table_names:
            self.listbox.insert(tk.END, item.replace('_', ' ').title())

        # Select button
        select_button = tk.Button(self, text='Select', command=self.select_category)
        select_button.pack(side=tk.RIGHT, padx=20)

        # Back Button, returns to WorldOverviewFrame
        back_button = tk.Button(self, text="Back", command=lambda: self.controller.show_frame(WorldOverviewFrame))
        back_button.pack(side=tk.LEFT, padx=20)

    def select_category(self):
        """
            Handles the selection of a category from the listbox and updates the application data accordingly.

            This method retrieves the user's selection from the listbox, updates the application data with the selected
            category, and triggers a frame transition to the EditEntryFrame for entry editing.

            If no selection is made, the method does nothing.
        """

        # Retrieve the selected listbox item
        selected_indices = self.listbox.curselection()

        # Check selected indices for data
        if selected_indices:

            # Retrieve selected index
            selected_item = self.listbox.get(selected_indices[0])

            # Store the selected category
            self.app_data.selected_category = selected_item.replace(' ', '_').lower()
            
            # Proceed to EditEntryFrame
            self.controller.show_frame(EditEntryFrame)


class ViewEntryFrame(tk.Frame):
    """
    A Tkinter Frame subclass for viewing details of a selected entry within an application.

    This frame displays details of a selected entry, including textual information and optionally an image.
    It provides functionality for navigating through entries, viewing images, and updating tags.

    Attributes:
        parent (tk.Widget): The parent widget.
        controller (misc): The controlling entity which manages frame transitions and data sharing between frames.
        app_data (object): An object that holds application-wide data, including selected entry details.
        text_widgets (dict): A dictionary containing text widgets for displaying entry details.
        image_data (bytes): Raw image data of the entry's photo, if available.
    """

    def __init__(self, parent, controller, app_data):
        """
        Initializes the ViewEntryFrame with a parent widget, a controller, and application data.

        Args:
            parent (tk.Widget): The parent widget.
            controller (misc): The application's main controller that manages frame transitions and data sharing.
            app_data (object): An object containing application-wide data, such as selected entry details.

        The frame includes labels and widgets for displaying entry details, including textual information and an image.
        Navigation buttons are provided for returning to the previous frame.
        """

        # Create frame and store parent, controller, and app_data
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.controller = controller
        self.app_data = app_data

        # Create variables to store as a class attribute
        self.text_widgets = {}
        self.image_data = None

        # Guarded statement to enure a world is selected
        if not self.app_data.selected_world:
            return

        # Get categories for entry by getting column names using session and selected_category
        self.column_names = backend_logic.get_column_names(self.app_data.session, self.app_data.selected_category)

        # Entry Category label
        top_label = tk.Label(self, text=f"{self.app_data.selected_category.title()} Entry:")
        top_label.pack(fill='both')

        # Name frame separate from scrollable frame
        name_frame = tk.Frame(self)
        name_frame.pack(pady=10, fill='both')
        
        # Name label
        name_label = tk.Label(name_frame, text="Name")
        name_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        # Entry name
        self.name_text = tk.Label(name_frame)
        self.name_text.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # Separator for easier scrolling
        separator = tk.Frame(self, bd=10, relief='flat', height=2, background='grey')
        separator.pack(fill='x')

        # Frame to hold the canvas widget for scrolling
        canvas_frame = tk.Frame(self)
        canvas_frame.pack(fill='both', expand=True)

        # Canvas widget for scrolling
        self.canvas = tk.Canvas(canvas_frame)
        self.canvas.pack(side='left', fill='both', expand=True)

        # Scrollbar
        self.scrollbar = tk.Scrollbar(canvas_frame, orient='vertical', command=self.canvas.yview)
        self.scrollbar.pack(side='right', fill='y')

        # Scrollable frame
        self.inner_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor='nw')

        # Assign creation of window to an id for configuring the scrolling
        self.inner_frame_id = self.canvas.create_window(0, 0, window=self.inner_frame, anchor='nw')

        # Bind the configuration of the inner_frame to on_frame_configure method
        self.inner_frame.bind("<Configure>", self.on_frame_configure)

        # Bind the configuration of the canvas to the on_canvas_confgigure method
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        # Configure the canvas yscrollcommand to the scroll bar
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Store the starting row
        current_row = 0

        # Iterate through column_names
        for column_name in self.column_names:

            # Check if column_name is in the following list and skip iteration if it is
            if column_name in ["name", "tags", "image_data"]:
                continue

            # Label for column name
            label = tk.Label(self.inner_frame, text=column_name.title())
            label.grid(row=current_row, column=0, sticky="w", padx=5, pady=5)

            # Label for data
            text = tk.Label(self.inner_frame)
            text.grid(row=current_row + 1, column=1, sticky="n", padx=5, pady=5)

            # Store the text widget in dictionary with name
            self.text_widgets[column_name] = text

            # Update current row
            current_row = current_row + 2
        
        # Image label
        image_label = tk.Label(self.inner_frame, text="Photo")
        image_label.grid(row=current_row + 2, column=0, sticky="w", padx=5, pady=5)

        # The image itself
        self.image = tk.Label(self.inner_frame)
        self.image.grid(row=current_row + 3, column=1, sticky="w", padx=5, pady=5)

        # Bind the doubleclick on the image to view_original_image method
        self.image.bind('<Double-1>', self.view_original_image)

        # Tag Listbox
        self.tag_listbox = tk.Listbox(self.inner_frame, selectmode=tk.MULTIPLE)
        
        # Check if parent is main window or TopLevel window
        if not isinstance(self.parent, tk.Toplevel):

            # Tag Label
            tag_label = tk.Label(self.inner_frame, text='Tags')
            tag_label.grid(row=current_row + 4, column=0, sticky="w", padx=5, pady=5)

            # Create list of options for filtering tags
            filter_options = ['All Categories'] + [x.replace('_', ' ').title() for x in self.app_data.table_names if x != 'tags']

            # Grid the tag listbox only if not Top Level Window
            self.tag_listbox.grid(row=current_row + 5, column=1, sticky="w", padx=5, pady=5)

            # Combobox to hold the filter options, bound to update_tag_listbox on selection
            self.tag_filter_combobox = ttk.Combobox(self.inner_frame, values=filter_options, state='readonly')
            self.tag_filter_combobox.grid(row=current_row + 5, column=2, sticky='w')
            self.tag_filter_combobox.bind("<<ComboboxSelected>>", self.update_tag_listbox)

            # Bind the on_tag_double_click command
            self.tag_listbox.bind('<Double-1>', self.on_tag_double_click)

            # Back Button bound to go_back
            back_button = tk.Button(self, text="Back", command=self.go_back)
            back_button.pack(pady=10)

        # Insert data if exists
        self.insert_data()
    
    def go_back(self):
        """
            Handles the action of going back to the previous frame.

            Clears selected entry data and switches the frame back the WorldOverviewFrame
        """

        # Empty both selected_entry_data and previous_entry_data for logic
        self.app_data.selected_entry_data = None
        self.app_data.previous_entry_data = None

        # Show WorldOverviewFrame
        self.controller.show_frame(WorldOverviewFrame)

    def insert_data(self):
        """
        Inserts data into text widgets.

        If there is data for the selected entry (which there should be in View mode), this method inserts
        it into the relating text widget. Note the text widgets are actually labels in read only mode but
        the name text was kept to avoid confusion with the label tha describes the data.
        """

        # Guarded statement to ensure the existence of data
        if not self.app_data.selected_entry_data:
            return
    
        # Save previous data to allow for frame reversal when closing the TopLevel window
        if not self.app_data.previous_entry_data:
            self.app_data.previous_entry_data = self.app_data.selected_entry_data

        # Iterate through label_widgets and insert text
        for table, textbox in self.text_widgets.items():
            textbox.configure(text=self.app_data.selected_entry_data[table])

        # Inputs the name into the name label
        self.name_text.configure(text=self.app_data.selected_entry_data['name'])

        # Inputs image data if it exists
        if self.app_data.selected_entry_data['image_data']:
            self.image_data = self.app_data.selected_entry_data['image_data']
            self.display_image(self.image_data)

        # Clear the Listbox
        self.tag_listbox.delete(0, tk.END)

        # Get list of tags
        existing_tags = self.app_data.selected_entry_data['tags'].split(', ')

        # Iterate through existing tags
        for tag in existing_tags:

            # Ignore iteration if tag is own name (to avoid an entry being tagged with itself)
            if tag == self.app_data.selected_entry_data['name']:
                continue

            # Insert current tag into list box
            self.tag_listbox.insert(tk.END, tag)

    def on_frame_configure(self, event):
        """
        Handles the canvas frame configuration change event.

        Adjusts the scroll region of the canvas to accommodate changes in the inner frame's size.
        """

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """
        Adjusts the inner frame's width in response to canvas configuration changes.

        Args:
            event (tk.Event): The event object triggered by canvas configuration changes.

        This method is bound to the <Configure> event of the canvas widget. It adjusts the width of the inner frame
        (self.inner_frame) within the canvas to match the canvas's width, ensuring that the inner frame fills the
        available space horizontally.
        """

        self.canvas.itemconfig(self.inner_frame_id, width=event.width)

    def display_image(self, image_data):
        """
        Displays an image within the ViewEntryFrame.

        Args:
            image_data (bytes): The raw image data to be displayed.

        This method opens the provided image using the Python Imaging Library (PIL), resizes it to fit the GUI if
        necessary, converts it to the Tkinter PhotoImage format, and displays it in a label widget (self.image) within
        the ViewEntryFrame.
        """

        # Open the image using PIL
        image = Image.open(io.BytesIO(image_data))

        # Resample using Image.Resampling.LANCZOS for high-quality downsampling
        image = image.resize((200, 200), Image.Resampling.LANCZOS)

        # Convert the image to Tkinter PhotoImage format
        photo = ImageTk.PhotoImage(image)

        # Display the image in a label
        self.image.configure(image=photo)

        # Keep a reference to avoid garbage collection
        self.image.image = photo

    def view_original_image(self, event):
        """
        Displays the original image in a new window when the image label is double-clicked.

        Args:
            event (tk.Event): The event object representing the double-click event.

        If image data exists (self.image_data), this method opens the original image using the Python Imaging Library
        (PIL) and displays it in a new Toplevel window titled "Original Image". If no image data exists, it shows an
        information messagebox indicating that no image data is available.
        """

        # Check if the image data exists
        if hasattr(self, 'image_data'):

            # Open the original image using PIL
            original_image = Image.open(io.BytesIO(self.image_data))

            # Create a new window to display the original image
            original_window = tk.Toplevel(self.parent)
            original_window.title("Original Image")

            # Create a label to display the original image
            original_image_label = tk.Label(original_window)

            # Convert the original image to Tkinter PhotoImage format
            original_photo = ImageTk.PhotoImage(original_image)

            # Display the original image in the label
            original_image_label.configure(image=original_photo)
            original_image_label.pack()

            # Keep a reference to avoid garbage collection
            original_image_label.image = original_photo

        else:

            # If image data does not exist, show a message
            messagebox.showinfo("No Image", "No image data available.")

    def update_tag_listbox(self, event):
        """
        Updates the tag listbox based on the selected category in the tag filter combobox.

        Args:
            event (tk.Event): The event object representing the selection change event in the tag filter combobox.

        This method updates the tag listbox (self.tag_listbox) with tags filtered based on the selected category in the
        tag filter combobox (self.tag_filter_combobox).
        """

        # Retrieve the selected option from the tag filter combobox
        selected_option = self.tag_filter_combobox.get().replace(' ', '_').lower()

        # Retrieve tag list from selected data and stript any unwanted spaces
        tag_list = self.app_data.selected_entry_data['tags'].split(',')
        tag_list = [tag.strip() for tag in tag_list]

        # Filter the tags using the backend logic filtering function
        filtered_tags = backend_logic.filter_tag_list_by_table(self.app_data.session, self.app_data.url, tag_list, selected_option)
        
        # Delete all tags in listbox
        self.tag_listbox.delete(0, tk.END)
        
        # Iterate through the filtered tags
        for tag in filtered_tags:

            # Insert the current tag
            self.tag_listbox.insert(tk.END, tag)

    def on_tag_double_click(self, event):
        """
        Handles double-click events on tags in the tag listbox.

        Args:
            event (tk.Event): The event object representing the double-click event.

        This method retrieves information about the selected tag, such as entry data and category, and displays it in a
        new Toplevel window using ViewEntryFrame.
        """

        # Get the selected tag from the tag_listbox
        selected_index = self.tag_listbox.curselection()
        selected_tag = self.tag_listbox.get(self.tag_listbox.curselection())

        # Retrieve information about the selected tag
        self.app_data.selected_entry_data = backend_logic.get_data_for_entry(self.app_data.session, selected_tag, self.app_data.url)
        self.app_data.selected_category = backend_logic.get_tag_location(self.app_data.session, selected_tag, self.app_data.url)

        # Create a new Toplevel window and configure size and closing
        new_window = tk.Toplevel(self.parent)
        new_window.geometry("700x600")
        new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_window_close(new_window))

        # Create a new instance of EditEntryFrame with the info from the selected tag
        new_frame = ViewEntryFrame(new_window, self.controller, self.app_data)

        # Pack the EditEntryFrame into the new window
        new_frame.pack(expand=True, fill="both", pady=20, padx=20)

        # Deselect the tag after opening the new window
        self.tag_listbox.selection_clear(selected_index)

    def on_window_close(self, window):
        """
        Handles the closing of the Toplevel window and resets the state of the application.

        Args:
            window (tk.Toplevel): The Toplevel window to be closed.

        This method unbinds mouse wheel events from the canvas, destroys the provided window, and resets the application
        state to the previously selected entry data and category.
        """

        # Destroy the window
        window.destroy()

        # Retrieve the previous data as the selected data
        self.app_data.selected_entry_data = self.app_data.previous_entry_data

        # Set the previous data to None
        self.app_data.previous_entry_data = None

        # Update the selected category with the selected entry data
        self.app_data.selected_category = backend_logic.get_tag_location(self.app_data.session, self.app_data.selected_entry_data['name'], self.app_data.url)

        # Instantiate new ViewEntryFrame with the selected entry data
        new_frame = ViewEntryFrame(self.parent, self.controller, self.app_data)

        # Show new instance of ViewEntryFrame
        self.controller.show_frame(new_frame)


class EditEntryFrame(tk.Frame):
    """
    A frame for editing and adding new entries.

    Args:
        parent (tk.Tk or tk.Toplevel): The parent widget.
        controller (tk.Tk): The main application controller.
        app_data: An object containing application data.

    This frame provides functionality for editing existing entries or adding new ones. It includes fields for entering
    data, selecting tags, adding images, and saving or deleting entries.
    """

    def __init__(self, parent, controller, app_data):
        """
        Initializes the EditEntryFrame.

        Args:
            parent (tk.Tk or tk.Toplevel): The parent widget.
            controller (tk.Tk): The main application controller.
            app_data: An object containing application data.

        This method sets up the user interface for editing or adding new entries, including text fields, canvas for
        scrolling, image display, tag selection, and buttons for saving or deleting entries.
        """

        # Create frame and save args as properties of frame
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.controller = controller
        self.app_data = app_data
        self.text_widgets = {}
        self.image_data = None

        # If no selected_world end method
        if not self.app_data.selected_world:
            return

        # Retrieve column names using the backend logic
        self.column_names = backend_logic.get_column_names(self.app_data.session, self.app_data.selected_category)

        # Top label
        top_label = tk.Label(self, text=f"New {self.app_data.selected_category.title()} Entry:")
        top_label.pack(pady=5)

        # Name label
        name_label = tk.Label(self, text="Name")
        name_label.pack(pady=5)

        # Name text
        self.name_text = tk.Entry(self)
        self.name_text.pack(pady=5)

        # Canvas frame
        canvas_frame = tk.Frame(self)
        canvas_frame.pack(pady=5, fill='both', expand=True)

        # Canvas to allow scrolling
        self.canvas = tk.Canvas(canvas_frame)
        self.canvas.pack(side='left', fill='both', expand=True)

        # Scrollbar
        self.scrollbar = tk.Scrollbar(canvas_frame, orient='vertical', command=self.canvas.yview)
        self.scrollbar.pack(side='right', fill='y')

        # Configure canvas to y-scroll
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create inner_frame and place it on the canvas
        self.inner_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor='nw')

        # Store the creation of the window as a variable for later calls
        self.inner_frame_id = self.canvas.create_window(0, 0, window=self.inner_frame, anchor='nw')

        # Bind the creatino of the inner_frame to on_frame_configure
        self.inner_frame.bind("<Configure>", self.on_frame_configure)

        # Bind the creation of the canvas to on_canvas_creation
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        # Finally, configure the scrollbar to the canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Iterate through column_names
        for column_name in self.column_names:

            # if column name in list, skip iteration
            if column_name in ["tags", "name", "image_data"]:
                continue

            # Column name label
            label = tk.Label(self.inner_frame, text=column_name.title())
            label.pack(pady=5)

            # Text frame label
            text_frame = tk.Frame(self.inner_frame)
            text_frame.pack(pady=10)

            # Scrollbar for text box
            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side=tk.RIGHT, fill='y')

            # Textbox
            text = tk.Text(text_frame, wrap='word', yscrollcommand=scrollbar.set, height=10)
            text.pack(side=tk.LEFT)

            # Store the textbox in a dictionary wth the column_name being the key
            self.text_widgets[column_name] = text
        
        # Image label
        image_label = tk.Label(self.inner_frame, text="Photo")
        image_label.pack(pady=5)

        # Label to show image
        self.image = tk.Label(self.inner_frame)
        self.image.pack(pady=5)

        # Bind the double click of the image to view_original_image
        self.image.bind('<Double-1>', self.view_original_image)

        # Select image button
        select_image_btn = tk.Button(self.inner_frame, text="Select Image", command=self.select_image)
        select_image_btn.pack(pady=5)

        # Tag label
        tag_label = tk.Label(self.inner_frame, text='Tags')
        tag_label.pack(pady=5)

        # Retrieve all tags from tag table
        tags = backend_logic.get_all_tags(self.app_data.session, self.app_data.url)

        # if we are editing an existing entry
        if self.app_data.selected_entry_data:          

            # If name in tags
            if self.app_data.selected_entry_data['name'] in tags:

                # Remove name in tags
                tags.remove(self.app_data.selected_entry_data['name'])

        # Combobox for tags
        self.tag_combobox = ttk.Combobox(self.inner_frame, values=tags, state='readonly')
        self.tag_combobox.pack(pady=5)

        # Add Frame to pack the tag_listbox and filter combo
        tag_frame = tk.Frame(self.inner_frame)
        tag_frame.pack(pady=10)

        # Listbox to display existing tags
        self.tag_listbox = tk.Listbox(tag_frame, selectmode=tk.MULTIPLE)
        self.tag_listbox.pack(side='left', padx=5)

        filter_options = ['All Categories'] + [x.replace('_', ' ').title() for x in self.app_data.table_names if x != 'tags']

        self.tag_filter_combobox = ttk.Combobox(tag_frame, values=filter_options, state='readonly')
        self.tag_filter_combobox.pack(side='right', padx=5)
        self.tag_filter_combobox.bind("<<ComboboxSelected>>", self.update_tag_listbox)

        # Bind the on_tag_double_click command
        self.tag_listbox.bind('<Double-1>', self.on_tag_double_click)

        # Bind the <Return> key to the add_tag function
        self.tag_combobox.bind('<Return>', self.add_tag)

        delete_entry_button = tk.Button(self.inner_frame, text="Delete Entry", command=self.delete_entry)
        delete_entry_button.pack(pady=5)

        button_frame = tk.Frame(self)
        button_frame.pack(side='bottom', pady=10)

        save_button = tk.Button(button_frame, text='Save', command=self.save)
        save_button.pack(side=tk.RIGHT, padx=10)

        back_button = tk.Button(button_frame, text='Back', command=self.go_back)
        back_button.pack(side=tk.LEFT, padx=10)

        self.insert_data_if_exists()

    def go_back(self):
        """
        Returns to the previous frame (WorldOverviewFrame).

        This method resets the selected entry data and category, then shows the WorldOverviewFrame.
        """

        # Empty the selected entry data and previous entry data in the data class
        self.app_data.selected_entry_data = None
        self.app_data.previous_entry_data = None

        # Go back a frame
        self.controller.show_frame(WorldOverviewFrame)

    def save(self):
        """
        Saves the edited or new entry.

        This method gathers data from the input fields, tags, and image, then saves the entry using backend logic. After
        saving, it navigates back to the WorldOverviewFrame.
        """

        # Instantiate an empty dictionary to generate the data to save
        data_to_write = {}

        # Insert name in dictionary
        data_to_write['name'] = self.name_text.get()

        # Iterate through column_names
        for column_name in self.column_names:
            
            # Skip iteration if column name in list
            if column_name in ['tags', 'name', 'image_data']:
                continue

            # Save data from named text widget and save in dictionary
            data_to_write[column_name] = self.text_widgets[column_name].get("1.0", tk.END).strip()

        # Get selected tags from the Listbox
        selected_tags = self.tag_listbox.get(0, tk.END)

        # Convert the list of tags to a comma-separated string
        data_to_write['tags'] = ', '.join(selected_tags)

        # Check for image_data
        if self.image_data:

            # Include the image data in the data_to_write dictionary
            data_to_write['image_data'] = self.image_data

        # Save dictionary in database using backend logic
        backend_logic.add_data_to_table(self.app_data.session, self.app_data.selected_category, data_to_write, self.app_data.url)
        
        # Show WorldOverviewFrame
        self.controller.show_frame(WorldOverviewFrame)

    def delete_entry(self):
        """
        Deletes the selected entry.

        This method removes the selected entry using backend logic and navigates back to the WorldOverviewFrame.
        """

        # Get name of entry to remove
        data_to_remove = self.name_text.get()

        # Remove entry using backend logic
        backend_logic.remove_entry(self.app_data.session, self.app_data.selected_category, data_to_remove, self.app_data.url)

        # Show WorldOverviewFrame
        self.controller.show_frame(WorldOverviewFrame)

    def insert_data_if_exists(self):
        """
        Inserts existing data into the entry fields if editing an existing entry.

        If an existing entry is being edited, this method populates the text fields, image display, and tag listbox with
        existing data.
        """

        # Check for selected entry data, if None exit method
        if not self.app_data.selected_entry_data:
            return
        
        # Check for previous entry data
        if not self.app_data.previous_entry_data:

            # Set selected entry data to previous entry data
            self.app_data.previous_entry_data = self.app_data.selected_entry_data

        # Iterate through text_boxes in self.text_widgets, unpacking them into table and textbox
        for table, textbox in self.text_widgets.items():

            # Insert data into textbox
            textbox.insert(tk.END, self.app_data.selected_entry_data[table])

        # Insert name into name_text
        self.name_text.insert(tk.END, self.app_data.selected_entry_data['name'])

        # Check for image data
        if self.app_data.selected_entry_data['image_data']:
            
            # Store image data as an attribute of the class to avoid garbage collection
            self.image_data = self.app_data.selected_entry_data['image_data']

            # Display image using method
            self.display_image(self.image_data)

        # Clear the Listbox
        self.tag_listbox.delete(0, tk.END)

        # Get list of tags
        existing_tags = self.app_data.selected_entry_data['tags'].split(', ')
        
        # Iterate through existing tags
        for tag in existing_tags:

            # Skip if tag is own name
            if tag == self.app_data.selected_entry_data['name']:
                continue

            # Insert tag into listbox
            self.tag_listbox.insert(tk.END, tag)

    def add_tag(self, event):
        """
        Adds a tag to the entry.

        Args:
            event (tk.Event): The event object representing the return key press event in the tag combobox.

        This method adds a tag from the combobox to the tag listbox when the return key is pressed.
        """

        # Get selected tag
        selected_tag = self.tag_combobox.get()
        
        # If tag listbox size is 1 and the first entry is blank
        if self.tag_listbox.size() == 1 and self.tag_listbox.get(0) == '':
            
            # Delete the empty tag
            self.tag_listbox.delete(0)

            # Insert selected tag
            self.tag_listbox.insert(0, selected_tag)
        
        # Else if selected_tag is not none and is not in tag_listbox
        elif selected_tag and selected_tag not in self.tag_listbox.get(0, tk.END):
            
            # Insert selected tag at the end of the list_box
            self.tag_listbox.insert(tk.END, selected_tag)
            
            # Clear the combobox after adding the tag
            self.tag_combobox.set("")

    def on_tag_double_click(self, event):
        """
        Opens a selected tag for editing.

        Args:
            event (tk.Event): The event object representing the double-click event on a tag in the tag listbox.

        This method retrieves information about the selected tag and opens it for editing in a new EditEntryFrame
        window.
        """

        # Get the selected tag from the tag_listbox
        selected_index = self.tag_listbox.curselection()
        selected_tag = self.tag_listbox.get(self.tag_listbox.curselection())

        # Retrieve information about the selected tag
        self.app_data.selected_entry_data = backend_logic.get_data_for_entry(self.app_data.session, selected_tag, self.app_data.url)
        self.app_data.selected_category = backend_logic.get_tag_location(self.app_data.session, selected_tag, self.app_data.url)

        # Create a new Toplevel window
        new_window = tk.Toplevel(self.parent)
        new_window.geometry("700x600")
        new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_window_close(new_window))

        # Create a new instance of EditEntryFrame with the info from the selected tag
        new_frame = ViewEntryFrame(new_window, self.controller, self.app_data)

        # Pack the EditEntryFrame into the new window
        new_frame.pack(expand=True, fill="both", pady=20, padx=20)

        # Deselect the tag after opening the new window
        self.tag_listbox.selection_clear(selected_index)

    def on_frame_configure(self, event):
        """
        Configures the canvas frame.

        Args:
            event (tk.Event): The event object representing the configuration change event in the canvas.

        This method adjusts the canvas frame to fit the canvas contents.
        """
        # Configure the scrollregion to be the canvas bbox
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """
        Configures the canvas.

        Args:
            event (tk.Event): The event object representing the configuration change event in the canvas.

        This method adjusts the canvas width in response to configuration changes.
        """
        self.canvas.itemconfig(self.inner_frame_id, width=event.width)

    def select_image(self):
        """
        Opens a file dialog to select an image.

        This method opens a file dialog to select an image file and displays the selected image.
        """

        # Open a file dialog to select an image file
        file_path = filedialog.askopenfilename()

        # If there is a file_path
        if file_path:

            # Read the image file and convert it to bytes
            with open(file_path, 'rb') as file:
                self.image_data = file.read()
            
            # Display the selected image
            self.display_image(self.image_data)

    def display_image(self, image_data):
        """
        Displays an image.

        Args:
            image_data (bytes): The raw image data.

        This method displays the selected image within the EditEntryFrame.
        """

        # Open the image using PIL
        image = Image.open(io.BytesIO(image_data))
        
        # Resize the image if necessary to fit in the GUI
        # Use Image.Resampling.LANCZOS for high-quality downsampling
        image = image.resize((200, 200), Image.Resampling.LANCZOS)
        
        # Convert the image to Tkinter PhotoImage format
        photo = ImageTk.PhotoImage(image)
        
        # Display the image in a label
        self.image.configure(image=photo)

        # Keep a reference to avoid garbage collection
        self.image.image = photo  

    def view_original_image(self, event):
        """
        Displays the original image.

        Args:
            event (tk.Event): The event object representing the double-click event on the image label.

        This method displays the original image in a new window when the image label is double-clicked.
        """

        # Check if the image data exists
        if hasattr(self, 'image_data'):

            # Open the original image using PIL
            original_image = Image.open(io.BytesIO(self.image_data))

            # Create a new window to display the original image
            original_window = tk.Toplevel(self.parent)
            original_window.title("Original Image")

            # Create a label to display the original image
            original_image_label = tk.Label(original_window)

            # Convert the original image to Tkinter PhotoImage format
            original_photo = ImageTk.PhotoImage(original_image)

            # Display the original image in the label
            original_image_label.configure(image=original_photo)
            original_image_label.image = original_photo  # Keep a reference to avoid garbage collection
            original_image_label.pack()

        # If no image_data
        else:

            # If image data does not exist, show a message
            messagebox.showinfo("No Image", "No image data available.")

    def update_tag_listbox(self, event):
        """
        Updates the tag listbox based on the selected category.

        Args:
            event (tk.Event): The event object representing the selection change event in the tag filter combobox.

        This method updates the tag listbox based on the selected category in the tag filter combobox.
        """

        # Get selected filter option
        selected_option = self.tag_filter_combobox.get().replace(' ', '_').lower()

        # Get the entire tag list and strip the excess whitespace from rach item in the list
        tag_list = self.app_data.selected_entry_data['tags'].split(',')
        tag_list = [x.strip() for x in tag_list]

        # Get list of filtered tags using backend logic
        filtered_tags = backend_logic.filter_tag_list_by_table(self.app_data.session, self.app_data.url, tag_list, selected_option)
        
        # Delete all entries in the listbox
        self.tag_listbox.delete(0, tk.END)
        
        # Iterate through tags
        for tag in filtered_tags:

            # Insert tag into listbox
            self.tag_listbox.insert(tk.END, tag)

    def on_window_close(self, window):
        """
        Handles the closing of the Toplevel window.

        Args:
            window (tk.Toplevel): The Toplevel window to be closed.

        This method unbinds mouse wheel events from the canvas, destroys the provided window, and resets the application
        state to the previously selected entry data and category.
        """
        
        # Destroy the window
        window.destroy()

        # Set previous entry data to selected entry data
        self.app_data.selected_entry_data = self.app_data.previous_entry_data
        
        # Set None to previous entry data
        self.app_data.previous_entry_data = None
        
        # Reset the selected category
        self.app_data.selected_category = backend_logic.get_tag_location(self.app_data.session, self.app_data.selected_entry_data['name'], self.app_data.url)

        # Instantiate new EditEntryFrame
        new_frame = EditEntryFrame(self.parent, self.controller, self.app_data)

        # Show new frame
        self.controller.show_frame(new_frame)    


class WorldBuilderApp(tk.Tk):
    """
    Main application class for the World Builder App.

    This class represents the main application window and handles the creation of frames, menu bar, and window events.
    """

    def __init__(self):
        """
        Initializes the WorldBuilderApp.

        This method sets up the main application window, initializes application data, creates the menu bar,
        initializes frame classes, and sets the initial frame to display. It also binds the closing event to the
        on_closing method.
        """

        # Set self to a a tk.Tk
        tk.Tk.__init__(self)

        # Set the title for the window
        self.title("World Builder App")

        # Set size of window
        self.geometry("700x600")

        # Instantiate the app data class
        self.app_data = AppData()

        # Create the menu bar
        self.create_menu_bar()

        # Create list of frame classes
        frame_classes = [WorldSelectionFrame, WorldOverviewFrame, NewEntrySelectCategoryFrame, ViewEntryFrame, EditEntryFrame]

        # Create dictionary of frames with the names as the key and no instance of the class saved
        self.frames = {frame_class: None for frame_class in frame_classes}

        # Track the current frame
        self.current_frame = None

        # Show frame WorldSelectionFrame
        self.show_frame(WorldSelectionFrame)

        # Bind the closing event to the on_closing method
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Bind scroll events to the parent window
        UniversalHandler.bind_scroll_event(self)

    def create_menu_bar(self):
        """
        Creates the menu bar for the application.

        This method creates a menu bar with a file menu that includes an option to exit the application.
        """

        # Create a menu bar
        menubar = tk.Menu(self)

        # Create a file menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.on_closing)
        menubar.add_cascade(label="File", menu=file_menu)

        # Add the menu bar to the application window
        self.config(menu=menubar)

    def on_closing(self):
        """
        Handles the closing event of the application window.

        This method prompts the user to confirm if they want to quit the application. If confirmed, it closes the
        database session (if exists) and destroys the main application window.
        """

        # Run messagebox to ask for if the user wants to quit
        if messagebox.askokcancel("Quit", "Do you want to quit?"):

            # Check for session
            if self.app_data.session:

                # Close session
                self.app_data.session.close()
            
            # Destroy main window
            self.destroy()

    def show_frame(self, cont):
        """
        Displays the specified frame in the main application window.

        Args:
            cont: The class or instance of the frame to be displayed.

        This method displays the specified frame in the main application window, hides the current frame (if exists),
        updates the current frame, and adjusts the window size accordingly. Additionally, it sets specific dimensions
        for frames of type EditEntryFrame or ViewEntryFrame.
        """

        # Check for instance of frame
        if isinstance(cont, tk.Frame):

            # If an instance of the frame is provided, use it directly
            frame = cont

        else:
            # If a frame class is provided, create a new instance
            frame = cont(self, self, self.app_data)
            self.frames[cont] = frame

        # Save the class of the current frame
        self.app_data.previous_frame = cont  # <-- Store the class, not the instance

        # Hide the current frame
        if self.current_frame:
            self.current_frame.pack_forget()

        # Place the frame inside the main window using pack with padding
        frame.pack(expand=True, fill="both", pady=20)

        # Update the current frame
        self.current_frame = frame

        # If the frame has the update_label_text method
        if hasattr(frame, "update_label_text"):
            frame.update_label_text()
       


if __name__ == "__main__":
    backend_logic.find_database()
    app = WorldBuilderApp()
    app.mainloop()
