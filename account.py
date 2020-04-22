import time
import datetime
from tdclient import TDClient
from db.models import session, Token, Account, AccountBalance

class Helpers(object):
    @classmethod
    def getaccount(cls, accountid):
        ''' Get/Create an Account based on the given Account ID
        '''
        account = session.query(Account).get(accountid)
        if account:
            return account
        else:
            print 'Creating New Account %s...' % accountid
            account = Account(id=accountid)
            session.add(account)
            session.commit()
            return account


class AccountDataClient(object):
    def __init__(self, clientid):
        ''' Client for Repeatedly Fetching & Storing Options Chain Data
        '''
        self.token = Token.current().token
        self.tdclient = TDClient(self.token, clientid)

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
            initial = float(accountjson['securitiesAccount']['initialBalances']['totalCash'])

            # Create new AccountBalance snapshot:
            balance = AccountBalance(
                time=now,
                cash=cash,
                value=value,
                initial=initial,
                account=account
            )
            session.add(balance)
            session.commit()

        print 'Finished Adding Balances For %s Accounts In %.2fs' % (
            len(accounts),
            time.time() - start,
        )


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
    client = AccountDataClient('DJCOHEN0115')
    client.accounts()
    client.orders()
