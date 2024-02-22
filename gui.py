import os
import io
import tkinter as tk
import backend_logic as backend_logic
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

        # Determine the directory containing the database files
        script_directory = Path(os.path.dirname(os.path.abspath(__file__)))
        path = script_directory / "db"

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
        update_combobox(): Updates the Combobox widget with new values.
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
        view_map_button = tk.Button(self, text='View World Map', command=self.view_map)
        view_map_button.pack(pady=10)

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

        # If not session exists, end the method
        if not self.app_data.session:
            return
        
        # Store table names from the current session
        table_names = backend_logic.get_table_names(self.app_data.session)
        self.app_data.table_names = table_names
    
        # Define the number of columns in the layout
        num_columns = 3

        # Canvas widget to allow scrolling
        canvas_frame = tk.Frame(self)
        canvas_frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(canvas_frame)
        canvas.pack(side="left", fill="both", expand=True, padx=5)

        # Scroll bar widget packed to the right
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        # Create frame to hold frames created below and create the scrollable window
        category_frames = tk.Frame(canvas)
        canvas.create_window((0, 0), window=category_frames, anchor="nw")

        # Create listbox dictionary to hold the entry listboxes
        self.listbox_dict = {}

        # Iterate through 0 to the length of the table names stepping the number of columns
        for i in range(0, len(table_names), num_columns):

            # Create category frame to hold the frames generated below
            category_frame = tk.Frame(category_frames)
            category_frame.pack(fill='both', side=tk.TOP, pady=10)

            # Iterate through i to lowest of i + number of columns of the total length of table names
            for x in range(i, min(i + num_columns, len(table_names))):

                # Create the overall frame for the label and listbox for entries in a horizontal line
                individual_frame = tk.Frame(category_frame)
                individual_frame.pack(side=tk.LEFT)

                # Category label
                label = tk.Label(individual_frame, text=table_names[x].replace('_', ' ').title())
                label.pack(side=tk.TOP)

                # Category listbox
                listbox = tk.Listbox(individual_frame, height=10)
                listbox.pack(side=tk.TOP, padx=10, fill='both', expand=True)

                # Bind the listbox doubleclick to the on_double_click method
                listbox.bind('<Double-1>', lambda event, table_name=table_names[x]: self.on_double_click(event, table_name))

                # Save the listbox and name in dictionary
                self.listbox_dict[table_names[x]] = listbox

                # Configure the canvas to update the vertical scrollbar
                canvas.configure(yscrollcommand=scrollbar.set)

                # Bind the MouseWheel event to scroll the canvas vertically
                canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))

                # Update the canvas tasks while the program is idle
                canvas.update_idletasks()

                # Configure the canvas to fit the bounding box of all elements
                canvas.config(scrollregion=canvas.bbox("all"))

                # Configure the packing of the canvas within its container widget
                canvas.pack_configure(side="left", fill="both", expand=True, padx=(0, scrollbar.winfo_width()))

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


class NewEntrySelectCategoryFrame(tk.Frame):
    def __init__(self, parent, controller, app_data):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.app_data = app_data

        top_label = tk.Label(self, text='Please select a category for the new entry:')
        top_label.pack()

        self.listbox = tk.Listbox(self, height=len(self.app_data.table_names))
        self.listbox.pack()

        for item in self.app_data.table_names:
            self.listbox.insert(tk.END, item.replace('_', ' ').title())

        select_button = tk.Button(self, text='Select', command=self.select_category)
        select_button.pack(side=tk.RIGHT, padx=20)

        back_button = tk.Button(self, text="Back", command=lambda: self.controller.show_frame(WorldOverviewFrame))
        back_button.pack(side=tk.LEFT, padx=20)

    def select_category(self):
         selected_indices = self.listbox.curselection()

         if selected_indices:
             selected_item = self.listbox.get(selected_indices[0])
             self.app_data.selected_category = selected_item.replace(' ', '_').lower()
             self.controller.show_frame(EditEntryFrame)


