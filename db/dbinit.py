from sqlalchemy import create_engine
from base import Base

if __name__ == '__main__':
    # Initialize the database with all the models found in models.py
    from session import engine
    from models import *
    Base.metadata.create_all(engine)
