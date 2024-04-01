"""
This class defines the EditEntryFrame frame.
"""

import io
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from .. import backend_logic
from .view_entry_frame import ViewEntryFrame


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

        filter_options = [x.replace('_', ' ').title() for x in self.app_data.table_names if x != 'tags']
        filter_options = ['All Categories'] + filter_options

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
        self.controller.choose_next_frame("WorldOverviewFrame")

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
        backend_logic.add_data_to_table(self.app_data.session,
            self.app_data.selected_category, data_to_write, self.app_data.url)

        # Show WorldOverviewFrame
        self.controller.choose_next_frame("WorldOverviewFrame")

    def delete_entry(self):
        """
        Deletes the selected entry.

        This method removes the selected entry using backend logic and navigates back to the WorldOverviewFrame.
        """

        # Get name of entry to remove
        data_to_remove = self.name_text.get()

        # Remove entry using backend logic
        backend_logic.remove_entry(self.app_data.session,
            self.app_data.selected_category, data_to_remove, self.app_data.url)

        # Show WorldOverviewFrame
        self.controller.choose_next_frame("WorldOverviewFrame")

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
        self.app_data.selected_entry_data = backend_logic.get_data_for_entry(self.app_data.session,
            selected_tag, self.app_data.url)
        self.app_data.selected_category = backend_logic.get_tag_location(self.app_data.session,
            selected_tag, self.app_data.url)

        # Create a new Toplevel window
        new_window = tk.Toplevel(self.parent)
        new_window.geometry("700x600")
        new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_window_close(new_window))

        # Create a new instance of ViewEntryFrame with the info from the selected tag
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
        filtered_tags = backend_logic.filter_tag_list_by_table(self.app_data.session,
            self.app_data.url, tag_list, selected_option)

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
        self.app_data.selected_category = backend_logic.get_tag_location(self.app_data.session,
            self.app_data.selected_entry_data['name'], self.app_data.url)

        # Instantiate new EditEntryFrame
        new_frame = EditEntryFrame(self.parent, self.controller, self.app_data)

        # Show new frame
        self.controller.choose_next_frame("EditEntryFrame")
