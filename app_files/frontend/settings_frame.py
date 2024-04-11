"""
This class defines the SettingsFrame frame.
"""

from tkinter import ttk, colorchooser

class SettingsFrame(ttk.Frame):
    """
    A Tkinter Frame subclass for adjusting any settings within the main_window.

    This frame display various settings for adjusting the look and feel of the
    mainwindow. 
    """

    def __init__(self, parent, controller, app_data):
        """
        Initializes the SettingsFrame with a parent widget, a controller widget,
        and a data class.

        Args:
            parent (tk.Widget): The parent widget.
            controller (misc): The application's main controller that manages frame transitions and data sharing.
            app_data (object): An object containing application-wide data, such as available categories.
        """

        # Create frame and store the controller and AppData
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.app_data = app_data

        # Get a stlye class
        self.style = ttk.Style()

        # Get theme names
        themes = self.style.theme_names()

        # Theme frame
        theme_frame = ttk.Frame(self)
        theme_frame.pack()

        # Theme label
        theme_label = ttk.Label(self, text='Please choose a theme:')
        theme_label.pack(pady=5, padx=5)
        
        # Create list to save radio buttons in
        radio_buttons = []

        # Iterate through themes
        for theme in themes:

            # Theme radio button
            radio = ttk.Radiobutton(self, text=theme, value=theme)
            radio.pack(pady=5, padx=5)

            # Store radio button
            radio_buttons.append(radio)
       
        # Save Theme button
        theme_button = ttk.Button(self, text='Save Theme', command=lambda:self.save_theme(radio_buttons))
        theme_button.pack(pady=5, padx=5)

        # Choose Color Button
        background_color_button = ttk.Button(self, text='Select Background Color', command=self.choose_color)
        background_color_button.pack(pady=5, padx=5)

        # Back button
        back_button = ttk.Button(self, text='Back', command=self.back_one_frame)
        back_button.pack(side='bottom')

    def choose_color(self):
        """
        This method allows the user to choose the background color for the app itself.
        """

        # Ask user for color chose
        color_code = colorchooser.askcolor(title="Choose background color")

        # If the user choose a coloe
        if color_code[1]:

            # Configure the current style background color
            self.style.configure('.', background=color_code[1])

            # Configure the controllers background color
            self.controller.configure(background=color_code[1])

            # Unpack the color code of the tuple
            r, g, b = color_code[0]

            # Get reverse of color
            opposite_r = 255 - r
            opposite_g = 255 - g
            opposite_b = 255 - b

            # Adjust the opposite color if it's too close to the background color
            threshold = 50
            if abs(r - opposite_r) < threshold:
                opposite_r = 255 if r < 128 else 0
            if abs(g - opposite_g) < threshold:
                opposite_g = 255 if g < 128 else 0
            if abs(b - opposite_b) < threshold:
                opposite_b = 255 if b < 128 else 0

            # Format the opposite color to a hexadecimal
            opposite_color = '#{:02x}{:02x}{:02x}'.format(opposite_r, opposite_g, opposite_b)

            # Change the font color
            self.style.configure('.', foreground=opposite_color)

    def save_theme(self, radio_buttons):
        """
        This method saves the new theme for the main_app

        Args:
            radio_buttons: a list containing the radio buttons
        
        This function has no returns instead saves the theme
        """

        for radio in radio_buttons:
            if radio.state():
                self.style.theme_use(radio.cget("value"))

    def back_one_frame(self):
        """
        This method returns the Main App Window to the previous frame is was on.
        """

        if self.app_data.selected_world:
            self.controller.choose_next_frame("WorldOverviewFrame")
        else:
            self.controller.choose_next_frame("WorldSelectionFrame")
