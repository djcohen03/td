from dateutil.relativedelta import relativedelta
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, Numeric, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base
from .session import session, engine


class Tradable(Base):
    ''' Class to Represent a Stock Market Equity
    '''
    __tablename__ = 'tradables'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    enabled = Column(Boolean)

    options = relationship('Option')
    fetches = relationship('OptionsFetch')

    def __repr__(self):
        return '<Tradable: %s>' % self.name


class Option(Base):
    ''' Class to Represent an Option
    '''
    __tablename__ = 'options'
    id = Column(Integer, primary_key=True)
    type = Column(String)
    description = Column(String)
    symbol = Column(String)
    exchange = Column(String)
    expirationtype = Column(String)
    strike = Column(Numeric)
    expiration = Column(Date)

    tradable_id = Column(Integer, ForeignKey('tradables.id'))
    tradable = relationship('Tradable')
    values = relationship('OptionData')

    def __repr__(self):
        return '<%s %s Option, %s - %s>' % (
            self.tradable.name,
            self.type,
            self.strike,
            self.expiration
        )

class OptionData(Base):
    ''' Class to Represent an Option Data Snapshot
    '''
    __tablename__ = 'options_data'
    id = Column(Integer, primary_key=True)
    ask = Column(Numeric)
    asksize = Column(Numeric)
    bid = Column(Numeric)
    bidsize = Column(Numeric)
    close = Column(Numeric)
    dte = Column(Integer)
    delta = Column(Numeric)
    gamma = Column(Numeric)
    low = Column(Numeric)
    high = Column(Numeric)
    itm = Column(Boolean)
    last = Column(Numeric)
    lastsize = Column(Numeric)
    mark = Column(Numeric)
    markchange = Column(Numeric)
    rho = Column(Numeric)
    theovalue = Column(Numeric)
    theovol = Column(Numeric)
    theta = Column(Numeric)
    timevalue = Column(Numeric)
    volume = Column(Numeric)
    vega = Column(Numeric)
    volatility = Column(Numeric)
    time = Column(DateTime)
    underlying = Column(Numeric)
    riskfree = Column(Numeric)
    openinterest = Column(Integer)

    option_id = Column(Integer, ForeignKey('options.id'))
    option = relationship('Option')

    fetch_id = Column(Integer, ForeignKey('options_fetch.id'))
    fetch = relationship('OptionsFetch')

    __mapper_args__ = {
        'order_by': time
    }

    def __repr__(self):
        return '<OptionData: %s>' % self.time

class OptionsFetch(Base):
    '''
    '''
    __tablename__ = 'options_fetch'
    id = Column(Integer, primary_key=True)

    tradable_id = Column(Integer, ForeignKey('tradables.id'))
    tradable = relationship('Tradable')
    values = relationship('OptionData')

    time = Column(DateTime)
    volatility = Column(Numeric)
    oi = Column(Integer)
    volume = Column(Integer)

    __mapper_args__ = {
        'order_by': time
    }

    @property
    def cststring(self):
        ''' Convert the given datetime into a CST String
        '''
        return self.csttime.strftime('%B %d at %I:%M') # Central')

    @property
    def csttime(self):
        ''' Convert the given datetime into a CST String
        '''
        return self.time - relativedelta(hours=5)

    @property
    def spot(self):
        ''' Gets the spot price for this surface fetch
        '''
        sample = self.values[0]
        return float(sample.underlying)
