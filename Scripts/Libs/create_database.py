import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from tkinter import simpledialog
from Scripts.Libs.database_schema import WorldBuilder


Base = declarative_base()

script_directory = Path(os.path.dirname(os.path.abspath(__file__)))

path = script_directory.parent.parent / "Lib" / "db"

def find_existing_database():
    for file in os.listdir(path):
        if file.endswith("_database.db"):
            return True
    return False

def prompt_for_world_name():
    # Ask for the world name
    world_name = simpledialog.askstring("World Name", "Please Enter a world name:")

    return world_name.strip() if world_name else None

def create_database():
    name = prompt_for_world_name()
    
    # Quick if for verification of name
    if name is None:
        print("Invalid world name. Aborting.")
        return None  # Return None if the name is invalid

    database_folder = path
    database_folder.mkdir(parents=True, exist_ok=True)

    DATABASE_URL = rf'sqlite:///{database_folder}/{name.lower().replace(" ", "_")}_database.db'
    print(f"Database URL: {DATABASE_URL}")

    world_builder = WorldBuilder(database_url=DATABASE_URL)

    with world_builder.get_session() as session:
        try:
            world = WorldBuilder.World(name=name)
            session.add(world)
            session.commit()
            print(session.query(WorldBuilder.World).first().name)
            return name, DATABASE_URL  # Return the created database url
        except SQLAlchemyError as e:
            print(f"Error: {e}")
            os.remove(DATABASE_URL)
            return None

def look_for_database():
    if not find_existing_database():
        create_database()
    else:
        print('Database Found. Aborting Creation.')

if __name__ == '__main__':
    look_for_database()