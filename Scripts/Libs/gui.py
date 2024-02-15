import os
import io
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from sqlalchemy import create_engine, inspect, MetaData
from sqlalchemy.orm import sessionmaker
from Scripts.Libs.database_schema import WorldBuilder
from Scripts.Libs.create_database import create_database
from PIL import Image, ImageTk
import Scripts.Libs.backend_logic as backend_logic


class AppData:
    def __init__(self):
        self.selected_world = None
        self.table_names = []
        self.selected_category = None
        self.selected_entry_data = None
        self.previous_frame = None
        self.session = None
        self.url = None


class WorldSelectionFrame(tk.Frame):
    def __init__(self, parent, controller, app_data):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.app_data = app_data

        self.worlds = self.get_worlds()

        self.world_var = tk.StringVar()

        # Extract world names from the dictionary keys
        world_names = list(self.worlds.keys())
        self.world_var.set(world_names[0])

        self.edit_var = tk.StringVar()
        self.edit_var.set("View")

        # Create dropdown for world selection
        world_label = ttk.Label(self, text="Select World:")
        world_label.pack(padx=10, pady=10)

        world_dropdown = ttk.Combobox(self, values=world_names, textvariable=self.world_var, state="readonly")
        world_dropdown.pack(padx=10, pady=10)

        # Create radio buttons for edit/view
        edit_view_frame = ttk.Frame(self)
        edit_view_frame.pack(padx=10, pady=10)

        view_radio = ttk.Radiobutton(edit_view_frame, text="View", variable=self.edit_var, value="View")
        view_radio.pack(padx=10, pady=10)

        edit_radio = ttk.Radiobutton(edit_view_frame, text="Edit", variable=self.edit_var, value="Edit")
        edit_radio.pack(padx=10, pady=10)

        # Button to proceed
        proceed_button = ttk.Button(self, text="Proceed", command=self.proceed)
        proceed_button.pack(padx=10, pady=10)

        # Button to create a new world
        create_button = ttk.Button(self, text='Create New World', command=self.create_new)
        create_button.pack(padx=10, pady=10)

    def proceed(self):
        selected_world = self.world_var.get()
        edit_mode = self.edit_var.get()

        # Get the URL from the dictionary using the selected_world
        database_url = self.worlds[selected_world]
        self.app_data.url = database_url

        # Create a session with the URL
        self.app_data.session = backend_logic.create_session_by_url(database_url)
        self.app_data.selected_world = selected_world

        # Handle the selected world and edit mode
        self.controller.show_frame(WorldOverviewFrame)

    def get_worlds(self):
        script_directory = Path(os.path.dirname(os.path.abspath(__file__)))
        path = script_directory.parent.parent / "Lib" / "db"

        names = {}
        for file in os.listdir(path):
            if file.endswith("_database.db"):
                database_url = f"sqlite:///{path / file}"

                session = backend_logic.create_session_by_url(database_url)

                # Use the session passed as an argument
                
                world_entry = session.query(WorldBuilder.World).first()
                if world_entry:
                    names[world_entry.name] = database_url

        return names
    
    def create_new(self):
        database_url = create_database()
        
        if database_url:
            self.app_data.session = backend_logic.create_session_by_url(database_url)
            self.controller.show_frame(WorldOverviewFrame)
        

class WorldOverviewFrame(tk.Frame):
    def __init__(self, parent, controller, app_data):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.app_data = app_data

        self.label_text_var = tk.StringVar()

        self.label_text_var.set(self.app_data.selected_world)
        label = tk.Label(self, text=self.label_text_var.get())
        label.pack(pady=10)

        selection_label = tk.Label(self, text="Entries:")
        selection_label.pack(pady=10)

        self.create_dynamic_category_widgets()
        self.update_label_text()

        button_frame = tk.Frame(self)

        back_button = ttk.Button(button_frame, text="Back", command=lambda: self.controller.show_frame(WorldSelectionFrame))
        back_button.pack(side=tk.LEFT, padx=20)
 
        create_button = ttk.Button(button_frame, text="Create New Entry", command=lambda: self.controller.show_frame(NewEntrySelectCategoryFrame))
        create_button.pack(side=tk.RIGHT, padx=20)

        button_frame.pack(side="bottom", pady=20)

    def create_dynamic_category_widgets(self):
        if not self.app_data.session:
            return
        
        
        table_names = backend_logic.get_table_names(self.app_data.session)
        self.app_data.table_names = table_names
    
        # Define the number of columns in the layout
        num_columns = 3

        canvas_frame = tk.Frame(self)
        canvas_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(canvas_frame)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        category_frames = tk.Frame(canvas)
        canvas.create_window((0, 0), window=category_frames, anchor="nw")

        self.listbox_dict = {}

        for i in range(0, len(table_names), num_columns):
            category_frame = tk.Frame(category_frames)

            for x in range(i, min(i + num_columns, len(table_names))):
                individual_frame = tk.Frame(category_frame)
                individual_frame.pack(side=tk.LEFT)

                label = tk.Label(individual_frame, text=table_names[x])
                label.pack(side=tk.TOP)

                listbox = tk.Listbox(individual_frame, height=10)
                listbox.pack(side=tk.TOP, padx=10, fill='both', expand=True)

                listbox.bind('<Double-1>', lambda event, table_name=table_names[x]: self.on_double_click(event, table_name))

                self.listbox_dict[table_names[x]] = listbox

            category_frame.pack(fill='both', side=tk.TOP, pady=10)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))
        canvas.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        canvas.pack_configure(side="left", fill="both", expand=True, padx=(0, scrollbar.winfo_width()))

        self.update_listboxes()

    def update_combobox(self):
        # Clear and update Combobox with new values
        table_names = self.get_table_names()
        self.world_combobox['values'] = table_names
        self.world_combobox.set(table_names[0])

    def update_label_text(self):
        selected_world = self.app_data.selected_world
        self.label_text_var.set(selected_world)

    def update_listboxes(self):
        for table_name, listbox in self.listbox_dict.items():
            entries = backend_logic.get_entry_names(self.app_data.session, table_name, self.app_data.url)
            
            if entries:
                for entry in entries:
                    listbox.insert(tk.END, entry)

    def on_double_click(self, event, table_name):
        selected_item = event.widget.get(event.widget.curselection())

        data = backend_logic.get_data_for_entry(self.app_data.session, selected_item, self.app_data.url)

        self.app_data.selected_entry_data = data
        self.app_data.selected_category = table_name

        self.controller.show_frame(EditEntryFrame)


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
            self.listbox.insert(tk.END, item)

        select_button = tk.Button(self, text='Select', command=self.select_category)
        select_button.pack(side=tk.RIGHT, padx=20)

        back_button = tk.Button(self, text="Back", command=lambda: self.controller.show_frame(WorldOverviewFrame))
        back_button.pack(side=tk.LEFT, padx=20)

    def select_category(self):
         selected_indices = self.listbox.curselection()

         if selected_indices:
             selected_item = self.listbox.get(selected_indices[0])
             self.app_data.selected_category = selected_item
             self.controller.show_frame(EditEntryFrame)


