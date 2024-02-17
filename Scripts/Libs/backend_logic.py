from sqlalchemy import create_engine, inspect, text, event
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import os
from Scripts.Libs.database_schema import WorldBuilder
from tkinter import messagebox
import traceback


def get_database_url(database_identifier):
    if "://" in database_identifier:
        return database_identifier
    else:
        return f"sqlite:///{database_identifier.lower().replace(' ', '_')}_database.db"

def create_session_by_url(database_url):
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()

def create_session_by_name(database_name):
    database_url = get_database_url(database_name)
    return create_session_by_url(database_url)

def get_table_names(session):
    try:        
        inspector = inspect(session.bind)
        
        names = inspector.get_table_names()

        excluded_tables = ['world', 'tags']

        table_names = [name for name in names if name not in excluded_tables]
        
        return table_names
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_column_names(session, table_name):
    if not table_name:
        return []

    engine = session.get_bind()

    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)

    column_names = [column['name'] for column in columns]

    excluded_names = ['id']

    names = [name for name in column_names if name not in excluded_names]

    return names

def add_data_to_table(session, table_name, data_dict, database_url):
    try:
        world_builder = WorldBuilder(database_url)
        tag_table = world_builder.get_table_class('tags')

        # Get the table class
        main_table_class = world_builder.get_table_class(table_name)

        # Check if the entry already exists in the main table
        existing_entry = session.query(main_table_class).filter_by(name=data_dict['name']).first()

        if existing_entry:
            # Ask the user if they want to update the data
            update_data = messagebox.askyesno("Update Entry", "Entry already exists. Do you want to update the data?")
            
            if update_data:
                print("Updating data...")
                # Update the existing entry if the user chooses to do so
                for key, value in data_dict.items():
                    setattr(existing_entry, key, value)
                
                session.commit()

                print("Data updated successfully!")
            else:
                print("Data not updated.")

        else:
            # Create a new entry if it doesn't exist
            new_entry = main_table_class(**data_dict)
            session.add(new_entry)
            print("Data added successfully!")

            # Commit the transaction to ensure the new entry gets an ID
            session.commit()

            # Get the last inserted ID
            last_id = session.query(main_table_class.id).order_by(main_table_class.id.desc()).first()

            if last_id:
                last_id = last_id[0]

                # Add entry to tags table with the last inserted ID
                tags = data_dict['tags'].split(",")  # Assuming tags are stored as comma-separated values
                for tag in tags:
                    tag_entry = tag_table(entry_name=data_dict['name'], entry_location=f'{table_name}/{last_id}')
                    session.add(tag_entry)
                    print(f"Tag '{tag}' added to tags table with location: {last_id}")

                # Commit the transaction
                session.commit()

            else:
                print("Error retrieving last inserted ID.")

    except Exception as e:
        # Print the traceback and error message
        traceback.print_exc()
        print(f"Error adding/updating data to {table_name}: {e}")
        print(f"Data dictionary: {data_dict}")
        # Rollback the transaction in case of an error
        session.rollback()

def remove_entry(session, table_name, entry_name, database_url):
    try:
        world_builder = WorldBuilder(database_url)
        main_table_class = world_builder.get_table_class(table_name)

        # Query the entry to be deleted
        entry_to_delete = session.query(main_table_class).filter_by(name=entry_name).first()

        if entry_to_delete:
            # Delete the entry
            session.delete(entry_to_delete)
            session.commit()
            print(f"Entry '{entry_name}' removed successfully!")
        else:
            print(f"Entry '{entry_name}' not found.")
    except Exception as e:
        # Print the traceback and error message
        traceback.print_exc()
        print(f"Error removing entry '{entry_name}' from {table_name}: {e}")
        # Rollback the transaction in case of an error
        session.rollback()

def get_entry_names(session, table_name, database_url):
    try:
        # Get the table class dynamically using the session
        world_builder = WorldBuilder(database_url)
        table_class = world_builder.get_table_class(table_name)
        
        # If the table class is found
        if table_class:
            result = session.query(table_class.name).all()

            # Extract the names from the result
            names = [row[0] for row in result]
            return names

        else:
            print(f"Error: Table class not found for {table_name}")
            return []

    except Exception as e:
        print(f"Error retrieving names from {table_name}: {e}")
        return []

def get_data_for_entry(session, entry_name, database_url):
    try:
        world_builder = WorldBuilder(database_url)
        tag_table = world_builder.get_table_class('tags')

        # Search for entry in tag table first and return location
        tag_entry = session.query(tag_table).filter_by(entry_name=entry_name).first()

        if not tag_entry:
            print("Entry Data not found.")
            return
        
        entry_location, entry_id = tag_entry.entry_location.split('/')

        table_class = world_builder.get_table_class(entry_location)


        # Query the database to get all columns for the specified entry_name
        result = session.query(table_class).filter_by(id=entry_id).first()

        if result:
            # Convert the result to a dictionary for easy access
            data_dict = result.__dict__
            # Remove unnecessary attributes
            data_dict.pop("_sa_instance_state", None)
            return data_dict
        else:
            return None

    except Exception as e:
        print(f"Error retrieving data from {entry_name}: {e}")
        traceback.print_exc()
        return None

def get_all_tags(session, database_url):
    try:
        world_builder = WorldBuilder(database_url)
        tag_table = world_builder.get_table_class('tags')
        
        # Query to retrieve all tags
        result = session.query(tag_table.entry_name).all()

        # Extract the tags from the result
        tags = [row[0] for row in result]

        return tags
    
    except Exception as e:
        print(f"Error retrieving tags: {e}")
        return []
    
def get_tag_location(session, entry_name, database_url):
    try:
        world_builder = WorldBuilder(database_url)
        tag_table = world_builder.get_table_class('tags')
        
        # Query to retrieve all tags
        tag_entry = session.query(tag_table).filter_by(entry_name=entry_name).first()

        tag_column = tag_entry.entry_location.split('/')[0]

        return tag_column
    
    except Exception as e:
        print(f"Error retrieving tags: {e}")
        return []

def add_world_map(session, image_data, database_url):
    try:
        #create instance of WorldBuilder
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
    try:
        # Create instance of world
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



if __name__ == '__main__':
    pass