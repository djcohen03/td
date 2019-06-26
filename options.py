import time
import datetime
import tdtoken
from tdclient import TDClient
from db.models import Tradable, Option, OptionData, session

class Helpers(object):
    @classmethod
    def ismarketopen(cls):
        ''' Determine if the market is open
        '''
        now = datetime.datetime.now()
        if now.weekday() >= 5:
            print 'It is a Weekend, Market is Closed...'
            return False
        elif now.hour >= 20 or (now.hour <= 13 and now.minute < 30):
            print 'Market Is Closed for the Day (%s)...' % now
            return False
        print 'Market is current open: %s' % now
        return True

    @classmethod
    def getoption(cls, tradable, expiration, type, description, symbol, exchange, expirationtype, strike):
        ''' Get the given Option if it exists, else create a new Option instace
        '''
        option = session.query(Option).filter_by(symbol=symbol).first()
        if option:
            return option
        else:
            option = Option(
                tradable=tradable,
                type=type,
                description=description,
                symbol=symbol,
                exchange=exchange,
                expirationtype=expirationtype,
                strike=strike,
                expiration=expiration,
            )
            return option

class OptionsDataClient(object):
    def __init__(self, token, clientid):
        ''' Client for Repeatedly Fetching & Storing Options Chain Data
        '''
        self.tdclient = TDClient(token, clientid)

    def authenticate(self):
        ''' Refresh the TD API Session
        '''
        self.tdclient.authenticate()

    def fetch(self, name):
        '''
        '''
        start = time.time()
        # Query the TD API:
        tradable = session.query(Tradable).filter_by(name=name).first()
        response = self.tdclient.optionschain(tradable.name)

        self._parse(response, tradable)

        print 'Finished Fetching %s Options Data In %.2fs' % (tradable, time.time() - start)

    def _parse(self, data, tradable):
        ''' Parse the options chain data and insert in into the Database
        '''

        # Gather some constant values:
        riskfree = data['interestRate']
        underlying = data['underlyingPrice']
        now = datetime.datetime.now()

        # Parse the Calls and Puts in the Response:
        calls = data['callExpDateMap']
        puts = data['putExpDateMap']

        # Loop Through The Entire Options Chain:
        alloptions = []
        alloptionsdata = []
        for datemap, calltype in [(calls, 'Calls'), (puts, 'Puts')]:
            dates = datemap.keys()
            for datestr in sorted(dates):
                # Parse the Date String into a datetime object:
                expdate, _ = datestr.split(':')
                expiration = datetime.datetime.strptime(expdate, '%Y-%m-%d').date()

                print 'Parsing %s %s for: %s..' % (expdate, calltype, tradable)

                # Loop Through All Strike Prices for the given expiration Date:
                for strikestr in datemap[datestr]:
                    # Get this Options Data:
                    strike = float(strikestr)
                    data = datemap[datestr][strikestr][0]

                    # Get or Create the Option:
                    option = Helpers.getoption(
                        tradable=tradable,
                        expiration=expiration,
                        type=data['putCall'],
                        description=data['description'],
                        symbol=data['symbol'],
                        exchange=data['exchangeName'],
                        expirationtype=data['expirationType'],
                        strike=strike,
                    )
                    # Create & Save a new OptionsData row instance:
                    optiondata = OptionData(
                        ask=data['ask'],
                        asksize=data['askSize'],
                        bid=data['bid'],
                        bidsize=data['bidSize'],
                        close=data['closePrice'],
                        dte=data['daysToExpiration'],
                        delta=data['delta'],
                        gamma=data['gamma'],
                        low=data['lowPrice'],
                        high=data['highPrice'],
                        itm=data['inTheMoney'],
                        last=data['last'],
                        lastsize=data['lastSize'],
                        mark=data['mark'],
                        markchange=data['markChange'],
                        rho=data['rho'],
                        theovalue=data['theoreticalOptionValue'],
                        theovol=data['theoreticalVolatility'],
                        theta=data['theta'],
                        timevalue=data['timeValue'],
                        volume=data['totalVolume'],
                        vega=data['vega'],
                        volatility=data['volatility'],
                        option=option,
                        time=now,
                        riskfree=riskfree,
                        underlying=underlying,
                    )
                    alloptions.append(option)
                    alloptionsdata.append(optiondata)

        print 'Saving %s New Options Data Instances For %s...' % (len(alloptionsdata), tradable)
        session.add_all(alloptions)
        session.add_all(alloptionsdata)
        session.commit()


if __name__ == '__main__':
    if Helpers.ismarketopen():
        client = OptionsDataClient(tdtoken.token, 'DJCOHEN0115')
        tradables = session.query(Tradable).filter_by(name='SPY').all()
        for tradable in tradables:
            client.fetch(tradable.name)
