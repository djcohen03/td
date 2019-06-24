import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import dbpaths

engine = create_engine(dbpaths.aws)
Session = sessionmaker(bind=engine)
Session.configure(bind=engine)

session = Session()
