"""
This class defines the frame for the World Overview Frame.
"""

import io
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk

from .. import backend_logic
#from .world_selection_frame import WorldSelectionFrame
#from .new_entry_select_category_frame import NewEntrySelectCategoryFrame
#from .edit_entry_frame import EditEntryFrame
#from .view_entry_frame import ViewEntryFrame

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
            create_dynamic_category_widgets(): Creates dynamic category widgets based on available tables in the 
                database.
            update_label_text(): Updates the label text to display the selected world name.
            update_listboxes(): Updates the listboxes with entry names for each category.
            on_double_click(event, table_name): Handles double-click events on listbox items to view or edit 
                entry details.
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

        from .world_selection_frame import WorldSelectionFrame
        from .new_entry_select_category_frame import NewEntrySelectCategoryFrame

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
        back_button = ttk.Button(button_frame, text="Back",
            command=lambda: self.controller.show_frame(WorldSelectionFrame))
        back_button.pack(side=tk.LEFT, padx=20)

        # Create Entry button, if mode is edit
        if self.app_data.edit:
            create_button = ttk.Button(button_frame, text="Create New Entry",
                command=lambda: self.controller.show_frame(NewEntrySelectCategoryFrame))
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

                listbox.bind('<Double-1>', lambda event,
                    table_name=table_names[x]: self.on_double_click(event, table_name))

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

        from .edit_entry_frame import EditEntryFrame
        from .view_entry_frame import ViewEntryFrame

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
        """
        Adjust the width of the canvas when resized.
        """
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def on_frame_configure(self, event):
        """
        Configure the scroll region on the canvas to the entire size of the canvas
        once the frame is created.
        """
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
