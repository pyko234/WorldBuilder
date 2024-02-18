from sqlalchemy import create_engine, Column, Integer, String, Text, BLOB
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import inspect


Base = declarative_base()

class WorldBuilder:
    def __init__(self, database_url=None):
        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(bind=self.engine)

    # Mapping of table names to their corresponding class objects
        self.table_classes = {
            'tags': WorldBuilder.Tag,
            'world': WorldBuilder.World,
            'planes': WorldBuilder.Planes_of_Exsitence,
            'continents': WorldBuilder.Continents,
            'regions': WorldBuilder.Regions,
            'countries': WorldBuilder.Countries,
            'cities': WorldBuilder.Cities,
            'historical_events': WorldBuilder.Historical_Events,
            'religions': WorldBuilder.Religions,
            'characters': WorldBuilder.Characters,
            'deities': WorldBuilder.Deites,
            'enemies': WorldBuilder.Enemies,
            'items': WorldBuilder.Items,
            'quests': WorldBuilder.Quests,
        }

    class Tag(Base):
        __tablename__ = 'tags'
        id = Column(Integer, primary_key=True)
        entry_name = Column(String, nullable=False)
        entry_location = Column(String, nullable=False)

    class World(Base):
        __tablename__ = 'world'
        name = Column(Text, primary_key=True)
        world_map = Column(BLOB, nullable=True)

    class Planes_of_Exsitence(Base):
        __tablename__ = 'planes'
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        description = Column(Text, nullable=True)
        tags = Column(Text, nullable=True)
        image_data = Column(BLOB, nullable=True)

    class Continents(Base):
        __tablename__ = 'continents'
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        description = Column(Text, nullable=True)
        tags = Column(Text, nullable=True)
        image_data = Column(BLOB, nullable=True)

    class Regions(Base):
        __tablename__ = 'regions'
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        description = Column(Text, nullable=True)
        tags = Column(Text, nullable=True)
        image_data = Column(BLOB, nullable=True)

    class Countries(Base):
        __tablename__ = 'countries'
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        description = Column(Text, nullable=True)
        tags = Column(Text, nullable=True)
        image_data = Column(BLOB, nullable=True)

    class Cities(Base):
        __tablename__ = 'cities'
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        description = Column(Text, nullable=True)
        tags = Column(Text, nullable=True)
        image_data = Column(BLOB, nullable=True)

    class Historical_Events(Base):
        __tablename__ = 'historical_events'
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        description = Column(Text, nullable=True)
        tags = Column(Text, nullable=True)
        image_data = Column(BLOB, nullable=True)

    class Religions(Base):
        __tablename__ = 'religions'
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        description = Column(Text, nullable=True)
        tags = Column(Text, nullable=True)
        image_data = Column(BLOB, nullable=True)

    class Characters(Base):
        __tablename__ = 'characters'
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        description = Column(Text, nullable=True)
        stats = Column(Text, nullable=True)
        tags = Column(Text, nullable=True)
        image_data = Column(BLOB, nullable=True)

    class Deites(Base):
        __tablename__ = 'deities'
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        description = Column(Text, nullable=True)
        stats = Column(Text, nullable=True)
        tags = Column(Text, nullable=True)
        image_data = Column(BLOB, nullable=True)

    class Enemies(Base):
        __tablename__ = 'enemies'
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        description = Column(Text, nullable=True)
        stats = Column(Text, nullable=True)
        tags = Column(Text, nullable=True)
        image_data = Column(BLOB, nullable=True)

    class Items(Base):
        __tablename__ = 'items'
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        description = Column(Text, nullable=True)
        tags = Column(Text, nullable=True)
        image_data = Column(BLOB, nullable=True)


    class Quests(Base):
        __tablename__ = 'quests'
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        description = Column(Text, nullable=True)
        tags = Column(Text, nullable=True)

    def get_table_class(self, table_name):
        # Returns the class object for a given table name.
        return self.table_classes.get(table_name)

    def get_session(self):
        Session = sessionmaker(bind=self.engine)
        return Session()