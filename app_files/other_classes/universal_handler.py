"""
This utility class to handle all events that need platform
specfic code.
"""

import sys
import os

class UniversalHandler:
    """
        Handle events in a way that works cross-platform
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
            if 'listbox' in str(widget).rsplit('!', maxsplit=1):

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
