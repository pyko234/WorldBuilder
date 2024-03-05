from sqlalchemy import create_engine, inspect, text, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path
from database_schema import WorldBuilder
from tkinter import messagebox, simpledialog
from sys import exit
import traceback
import json
import os

# Get script path
script_directory = Path(os.path.dirname(os.path.abspath(__file__)))

# Set path to the databases folder
path = script_directory / "db"

# If the folder does not exist
if not os.path.exists(path):

    # Create the folder
    os.makedirs(path)


def find_database():
    """
    Checks if a database exists in the specified path.

    If no database is found, prompts the user to create one. If the user agrees, calls the create_database function.

    Returns:
        None
    """

    # Get list of database files in the path
    found = any(file.endswith("_database.db") for file in os.listdir(path))
    
    # If no database files found
    if not found:

        # Ask user to create a database
        reponse = messagebox.askokcancel(message="No database found. Select OK to create one")

        # If user selects "ok"
        if reponse:

            # Create database
            create_database()
        
        # Else exit
        else:
            exit()

def create_database():
    """
    Creates a new SQLite database.

    Prompts the user to enter a world name and creates a new SQLite database with the specified name.

    Returns:
        str or None: The database URL if creation is successful, None otherwise.
    """

    # Ask for world name
    name = simpledialog.askstring("World Name", "Please Enter a world name:")

    # Quick if for verification of name
    if name is None:
        print("Invalid world name. Aborting.")
        
        # Return None if the name is invalid
        return None

    # Set database folder to path
    database_folder = path

    # Get database_url
    DATABASE_URL = rf'sqlite:///{database_folder}/{name.lower().replace(" ", "_")}_database.db'
    print(f"Database URL: {DATABASE_URL}")

    # Instaniate world_builder using the database url
    world_builder = WorldBuilder(database_url=DATABASE_URL)

    # With state to work with session and close when down
    with world_builder.get_session() as session:

        # Try statement to catch errors
        try:

            # Instaniate the world table and set the name column to name
            world = WorldBuilder.World(name=name)

            # Insert the world object into the database
            session.add(world)

            # Commit changes
            session.commit()
            
            # Return just the created database url
            return DATABASE_URL
        
        # Catch any errors thrown
        except SQLAlchemyError as e:
            print(f"Error: {e}")

            # Remove the created database
            os.remove(DATABASE_URL)

            # Return None
            return None

def get_database_url(database_identifier):
    """
    Constructs the database URL based on the provided database identifier.

    Args:
        database_identifier (str): The database name or URL.

    Returns:
        str: The constructed database URL.
    """

    # Check for string in database_identifier
    if "://" in database_identifier:

        # Return as database identifier is already a url
        return database_identifier
    
    else:

        # Return sqlite url
        return f"sqlite:///{database_identifier.lower().replace(' ', '_')}_database.db"

def create_session_by_url(database_url):
    """
    Creates a session object using the provided database URL.

    Args:
        database_url (str): The URL of the database.

    Returns:
        Session: The session object.
    """

    # Create engine
    engine = create_engine(database_url)
    
    # Create session using engine
    Session = sessionmaker(bind=engine)
    
    # Return session
    return Session()

def create_session_by_name(database_name):
    """
    Creates a session object using the provided database name.

    Args:
        database_name (str): The name of the database.

    Returns:
        Session: The session object.
    """

    # Get database url
    database_url = get_database_url(database_name)
    
    # Return session using create_session_by_url
    return create_session_by_url(database_url)

def get_table_names(session):
    """
    Retrieves the names of all tables in the database.

    Args:
        session: The session object.

    Returns:
        list: A list of table names.
    """

    # Try block for error handling
    try:

        # Creater inspector
        inspector = inspect(session.bind)
        
        # Get names of all the tables
        names = inspector.get_table_names()

        # List to exclude tables
        excluded_tables = ['world', 'tags']

        # Remove the excluded tables
        table_names = [name for name in names if name not in excluded_tables]
        
        # Return table names
        return table_names
    
    # Handle Errors
    except Exception as e:
        print(f"An error occurred: {e}")

        return None

def get_column_names(session, table_name):
    """
    Retrieves the column names of a specified table.

    Args:
        session: The session object.
        table_name (str): The name of the table.

    Returns:
        list: A list of column names.
    """

    # If no table names return an empty list
    if not table_name:
        return []

    # Get engine
    engine = session.get_bind()

    # Get inspector
    inspector = inspect(engine)
    
    # Get columns
    columns = inspector.get_columns(table_name)

    # Get column names
    column_names = [column['name'] for column in columns]

    # List of names to exclude
    excluded_names = ['id']

    # Remove excluded names from column names
    names = [name for name in column_names if name not in excluded_names]

    # Return list of names
    return names

