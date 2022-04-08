import os
import functools
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask_appbuilder import Model

class DatabaseConfig(object):
    def __init__(self, url):
        ''' Database Connection Client
        '''
        self.url = url
        self.engine = create_engine(
            self.url,
            convert_unicode=True,
            logging_name='core',
            poolclass=NullPool,
            # pool_size=0,
            # max_overflow=10,
            # pool_timeout=10,
        )

        self._session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = scoped_session(self._session)
        Model.query = self.session.query_property()

    @staticmethod
    def urlfromenv():
        ''' Get the full postgres URL from environment variables
        '''
        host = os.environ.get('POSTGRES_HOST', 'db')
        user = os.environ.get('POSTGRES_USER', 'halo')
        password = os.environ.get('POSTGRES_PASSWORD', 'haloninja')
        database = os.environ.get('POSTGRES_DB', 'options')
        url = 'postgresql://%s:%s@%s/%s' % (user, password, host, database)
        return url

    def integrate_with_flask(self, new_engine, new_session):
        '''
        '''
        self.engine = new_engine
        self.session = new_session
        Model.query = self.session.query_property()


Base = declarative_base()
database_uri = DatabaseConfig.urlfromenv()
db_config = DatabaseConfig(database_uri)
db_session = db_config.session


def ensure_db_cleanup():
    def wrapper(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            with db_cleanup():
                return f(*args, **kwargs)
        return wrapped
    return wrapper

@contextmanager
def db_cleanup():
    try:
        yield db_config
    except:
        db_config.session.rollback()
        raise
    else:
        db_config.session.commit()
    finally:
        db_config.session.close()
