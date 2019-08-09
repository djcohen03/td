import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .dbpaths import *

engine = create_engine(dbpath)
Session = sessionmaker(bind=engine)
Session.configure(bind=engine)

session = Session()
