from td.database.config import Model, db_config
from td.database.mixins import CreatedAtMixin
from sqlalchemy import Column, Integer, Numeric, String, Boolean, ForeignKey, Date, DateTime, Enum
from sqlalchemy.orm import relationship

class Token(Model, CreatedAtMixin):
    ''' Class to Represent a TD API Token
    '''
    __tablename__ = 'tokens'
    id = Column(Integer, primary_key=True)
    token = Column(String, nullable=False, unique=True)
    date = Column(Date, nullable=False)

    @classmethod
    def current(cls):
        ''' Get the current Token
        '''
        tokens = cls.query.all()
        return max(tokens, key=lambda token: token.date)

    @property
    def daysleft(self):
        ''' Number of days left until this token becomes invalid
        '''
        return max(0, 90 - self.dayssince)

    @property
    def dayssince(self):
        ''' Days since issuing this token
        '''
        return (datetime.date.today() - self.date).days

    @property
    def expires(self):
        ''' Date that this Token Expires
        '''
        return self.date + relativedelta(days=90)

    @property
    def isvalid(self):
        ''' Determine if this token is still valid
        '''
        return self.daysleft > 0

    @property
    def truncated(self):
        ''' Truncated Token For Display
        '''
        return self.token[:6]