class ViewEntryFrame(tk.Frame):
    def __init__(self, parent, controller, app_data):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.controller = controller
        self.app_data = app_data
        self.text_widgets = {}
        self.image_data = None
        self.canvas_widgets = []

        if not self.app_data.selected_world:
            return

        self.column_names = backend_logic.get_column_names(self.app_data.session, self.app_data.selected_category)

        top_label = tk.Label(self, text=f"{self.app_data.selected_category.title()} Entry:")
        top_label.pack(fill='both')

        name_frame = tk.Frame(self)
        name_frame.pack(pady=10, fill='both')
        
        name_label = tk.Label(name_frame, text="Name")
        name_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.name_text = tk.Label(name_frame)
        self.name_text.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        separator = tk.Frame(self, bd=10, relief='flat', height=2, background='grey')
        separator.pack(fill='x')

        canvas_frame = tk.Frame(self)
        canvas_frame.pack(fill='both', expand=True)

        self.canvas = tk.Canvas(canvas_frame)
        self.canvas.pack(side='left', fill='both', expand=True)

        self.canvas_widgets.append(self.canvas)

        self.scrollbar = tk.Scrollbar(canvas_frame, orient='vertical', command=self.canvas.yview)
        self.scrollbar.pack(side='right', fill='y')

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.inner_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor='nw')

        self.inner_frame_id = self.canvas.create_window(0, 0, window=self.inner_frame, anchor='nw')

        self.inner_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind_all("<MouseWheel>", lambda event: self.on_mouse_wheel(event, self.canvas))

        current_row = 3

        for i in self.column_names[1:-1]:
            if i == "tags":
                continue

            label = tk.Label(self.inner_frame, text=i.capitalize())
            label.grid(row=current_row, column=0, sticky="w", padx=5, pady=5)

            text_frame = tk.Frame(self.inner_frame)
            text_frame.grid(row=current_row + 1, column=1, sticky="n", padx=5, pady=5)

            text = tk.Label(text_frame)
            text.pack()

            self.text_widgets[i] = text

            current_row = current_row + 2
        
        image_label = tk.Label(self.inner_frame, text="Photo")
        image_label.grid(row=current_row + 2, column=0, sticky="w", padx=5, pady=5)

        self.image = tk.Label(self.inner_frame)
        self.image.grid(row=current_row + 3, column=1, sticky="w", padx=5, pady=5)

        self.image.bind('<Double-1>', self.view_original_image)

        tag_label = tk.Label(self.inner_frame, text='Tags')
        self.tag_listbox = tk.Listbox(self.inner_frame, selectmode=tk.MULTIPLE)
        
        if not isinstance(self.parent, tk.Toplevel):
            tag_label.grid(row=current_row + 4, column=0, sticky="w", padx=5, pady=5)

            filter_options = ['All Categories'] + [x.replace('_', ' ').title() for x in self.app_data.table_names if x != 'tags']

            self.tag_listbox.grid(row=current_row + 5, column=1, sticky="w", padx=5, pady=5)
            self.tag_filter_combobox = ttk.Combobox(self.inner_frame, values=filter_options, state='readonly')
            self.tag_filter_combobox.grid(row=current_row + 5, column=2, sticky='w')
            self.tag_filter_combobox.bind("<<ComboboxSelected>>", self.update_tag_listbox)

            # Bind the on_tag_double_click command
            self.tag_listbox.bind('<Double-1>', self.on_tag_double_click)

            back_button = tk.Button(self, text="Back", command=self.go_back)
            back_button.pack(pady=10)

        self.insert_data_if_exists()
    
    def go_back(self):
        self.app_data.selected_entry_data = None
        self.app_data.previous_entry_data = None
        self.controller.show_frame(WorldOverviewFrame)

    def insert_data_if_exists(self):
        if not self.app_data.selected_entry_data:
            return
    
        if not self.app_data.previous_entry_data:
            self.app_data.previous_entry_data = self.app_data.selected_entry_data

        for table, textbox in self.text_widgets.items():
            textbox.configure(text=self.app_data.selected_entry_data[table])

        self.name_text.configure(text=self.app_data.selected_entry_data['name'])

        if self.app_data.selected_entry_data['image_data'] != None:
            self.image_data = self.app_data.selected_entry_data['image_data']
            self.display_image(self.image_data)

        # Clear the Listbox
        self.tag_listbox.delete(0, tk.END)

        # Populate the Listbox with existing tags
        existing_tags = self.app_data.selected_entry_data['tags'].split(', ')

        for tag in existing_tags:
            if tag == self.app_data.selected_entry_data['name']:
                continue
            self.tag_listbox.insert(tk.END, tag)


    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.inner_frame_id, width=event.width)

    def on_mouse_wheel(self, event, canvas):
        # Adjust the view of the canvas when the mouse wheel is scrolled
        canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def display_image(self, image_data):
        # Open the image using PIL
        image = Image.open(io.BytesIO(image_data))
        # Resize the image if necessary to fit in the GUI
        # Use Image.Resampling.LANCZOS for high-quality downsampling
        image = image.resize((200, 200), Image.Resampling.LANCZOS)
        # Convert the image to Tkinter PhotoImage format
        photo = ImageTk.PhotoImage(image)
        # Display the image in a label
        self.image.configure(image=photo)
        self.image.image = photo  # Keep a reference to avoid garbage collection

    def view_original_image(self, event):
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

        else:
            # If image data does not exist, show a message
            messagebox.showinfo("No Image", "No image data available.")

    def update_tag_listbox(self, event):
        selected_option = self.tag_filter_combobox.get().replace(' ', '_').lower()

        tag_list = self.app_data.selected_entry_data['tags'].split(',')
        tag_list = [x.strip() for x in tag_list]

        filtered_tags = backend_logic.filter_tag_list_by_table(self.app_data.session, self.app_data.url, tag_list, selected_option)
        
        self.tag_listbox.delete(0, tk.END)
        
        for tag in filtered_tags:
            self.tag_listbox.insert(tk.END, tag)

    def on_tag_double_click(self, event):
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

    def on_window_close(self, window):
        self.canvas.unbind_all("<MouseWheel>")
        # Destroy the window
        window.destroy()

        self.app_data.selected_entry_data = self.app_data.previous_entry_data
        self.app_data.previous_entry_data = None
        self.app_data.selected_category = backend_logic.get_tag_location(self.app_data.session, self.app_data.selected_entry_data['name'], self.app_data.url)

        new_frame = ViewEntryFrame(self.parent, self.controller, self.app_data)

        self.controller.show_frame(new_frame)


