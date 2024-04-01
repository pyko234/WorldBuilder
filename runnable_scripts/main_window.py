"""
This class defines the mainwindow for the app.
"""

import tkinter as tk
from tkinter import messagebox

from .data_class import AppData
from .universal_handler import UniversalHandler
from .world_selection_frame import WorldSelectionFrame
from .world_overview_frame import WorldOverviewFrame
from .new_entry_select_category_frame import NewEntrySelectCategoryFrame
from .view_entry_frame import ViewEntryFrame
from .edit_entry_frame import EditEntryFrame


class MainWindow(tk.Tk):
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
        frame_classes = [WorldSelectionFrame,WorldOverviewFrame,
            NewEntrySelectCategoryFrame, ViewEntryFrame, EditEntryFrame]

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

if __name__ == '__main__':
    app = MainWindow()
    app.mainloop()
