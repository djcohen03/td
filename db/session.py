import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# todo: make the database name/user/password configurable:
dbpath = 'postgresql://david:david@localhost/options'
engine = create_engine(dbpath)
Session = sessionmaker(bind=engine)
Session.configure(bind=engine)

session = Session()