class EditEntryFrame(tk.Frame):
    def __init__(self, parent, controller, app_data):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.controller = controller
        self.app_data = app_data
        self.text_widgets = {}

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

        # Combobox for tags
        self.tag_combobox = ttk.Combobox(self.inner_frame, values=backend_logic.get_all_tags(self.app_data.session, self.app_data.url), state='readonly')
        self.tag_combobox.pack(pady=5)

        # Listbox to display existing tags
        self.tag_listbox = tk.Listbox(self.inner_frame, selectmode=tk.MULTIPLE)
        self.tag_listbox.pack(pady=5)

        # Bind the on_tag_double_click command
        self.tag_listbox.bind('<Double-1>', self.on_tag_double_click)

        # Bind the <Return> key to the add_tag function
        self.tag_combobox.bind('<Return>', self.add_tag)

        button_frame = tk.Frame(self)
        button_frame.pack(side='bottom', pady=10)

        save_button = tk.Button(button_frame, text='Save', command=self.save)
        save_button.pack(side=tk.RIGHT, padx=10)

        back_button = tk.Button(button_frame, text='Back', command=lambda: self.controller.show_frame(self.app_data.previous_frame))
        back_button.pack(side=tk.LEFT, padx=10)

        self.insert_data_if_exists()

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

        # Include the image data in the data_to_write dictionary
        data_to_write['image_data'] = self.image_data

        backend_logic.add_data_to_table(self.app_data.session, self.app_data.selected_category, data_to_write, self.app_data.url)
        self.controller.show_frame(WorldOverviewFrame)

    def insert_data_if_exists(self):
        if not self.app_data.selected_entry_data:
            return

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
            self.tag_listbox.insert(tk.END, tag)

        self.app_data.selected_entry_data = None

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

        # Create a new instance of EditEntryFrame with the info from the selected tag
        new_frame = EditEntryFrame(new_window, self.controller, self.app_data)

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


class WorldBuilderApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("World Builder App")

        self.app_data = AppData()

        frame_classes = [WorldSelectionFrame, WorldOverviewFrame, NewEntrySelectCategoryFrame, EditEntryFrame]

        self.frames = {frame_class: None for frame_class in frame_classes}
        self.current_frame = None  # Track the current frame

        if not self.check_for_databases():
            messagebox.showinfo("OK Message", "No world found, please create one.")
            name, database_url = create_database()
            session = backend_logic.create_session_by_url(database_url)
            self.app_data.selected_world, self.app_data.url, self.app_data.session = [name, database_url, session]
            self.show_frame(WorldOverviewFrame)
            return

        self.show_frame(WorldSelectionFrame)

        # Bind the closing event to the on_closing method
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()

    def show_frame(self, cont):
        if isinstance(cont, tk.Frame):
            # If an instance of the frame is provided, use it directly
            frame = cont
        else:
            # If a frame class is provided, create a new instance
            frame = cont(self, self, self.app_data)
            self.frames[cont] = frame

        # Save the instance of the current frame
        self.app_data.previous_frame = self.current_frame

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
        if isinstance(frame, EditEntryFrame):
            self.geometry("900x800")

    def check_for_databases(self):
        script_directory = Path(os.path.dirname(os.path.abspath(__file__)))
        path = script_directory.parent.parent / "Lib" / "db" 

        for file in os.listdir(path):
            if file.endswith("_database.db"):
                return True
        
        return False


if __name__ == "__main__":
    app = WorldBuilderApp()
    app.mainloop()
