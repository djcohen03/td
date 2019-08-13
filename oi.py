import time
import datetime
import traceback
import matplotlib.pyplot as plt
from db.models import Tradable, Option, OptionData, session


class OpenInterest(object):
    def __init__(self, name='SPY'):
        '''
        '''
        self.name = name
        self.tradable = session.query(Tradable).filter_by(name=self.name).first()
        self.chain, self.underlying = self.getchain()

        self.callcolor = (1.0, 0, 0, 0.4)
        self.putcolor = (0, 0, 1.0, 0.4)

    def plot(self, folder='ois/gif', minval=250, items=160, step=0.5, ylim=None):
        ''' Plot self.chain
        '''
        if ylim is None:
            ylim = max([max([max(t.values()) for t in v]) for v in [item.values() for item in self.chain.values()]])

        dtes = sorted(self.chain.keys())
        for index, dte in enumerate(dtes):

            plt.figure(figsize=(16, 8))
            expirationchain = self.chain[dte]
            puts = expirationchain['PUT']
            calls = expirationchain['CALL']

            # Get Axis, Bar Values:
            # strikes = sorted(list(set(puts.keys() + calls.keys())))
            strikes = [minval + i * step for i in range(items)]
            putvals = [puts.get(strike, 0) for strike in strikes]
            callvals = [calls.get(strike, 0) for strike in strikes]

            # Plot:
            plt.bar(strikes, putvals, label='Puts', color=self.putcolor, edgecolor=(0, 0, 0, 0))
            plt.bar(strikes, callvals, label='Calls', color=self.callcolor, edgecolor=(0, 0, 0, 0))

            # Add a black vertical line where the current price is:
            plt.axvline(x=self.underlying, color='black', lw=1.75)

            # Attempt to compute and add the open-interest-weighted predictor:
            oiestimator = self.oipredictor(expirationchain)
            if oiestimator:
                plt.axvline(x=oiestimator, color='purple', lw=1.75)

            # Use a standard yaxis limit:
            if ylim:
                plt.ylim([0, ylim])


            plt.legend()
            plt.ylabel('Open Interest')
            plt.title('%s DTE' % dte)
            # plt.show()
            filename = '%s/%s' % (folder, str(index).zfill(4))
            plt.savefig(filename, edgecolor='black')
            plt.close()


    def oipredictor(self, chain):
        ''' Calculates the Weighted Open-Interest predictor based on the
            following White Paper:
            https://www.researchgate.net/publication/305194232_Trading_on_the_information_content_of_open_interest_Evidence_from_the_US_equity_options_market
        '''
        puts = chain['PUT']
        calls = chain['CALL']

        callinterest = sum(calls.values())
        putinterest = sum(puts.values())

        weightedcallinterests = sum([strike * oi for strike, oi in calls.iteritems()])
        weightedputinterests = sum([strike * oi for strike, oi in puts.iteritems()])

        if callinterest or putinterest:
            estimate = (weightedcallinterests + weightedputinterests) / (callinterest + putinterest)
            return estimate
        else:
            # Avoid division by zero error
            return None


    def getchain(self):
        ''' Get the most recent options surface for this object's tradable
            Data is returned as follows:
                data = { dte -> { type -> { strike -> OI } } }
        '''
        start = time.time()

        # Get All Option IDs for this Tradable:
        print 'Fetching %s Options...' % self.tradable.name
        query = session.execute("SELECT id FROM options WHERE tradable_id=%s;" % self.tradable.id)
        optionids = [str(id) for (id,) in query]

        # Get the Time of The Most Recent Options Data Query For this Tradable:
        print 'Determining Most Recent Fetch Time...'
        query = session.execute("SELECT MAX(time) FROM options_data WHERE option_id IN (%s);" % ', '.join(optionids))
        mostrecent = list(query)[0][0]
        print 'Most recent Fetch Was: %s' % mostrecent

        # Get the options data ids for the most recent fetch:
        print 'Fetching Most Recent Fetch Options Data IDs...'
        query = session.execute("SELECT id FROM options_data WHERE time='%s';" % str(mostrecent))
        dataids = [int(id) for (id,) in query]

        # Get all the options Values:
        print 'Collecting Options Data Records From Most Recent API Fetch...'
        values = session.query(OptionData).filter(OptionData.id.in_(dataids)).all()

        print 'Constructing Options Chain...'

        data = {}

        underlying = None
        for value in values:
            underlying = float(value.underlying)
            strike = float(value.option.strike)
            oi = value.openinterest
            dte = value.dte
            data.setdefault(dte, {})
            data[dte].setdefault(value.option.type, {})
            data[dte][value.option.type][strike] = oi

        print 'Finished Constructing Options Chain in %.2fs' % (time.time() - start,)
        return data, underlying

if __name__ == '__main__':
    oi = OpenInterest('SPY')
    oi.plot()
