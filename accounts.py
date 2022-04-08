import os
import time
import logging
import datetime
from td.client import TDClient
from td.database.models import *
from td.database.config import db_config

log = logging.getLogger('td.accounts')

class Helpers(object):
    @classmethod
    def getaccount(cls, accountid):
        ''' Get/Create an Account based on the given Account ID
        '''
        account = db_config.session.query(Account).get(accountid)
        if account:
            return account
        else:
            log.info('Creating New Account %s...' % accountid)
            account = Account(id=accountid)
            db_config.session.add(account)
            db_config.session.commit()
            return account


class AccountDataClient(object):
    def __init__(self):
        ''' Client for Repeatedly Fetching & Storing Options Chain Data
        '''
        self.clientid = os.environ.get('TDCLIENTID')
        self.token = Token.current().token
        self.tdclient = TDClient(self.token, self.clientid)

    def authenticate(self):
        ''' Refresh the TD API Session
        '''
        self.tdclient.authenticate()

    def isauthenticated(self):
        ''' Determine if session is authenticated
        '''
        return self.tdclient.isauthenticated()

    def accounts(self):
        ''' Load all available accounts
        '''
        # Make sure the session is still valid:
        if not self.isauthenticated():
            self.authenticate()

        # Make API Request:
        accounts = self.tdclient.request('get', '/v1/accounts')

        #
        start = time.time()
        now = datetime.datetime.now()

        for accountjson in accounts:
            # Get Native Account Database Object:
            accountid = int(accountjson['securitiesAccount']['accountId'])
            account = Helpers.getaccount(accountid)

            # Get Account Balance Info:
            current = accountjson['securitiesAccount']['currentBalances']
            cash = float(current['availableFunds'])
            value = float(current['liquidationValue'])
            initial = float(current['moneyMarketFund'])

            # Create new AccountBalance snapshot:
            balance = AccountBalance(
                time=now,
                cash=cash,
                value=value,
                initial=initial,
                account=account
            )
            db_config.session.add(balance)
            db_config.session.commit()

        log.info('Finished Adding Balances For %s Accounts In %.2fs' % (
            len(accounts),
            time.time() - start,
        ))


    def orders(self):
        ''' Load all orders
        '''
        # Make sure the session is still valid:
        if not self.isauthenticated():
            self.authenticate()

        # Make API Request:
        orders = self.tdclient.request('get', '/v1/orders')

        # todo: parse & save orders information
        # ...
        # ...



if __name__ == '__main__':
    client = AccountDataClient()
    client.accounts()
    # client.orders()
