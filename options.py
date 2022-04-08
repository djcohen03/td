import os
import time
import logging
import datetime
import traceback
from td.client import TDClient
from td.research.implied import VIXImplied
from td.database.models import *
from td.database.config import db_config

log = logging.getLogger('td.options')

class Helpers(object):
    @classmethod
    def getoption(cls, tradable, expiration, type, description, symbol, exchange, expirationtype, strike):
        ''' Get the given Option if it exists, else create a new Option instace
        '''
        option = db_config.session.query(Option).filter_by(symbol=symbol).first()
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

    def fetch(self, name):
        '''
        '''
        try:
            # Make sure the session is still valid:
            if not self.isauthenticated():
                self.authenticate()

            start = time.time()
            # Query the TD API:
            tradable = db_config.session.query(Tradable).filter_by(name=name).first()
            response = self.tdclient.optionschain(tradable.name)

            self._parse(response, tradable)

            log.info('Finished Fetching %s Options Data In %.2fs' % (tradable, time.time() - start))
        except:
            log.error('An Error Occurred On Fetching %s Options, Skipping...' % name)
            log.error(traceback.format_exc())
            db_config.session.rollback()


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

        # Create an OptionsFetch wrapper for this fetch:
        fetch = OptionsFetch(tradable=tradable, time=now)

        # Loop Through The Entire Options Chain:
        alloptions = []
        alloptionsdata = []
        for datemap, calltype in [(calls, 'Calls'), (puts, 'Puts')]:
            dates = datemap.keys()
            for datestr in sorted(dates):
                # Parse the Date String into a datetime object:
                expdate, _ = datestr.split(':')
                expiration = datetime.datetime.strptime(expdate, '%Y-%m-%d').date()

                log.info('Parsing %s %s for: %s..' % (expdate, calltype, tradable))

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
                        openinterest=data['openInterest'],
                        fetch=fetch
                    )
                    alloptions.append(option)
                    alloptionsdata.append(optiondata)

        log.info('Saving %s New Options Data Instances For %s...' % (len(alloptionsdata), tradable))
        db_config.session.add_all(alloptions)
        db_config.session.add_all(alloptionsdata)
        db_config.session.commit()
        log.info('Saving Complete (%s)' % datetime.datetime.now())

    @classmethod
    def ismarketopen(cls):
        ''' Determine if the market is open
        '''
        now = datetime.datetime.now()
        if now.weekday() >= 5:
            log.info('It is a Weekend, Market is Closed...')
            return False
        elif now.hour > 21 or now.hour < 13:
            log.info('Market Is Closed for the Day (%s)...' % now)
            return False
        log.info('Market is current open: %s' % now)
        return True

    @classmethod
    def updatevols(cls):
        ''' Update the values of OptionsFetch volatility, oi, volume columns
        '''
        # Get the IDs of the all options fetches from the past five days:
        now = datetime.datetime.now()
        days = 5
        cutoff = now - datetime.timedelta(days=days)
        query = db_config.session.query(OptionsFetch.id).filter(OptionsFetch.time > cutoff).all()
        ids = [id for id, in query]
        log.info('Updating %s Options Fetches From the last %s Days...' % (len(ids), days))

        # Update Each Fetch:
        for id in ids:
            fetch = db_config.session.query(OptionsFetch).get(id)

            # Implied Volatility:
            if fetch.volatility is None:
                try:
                    log.info('Loading Implied Vol For %s...' % fetch.id)
                    fetch.volatility = VIXImplied.getiv(fetch)
                except:
                    db_config.session.rollback()
            # Volume:
            if fetch.volume is None:
                log.info('Loading Volume For %s...' % fetch.id)
                fetch.volume = VIXImplied.volume(fetch)

            # Open Interest:
            if fetch.oi is None:
                log.info('Loading Open Interest For %s...' % fetch.id)
                fetch.oi = VIXImplied.openinterest(fetch)

            # Save all changes:
            db_config.session.commit()

if __name__ == '__main__':
    client = OptionsDataClient()
    client.fetch('SPY')