def add_data_to_table(session, table_name, data_dict, database_url):
    """
    Adds or updates data in the specified table.

    Args:
        session: The session object.
        table_name (str): The name of the table.
        data_dict (dict): A dictionary containing the data to be added or updated.
        database_url (str): The URL of the database.

    Returns:
        None
    """

    # Try block to catch errors
    try:

        # Create instance of WorldBuilder
        world_builder = WorldBuilder(database_url)
        
        # Get tag table
        tag_table = world_builder.get_table_class('tags')

        # Get the table class
        main_table_class = world_builder.get_table_class(table_name)

        # Query the table for existing data of dictionary
        existing_entry = session.query(main_table_class).filter_by(name=data_dict['name']).first()

        # Check for exsisting entry
        if existing_entry:

            # Ask the user if they want to update the data
            update_data = messagebox.askyesno("Update Entry", "Entry already exists. Do you want to update the data?")
            
            # If the user selects "ok"
            if update_data:
                print("Updating data...")

                # Update the existing entry if the user chooses to do so
                for key, value in data_dict.items():
                    setattr(existing_entry, key, value)
                
                # Commit changes
                session.commit()

                print("Data updated successfully!")
            
            else:
                print("Data not updated.")

        # If no data in the database
        else:

            # Create a new entry if it doesn't exist
            new_entry = main_table_class(**data_dict)
            
            # Add new data to database
            session.add(new_entry)
            print("Data added successfully!")

            # Commit the transaction to ensure the new entry gets an ID
            session.commit()

            # Get the last inserted ID
            last_id = session.query(main_table_class.id).order_by(main_table_class.id.desc()).first()[0]

            # If there is a last_id (there definitly should be)
            if last_id:

                # Add entry to tags table with the last inserted ID
                # Get tags from entry data
                tags = data_dict['tags'].split(",")
                
                # Iterate through tags
                for tag in tags:
                    
                    # Insert tag entry into tag table
                    tag_entry = tag_table(entry_name=data_dict['name'], entry_location=f'{table_name}/{last_id}')
                    
                    # Add tag entry to database
                    session.add(tag_entry)
                    
                    print(f"Tag '{tag}' added to tags table with location: {last_id}")

                # Commit the transaction
                session.commit()

            else:
                print("Error retrieving last inserted ID.")

    # Catch any errors
    except Exception as e:
        
        # Print the traceback and error message
        traceback.print_exc()
        print(f"Error adding/updating data to {table_name}: {e}")
        print(f"Data dictionary: {data_dict}")
        
        # Rollback the transaction in case of an error
        session.rollback()

def remove_entry(session, table_name, entry_name, database_url):
    """
    Removes an entry from the specified table.

    Args:
        session: The session object.
        table_name (str): The name of the table.
        entry_name (str): The name of the entry to be removed.
        database_url (str): The URL of the database.

    Returns:
        None
    """

    # Try block to catch errors
    try:

        # Create instance of WorldBuilder
        world_builder = WorldBuilder(database_url)
        
        # Get table class
        main_table_class = world_builder.get_table_class(table_name)

        # Query the entry to be deleted
        entry_to_delete = session.query(main_table_class).filter_by(name=entry_name).first()

        # Check for entry data
        if entry_to_delete:

            # Delete the entry
            session.delete(entry_to_delete)
            
            # Commit changes
            session.commit()
            print(f"Entry '{entry_name}' removed successfully!")
        
        else:
            print(f"Entry '{entry_name}' not found.")
    
    # Catch errors
    except Exception as e:
        
        # Print the traceback and error message
        traceback.print_exc()
        print(f"Error removing entry '{entry_name}' from {table_name}: {e}")
        
        # Rollback the transaction in case of an error
        session.rollback()

def get_entry_names(session, table_name, database_url):
    """
    Retrieves the names of entries in the specified table.

    Args:
        session: The session object.
        table_name (str): The name of the table.
        database_url (str): The URL of the database.

    Returns:
        list: A list of entry names.
    """

    # Try block to catch errors
    try:
        
        # Get the table class dynamically using the session
        world_builder = WorldBuilder(database_url)
        
        # Get main table class
        table_class = world_builder.get_table_class(table_name)
        
        # If the table class is found
        if table_class:
            
            # Query the table fo all entry names
            result = session.query(table_class.name).all()

            # Extract the names from the result
            names = [row[0] for row in result]
            
            # Return list of names
            return names

        else:
            print(f"Error: Table class not found for {table_name}")
            return []

    # Catch errors
    except Exception as e:
        
        print(f"Error retrieving names from {table_name}: {e}")
        return []

