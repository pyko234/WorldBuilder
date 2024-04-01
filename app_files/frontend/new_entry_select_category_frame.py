"""
This class defines the NewEntrySelectCategoryFrame frame.
"""

import tkinter as tk

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
        back_button = tk.Button(self, text="Back",
            command=lambda: self.controller.choose_next_frame("WorldOverviewFrame"))
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
            self.controller.choose_next_frame("EditEntryFrame")