class EditEntryFrame(tk.Frame):
    def __init__(self, parent, controller, app_data):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.controller = controller
        self.app_data = app_data
        self.text_widgets = {}
        self.image_data = None

        if not self.app_data.selected_world:
            return

        self.column_names = backend_logic.get_column_names(self.app_data.session, self.app_data.selected_category)

        top_label = tk.Label(self, text=f"New {self.app_data.selected_category.title()} Entry:")
        top_label.pack(pady=5)

        name_label = tk.Label(self, text="Name")
        name_label.pack(pady=5)

        self.name_text = tk.Entry(self)
        self.name_text.pack(pady=5)

        canvas_frame = tk.Frame(self)
        canvas_frame.pack(pady=5, fill='both', expand=True)

        self.canvas = tk.Canvas(canvas_frame)
        self.canvas.pack(side='left', fill='both', expand=True)

        self.scrollbar = tk.Scrollbar(canvas_frame, orient='vertical', command=self.canvas.yview)
        self.scrollbar.pack(side='right', fill='y')

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.inner_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor='nw')

        self.inner_frame_id = self.canvas.create_window(0, 0, window=self.inner_frame, anchor='nw')

        self.inner_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

        for i in self.column_names[1:-1]:
            if i == "tags":
                continue

            label = tk.Label(self.inner_frame, text=i.capitalize())
            label.pack(pady=5)

            text_frame = tk.Frame(self.inner_frame)
            text_frame.pack(pady=10)

            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.pack(side=tk.RIGHT, fill='y')

            text = tk.Text(text_frame, wrap='word', yscrollcommand=scrollbar.set, height=10)
            text.pack(side=tk.LEFT)

            self.text_widgets[i] = text
        
        image_label = tk.Label(self.inner_frame, text="Photo")
        image_label.pack(pady=5)

        self.image = tk.Label(self.inner_frame)
        self.image.pack(pady=5)

        self.image.bind('<Double-1>', self.view_original_image)

        select_image_btn = tk.Button(self.inner_frame, text="Select Image", command=self.select_image)
        select_image_btn.pack(pady=5)

        tag_label = tk.Label(self.inner_frame, text='Tags')
        tag_label.pack(pady=5)

        if self.app_data.selected_entry_data:
            tags = backend_logic.get_all_tags(self.app_data.session, self.app_data.url)

            if self.app_data.selected_entry_data['name'] in tags:
                tags.remove(self.app_data.selected_entry_data['name'])
        
        else:
            tags = backend_logic.get_all_tags(self.app_data.session, self.app_data.url)

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
        self.app_data.selected_entry_data = None
        self.app_data.previous_entry_data = None
        self.controller.show_frame(WorldOverviewFrame)

    def save(self):
        data_to_write = {}

        data_to_write['name'] = self.name_text.get()

        for column_name in self.column_names[1:-1]:
            
            if column_name == 'tags':
                continue

            data_to_write[column_name] = self.text_widgets[column_name].get("1.0", tk.END).strip()

        # Get selected tags from the Listbox
        selected_tags = self.tag_listbox.get(0, tk.END)

        # Convert the list of tags to a comma-separated string
        data_to_write['tags'] = ', '.join(selected_tags)

        if self.image_data:
            # Include the image data in the data_to_write dictionary
            data_to_write['image_data'] = self.image_data

        backend_logic.add_data_to_table(self.app_data.session, self.app_data.selected_category, data_to_write, self.app_data.url)
        self.controller.show_frame(WorldOverviewFrame)

    def delete_entry(self):
        data_to_remove = self.name_text.get()

        backend_logic.remove_entry(self.app_data.session, self.app_data.selected_category, data_to_remove, self.app_data.url)

        self.controller.show_frame(WorldOverviewFrame)

    def insert_data_if_exists(self):
        if not self.app_data.selected_entry_data:
            return
        
        if not self.app_data.previous_entry_data:
            self.app_data.previous_entry_data = self.app_data.selected_entry_data

        for table, textbox in self.text_widgets.items():
            textbox.insert(tk.END, self.app_data.selected_entry_data[table])

        self.name_text.insert(tk.END, self.app_data.selected_entry_data['name'])

        if self.app_data.selected_entry_data['image_data'] != None:
            self.image_data = self.app_data.selected_entry_data['image_data']
            self.display_image(self.image_data)

        # Clear the Listbox
        self.tag_listbox.delete(0, tk.END)

        # Populate the Listbox with existing tags
        existing_tags = self.app_data.selected_entry_data['tags'].split(', ')
        for tag in existing_tags:
            if tag == self.app_data.selected_entry_data['name']:
                continue
            self.tag_listbox.insert(tk.END, tag)

    def add_tag(self, event):
        selected_tag = self.tag_combobox.get()
        if self.tag_listbox.size() == 1 and self.tag_listbox.get(0) == '':
            self.tag_listbox.delete(0)
            self.tag_listbox.insert(0, selected_tag)
        elif selected_tag and selected_tag not in self.tag_listbox.get(0, tk.END):
            self.tag_listbox.insert(tk.END, selected_tag)
            self.tag_combobox.set("")  # Clear the combobox after adding the tag

    def on_tag_double_click(self, event):
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
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.inner_frame_id, width=event.width)

    def on_mouse_wheel(self, event):
        # Adjust the view of the canvas when the mouse wheel is scrolled
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def select_image(self):
        # Open a file dialog to select an image file
        file_path = filedialog.askopenfilename()
        if file_path:
            # Read the image file and convert it to bytes
            with open(file_path, 'rb') as file:
               self.image_data = file.read()
            # Display the selected image
            self.display_image(self.image_data)

    def display_image(self, image_data):
        # Open the image using PIL
        image = Image.open(io.BytesIO(image_data))
        # Resize the image if necessary to fit in the GUI
        # Use Image.Resampling.LANCZOS for high-quality downsampling
        image = image.resize((200, 200), Image.Resampling.LANCZOS)
        # Convert the image to Tkinter PhotoImage format
        photo = ImageTk.PhotoImage(image)
        # Display the image in a label
        self.image.configure(image=photo)
        self.image.image = photo  # Keep a reference to avoid garbage collection

    def view_original_image(self, event):
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

        else:
            # If image data does not exist, show a message
            messagebox.showinfo("No Image", "No image data available.")

    def update_tag_listbox(self, event):
        selected_option = self.tag_filter_combobox.get().replace(' ', '_').lower()

        tag_list = self.app_data.selected_entry_data['tags'].split(',')
        tag_list = [x.strip() for x in tag_list]

        filtered_tags = backend_logic.filter_tag_list_by_table(self.app_data.session, self.app_data.url, tag_list, selected_option)
        
        self.tag_listbox.delete(0, tk.END)
        
        for tag in filtered_tags:
            self.tag_listbox.insert(tk.END, tag)

    def on_window_close(self, window):
        self.canvas.unbind_all("<MouseWheel>")
        # Destroy the window
        window.destroy()

        self.app_data.selected_entry_data = self.app_data.previous_entry_data
        self.app_data.previous_entry_data = None
        self.app_data.selected_category = backend_logic.get_tag_location(self.app_data.session, self.app_data.selected_entry_data['name'], self.app_data.url)

        new_frame = EditEntryFrame(self.parent, self.controller, self.app_data)

        self.controller.show_frame(new_frame)    


class WorldBuilderApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("World Builder App")

        self.app_data = AppData()

        # Create the menu bar
        self.create_menu_bar()

        frame_classes = [WorldSelectionFrame, WorldOverviewFrame, NewEntrySelectCategoryFrame, ViewEntryFrame, EditEntryFrame]

        self.frames = {frame_class: None for frame_class in frame_classes}
        self.current_frame = None  # Track the current frame

        self.show_frame(WorldSelectionFrame)

        # Bind the closing event to the on_closing method
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_menu_bar(self):
        # Create a menu bar
        menubar = tk.Menu(self)

        # Create a file menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.on_closing)
        menubar.add_cascade(label="File", menu=file_menu)

        # Add the menu bar to the application window
        self.config(menu=menubar)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            if self.app_data.session:
                self.app_data.session.close()
            self.destroy()

    def show_frame(self, cont):
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

        if hasattr(frame, "update_label_text"):
            frame.update_label_text()

        # Resize the window to match the frame size with padding
        self.update_idletasks()
        width = frame.winfo_reqwidth() + 40  # Add padding on both sides
        height = frame.winfo_reqheight() + 40  # Add padding on both sides
        x = (self.winfo_screenwidth() - frame.winfo_reqwidth()) // 2
        y = (self.winfo_screenheight() - frame.winfo_reqheight()) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        # If the frame is an instance of EditEntryFrame, set the main window to specific value
        if isinstance(frame, EditEntryFrame) or isinstance(frame, ViewEntryFrame):
            self.geometry("700x600")


if __name__ == "__main__":
    backend_logic.find_database()
    app = WorldBuilderApp()
    app.mainloop()
