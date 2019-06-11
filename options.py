import time
import datetime
import tdtoken
from tdclient import TDClient
from db.models import Tradable, Option, OptionData, session

class Helpers(object):
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
            print 'Created: %s' % option
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

        # Gather some base values:
        interest = response['interestRate']
        price = response['underlyingPrice']

        # Parse the Calls and Puts in the Response:
        self._parse(response['callExpDateMap'], tradable, price, interest)
        self._parse(response['putExpDateMap'], tradable, price, interest)

        print 'Finished Fetching %s Options Data In %.2fs' % (tradable, time.time() - start)

    def _parse(self, datemap, tradable, underlyingprice, interest):
        ''' Parse the options chain data and insert in into the Database
        '''
        now = datetime.datetime.now()
        bulksave = []
        for datestr in datemap:
            expdate, _ = datestr.split(':')
            expiration = datetime.datetime.strptime(expdate, '%Y-%m-%d').date()

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
                    theoreticalvalue=data['theoreticalOptionValue'],
                    theoreticalvol=data['theoreticalVolatility'],
                    theta=data['theta'],
                    timevalue=data['timeValue'],
                    volume=data['totalVolume'],
                    vega=data['vega'],
                    volatility=data['volatility'],
                    option=option,
                    time=now,
                )
                bulksave.append(option)
                bulksave.append(optiondata)
                print 'Created: %s' % optiondata

        print 'Saving All Data For %s...' % tradable
        session.add_all(bulksave)
        session.commit()




if __name__ == '__main__':
    tradables = session.query(Tradable).filter_by(name='SPY').all()
    client = OptionsDataClient(tdtoken.token, 'DJCOHEN0115')
    for tradable in tradables:
        client.fetch(tradable.name)
