"""
This class defines the frame for the World Selection.
"""

import tkinter as tk
from tkinter import ttk

from . import backend_logic



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
        self.worlds = backend_logic.get_database_names()

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
        world_dropdown = ttk.Combobox(self, values=world_names,
            textvariable=self.world_var, state="readonly")
        world_dropdown.pack(padx=10, pady=10)

        # Radio buttons for selecting edit or view mode
        edit_view_frame = ttk.Frame(self)
        edit_view_frame.pack(padx=10, pady=10)
        view_radio = ttk.Radiobutton(edit_view_frame, text="Edit",
            variable=self.edit_var, value="Edit")
        view_radio.pack(padx=10, pady=10)
        edit_radio = ttk.Radiobutton(edit_view_frame, text="View",
            variable=self.edit_var, value="View")
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
        from .world_overview_frame import WorldOverviewFrame

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

        from .world_overview_frame import WorldOverviewFrame

        # Generate a new database URL by creating a new database file
        database_url = backend_logic.create_database()

        # If the database URL is successfully created
        if database_url:

            # Establish a session with the new database URL
            self.app_data.session = backend_logic.create_session_by_url(database_url)

            # Navigate to the WorldOverviewFrame to display the newly created world
            self.controller.show_frame(WorldOverviewFrame)
     