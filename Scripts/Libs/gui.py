import os
import io
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from Scripts.Libs.database_schema import WorldBuilder
from PIL import Image, ImageTk

import Scripts.Libs.backend_logic as backend_logic


class AppData:
    def __init__(self):
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
        
        if edit_mode == "Edit":
            self.app_data.edit = True
        
        else:
            self.app_data.edit = False

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
        database_url = backend_logic.create_database()
        
        if database_url:
            self.app_data.session = backend_logic.create_session_by_url(database_url)
            self.controller.show_frame(WorldOverviewFrame)
        

class WorldOverviewFrame(tk.Frame):
    def __init__(self, parent, controller, app_data):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.controller = controller
        self.app_data = app_data

        self.label_text_var = tk.StringVar()

        self.label_text_var.set(self.app_data.selected_world)
        label = tk.Label(self, text=self.label_text_var.get())
        label.pack(pady=10)

        if self.app_data.edit:
            select_map_button = tk.Button(self, text='Select Map', command=self.select_map)
            select_map_button.pack(pady=10)

        view_map_button = tk.Button(self, text='View World Map', command=self.view_map)
        view_map_button.pack(pady=10)

        selection_label = tk.Label(self, text="Entries:")
        selection_label.pack(pady=10)

        self.create_dynamic_category_widgets()
        self.update_label_text()

        button_frame = tk.Frame(self)

        back_button = ttk.Button(button_frame, text="Back", command=lambda: self.controller.show_frame(WorldSelectionFrame))
        back_button.pack(side=tk.LEFT, padx=20)
 
        if self.app_data.edit:
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

                label = tk.Label(individual_frame, text=table_names[x].replace('_', ' ').title())
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

        if self.app_data.edit:
            self.controller.show_frame(EditEntryFrame)
        
        else:
            self.controller.show_frame(ViewEntryFrame)

    def select_map(self):
        # Open a file dialog to select an image file
        file_path = filedialog.askopenfilename()
        if file_path:
            # Read the image file and convert it to bytes
            with open(file_path, 'rb') as file:
               image_data = file.read()
            # Display the selected image
            self.save_image(image_data)
    
    def save_image(self, image_data):
        backend_logic.add_world_map(self.app_data.session, image_data, self.app_data.url)

    def view_map(self):
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

        self.app_data.selected_entry_data = None

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
        selected_option = self.tag_filter_combobox.get()

        tag_list = self.app_data.selected_entry_data['tags'].split(',')

        backend_logic.filter_tag_list_by_table(self.app_data.session, self.app_data.url, tag_list, selected_option)
        
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

        # Listbox to display existing tags
        self.tag_listbox = tk.Listbox(self.inner_frame, selectmode=tk.MULTIPLE)
        self.tag_listbox.pack(pady=5)

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
