import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, Numeric, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from base import Base
from session import session, engine


class Tradable(Base):
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

    def ivrank(self):
        ''' Gets the IV Rank of this Options Fetch
        '''
        ivs = [iv for date, iv in self.tradable.volatilities()]
        current = self.volatility
        if ivs and current:
            items = sorted(ivs)
            length = len(items)
            item = float(current)

            # Get the percentiles of each of the items:
            percentiles = [i / float(length - 1) for i, _ in enumerate(items)]

            try:
                # Item is in list:
                minindex = items.index(item)
                maxindex = length - list(reversed(items)).index(item) - 1
                return (percentiles[minindex] + percentiles[maxindex]) / 2. * 100.
            except ValueError:
                # This item is not in the list, so get the percentile of the closest
                # upper and lower numbers and average those two to get the result:
                uppers = filter(lambda x: x > item, items)
                lowers = filter(lambda x: x < item, items)
                upper = min(uppers) if uppers else items[-1]
                lower = max(lowers) if lowers else items[0]

                upperindex = items.index(upper)
                lowerindex = length - list(reversed(items)).index(lower) - 1
                return (percentiles[upperindex] + percentiles[lowerindex]) / 2. * 100.
        else:
            return None


class Token(Base):
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
        tokens = session.query(cls).all()
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


class Account(Base):
    ''' TD Ameritrade Account
    '''
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)

class AccountBalance(Base):
    ''' TD Ameritrade Account Balance
    '''
    __tablename__ = 'account_balances'
    id = Column(Integer, primary_key=True)
    time = Column(DateTime)
    cash = Column(Numeric, nullable=False)
    value = Column(Numeric, nullable=False)
    initial = Column(Numeric, nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    account = relationship('Account')