def get_data_for_entry(session, entry_name, database_url):
    """
    Retrieves data for a specific entry from the database.

    Args:
        session: The session object.
        entry_name (str): The name of the entry.
        database_url (str): The URL of the database.

    Returns:
        dict or None: A dictionary containing the data for the entry, or None if no data is found.
    """

    # Try block to catch errors
    try:
        
        # Create instance of WorldBuilder
        world_builder = WorldBuilder(database_url)
        
        # Get tag table
        tag_table = world_builder.get_table_class('tags')

        # Search for entry in tag table first and return location
        tag_entry = session.query(tag_table).filter_by(entry_name=entry_name).first()

        # Check for tag entry
        if not tag_entry:
            print("Entry Data not found.")
            return
        
        # Unpack entry location and id from entry_location column
        entry_location, entry_id = tag_entry.entry_location.split('/')

        # Get the entry table
        table_class = world_builder.get_table_class(entry_location)

        # Query the database to get all columns for the specified entry_name
        result = session.query(table_class).filter_by(id=entry_id).first()

        # Check for result
        if result:

            # Convert the result to a dictionary for easy access
            data_dict = result.__dict__
            
            # Remove unnecessary attributes
            data_dict.pop("_sa_instance_state", None)
            
            return data_dict
        
        else:
            return None

    # Catch Errors
    except Exception as e:
        
        # Print traceback
        traceback.print_exc()
        print(f"Error retrieving data from {entry_name}: {e}")
        
        return None

def get_all_tags(session, database_url):
    """
    Retrieves all tags from the database.

    Args:
        session: The session object.
        database_url (str): The URL of the database.

    Returns:
        list: A list of tags.
    """

    # Try block to catch errors
    try:

        # Create instance of WorldBuilder
        world_builder = WorldBuilder(database_url)
        
        # Get tag table
        tag_table = world_builder.get_table_class('tags')
        
        # Query to retrieve all tags
        result = session.query(tag_table.entry_name).all()

        # Extract the tags from the result
        tags = [row[0] for row in result]

        return tags
    
    # Catch errors
    except Exception as e:
        print(f"Error retrieving tags: {e}")
        return []
    
def get_tag_location(session, entry_name, database_url):
    """
    Retrieves the location of a tag in the database.

    Args:
        session: The session object.
        entry_name (str): The name of the tag.
        database_url (str): The URL of the database.

    Returns:
        str: The location of the tag.
    """

    # Try block to catch errors
    try:

        # Create instance of WorldBuilder
        world_builder = WorldBuilder(database_url)
        
        # Get tag table
        tag_table = world_builder.get_table_class('tags')
        
        # Query to retrieve all tags for entry
        tag_entry = session.query(tag_table).filter_by(entry_name=entry_name).first()

        # Split tag entry and return first index
        tag_column = tag_entry.entry_location.split('/')[0]

        # Return tag location
        return tag_column
    
    # Catch errors
    except Exception as e:
        print(f"Error retrieving tags: {e}")
        return []

def add_world_map(session, image_data, database_url):
    """
    Adds a world map image to the database.

    Args:
        session: The session object.
        image_data (bytes): The image data.
        database_url (str): The URL of the database.

    Returns:
        None
    """

    # Try block to catch errors
    try:

        # Create instance of WorldBuilder
        world = WorldBuilder(database_url)

        #Get column_class
        main_column_class = world.get_table_class('world')

        #Get Entry
        entry = session.query(main_column_class).first()

        #Update Entry
        entry.world_map = image_data

        #Commit changes
        session.commit()

    except Exception as e:
        # Print the traceback and error message
        traceback.print_exc()

        print(f"Erorr adding world map: {e}")

        # Rollback the transaction in case of error
        session.rollback()

def veiw_world_map(session, database_url):
    """
    Retrieves the world map image from the database.

    Args:
        session: The session object.
        database_url (str): The URL of the database.

    Returns:
        bytes: The image data.
    """

    # Try block to catch errors
    try:
        # Create instance of WorldBuilder
        world = WorldBuilder(database_url)

        # Get column class
        main_table_class = world.get_table_class('world')

        # Get Entry
        entry = session.query(main_table_class).first()

        # Get Data
        data = entry.world_map

        return data
    
    except Exception as e:
        # Print traceback and error message
        traceback.print_exc()

        print(f"Error viewing world map: {e}")

def filter_tag_list_by_table(session, database_url, tag_list, table_name):
    """
    Filters a list of tags based on the specified table.

    Args:
        session: The session object.
        database_url (str): The URL of the database.
        tag_list (list): A list of tags.
        table_name (str): The name of the table.

    Returns:
        list: A filtered list of tags.
    """

    # Create world builder 
    world_builder = WorldBuilder(database_url)
    
    # Create tag table
    tag_table = world_builder.get_table_class('tags')

    # Query tag table to return tags from entry
    all_tags = session.query(tag_table).filter(tag_table.entry_name.in_(tag_list)).all()

    # Check to return all tags
    if table_name == 'all_categories':
        return [x.entry_name for x in all_tags]

    # Filter tags
    filtered_tags = [x.entry_name for x in all_tags if x.entry_location.split('/')[0] == table_name]

    # Return list of filtered tags
    return filtered_tags




if __name__ == '__main__':
    find_database()
    pass