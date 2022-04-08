from td.database.config import Model
from td.database.mixins import CreatedAtMixin
from sqlalchemy import Column, Integer, Numeric, String, Boolean, ForeignKey, Date, DateTime, Enum
from sqlalchemy.orm import relationship

class Tradable(Model, CreatedAtMixin):
    ''' Class to Represent a Stock Market Equity
    '''
    __tablename__ = 'tradables'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    enabled = Column(Boolean)

    options = relationship('Option')
    fetches = relationship('OptionsFetch')

    def volatilities(self):
        ''' Returns a list of 2-tuples of datetimes/volatilities for this tradable
        '''
        return sorted([
            (f.time, float(f.volatility))
            for f in self.fetches
            if f.volatility
        ])

    def lastfetch(self):
        ''' Get the most recent options fetch for this tradable
        '''
        fetches = self.fetches
        if fetches:
            return max(fetches, key=lambda x: x.time)
        else:
            return None

    def ivrank(self):
        ''' Try to get the most recent IV Rank for this tradable
        '''
        fetch = self.lastfetch()
        if fetch:
            try:
                return fetch.ivrank()
            except:
                return None
        else:
            return None

    def __repr__(self):
        return '<Tradable: %s>' % self.name
