"""
This class defines the ViewEntryFrame frame.
"""

import io
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from .. import backend_logic

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
            filter_options = [x.replace('_', ' ').title() for x in self.app_data.table_names if x != 'tags']
            filter_options = ['All Categories'] + filter_options

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
        self.controller.choose_next_frame("WorldOverviewFrame")

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
        filtered_tags = backend_logic.filter_tag_list_by_table(self.app_data.session,
            self.app_data.url, tag_list, selected_option)

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
        self.app_data.selected_entry_data = backend_logic.get_data_for_entry(self.app_data.session,
            selected_tag, self.app_data.url)
        self.app_data.selected_category = backend_logic.get_tag_location(self.app_data.session,
            selected_tag, self.app_data.url)

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
        self.app_data.selected_category = backend_logic.get_tag_location(self.app_data.session,
            self.app_data.selected_entry_data['name'], self.app_data.url)

        # Instantiate new ViewEntryFrame with the selected entry data
        new_frame = ViewEntryFrame(self.parent, self.controller, self.app_data)

        # Show new instance of ViewEntryFrame
        self.controller.show_frame(new_frame)
