from td.database.config import Model
from td.database.mixins import CreatedAtMixin
from sqlalchemy import Column, Integer, Numeric, String, Boolean, ForeignKey, Date, DateTime, Enum
from sqlalchemy.orm import relationship

class Account(Model, CreatedAtMixin):
    ''' TD Ameritrade Account
    '''
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)

class AccountBalance(Model, CreatedAtMixin):
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
