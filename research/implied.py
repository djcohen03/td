import math
import json
import time
import logging
import datetime
import traceback


class PutCall(object):
    def __init__(self, put, call):
        assert put.option.strike == call.option.strike
        self.put = put
        self.call = call

        self.strike = float(self.put.option.strike)
        self.putmid = float(self.put.theovalue)
        self.callmid = float(self.call.theovalue)
        self.difference = abs(self.callmid - self.putmid)

        self.putBid = float(self.put.bid)
        self.putAsk = float(self.put.ask)
        self.callBid = float(self.call.bid)
        self.callAsk = float(self.call.ask)


class Helpers(object):
    @classmethod
    def volforladder(cls, dte, surface):
        ''' Get the near-term and next-term volatility for the surface's options
            that have the given DTE
        '''
        # Filter out Options to only use
        options = filter(lambda o: o.dte == dte, surface)

        # Use the risk free rate of the first option:
        rfree = float(options[0].riskfree)
        minutes = float(dte) * 60. * 24. / 525600.

        #
        puts = filter(lambda o: o.option.type == 'PUT', options)
        calls = filter(lambda o: o.option.type == 'CALL', options)
        puts.sort(key=lambda x: x.option.strike)
        calls.sort(key=lambda x: x.option.strike)

        assert len(puts) == len(calls)

        # Zip all equal striked calls and puts into PutCalls objects:
        options = [PutCall(puts[i], calls[i]) for i in range(len(puts))]

        # Get forward price:
        foption = min(options, key=lambda x: x.difference)
        forward = foption.strike + math.exp(minutes * rfree) * (foption.callmid - foption.putmid)

        # Find the pivot strike price:
        k0 = max(o.strike for o in options if o.strike < forward)

        # Get all calls and puts above and below k0, repectively:
        puts = filter(lambda o: o.strike <= k0, options)
        calls = filter(lambda o: o.strike >= k0, options)
        puts.sort(key=lambda o: o.strike, reverse=True)
        calls.sort(key=lambda o: o.strike)

        # Filter out calls & puts with zero bids:
        puts = cls.filterbybid(puts, put=True)
        calls = cls.filterbybid(calls, put=False)


        # Take a weighted sum across the filtered set of calls and puts:
        wsum = 0.
        for i, put in enumerate(puts[1:-1]):
            delta = (puts[i].strike - puts[i + 2].strike) / 2.
            wsum += delta * put.putmid / (put.strike ** 2)

        for i, call in enumerate(calls[1:-1]):
            delta = (calls[i + 2].strike - calls[i].strike) / 2.
            wsum += delta * call.callmid / (call.strike ** 2)

        # Add in border put:
        bput = puts[-1]
        delta = puts[-2].strike - bput.strike
        wsum += delta * bput.putmid / (bput.strike ** 2)
        # Add in border call:
        bcall = calls[-1]
        delta = bcall.strike - calls[-2].strike
        wsum += delta * bcall.callmid / (bcall.strike ** 2)

        # Add in averaged pivot put/call option:
        midoption = puts[0]
        midprice = (midoption.callmid + midoption.putmid) / 2.
        delta = (calls[1].strike - puts[1].strike) / 2.
        wsum += delta * midprice / midoption.strike ** 2

        # Do one final computation to get the vol metric for this level:
        vol = (2. / minutes) * wsum * math.exp(minutes * rfree) - (forward / k0 - 1) ** 2 / minutes
        return minutes, vol

    @classmethod
    def filterbybid(cls, options, put=True):
        ''' Filter the sorted options as follows:
                - If bid is zero, skip
                - If two consecutive zero bids are found, terminate
        '''
        consecutive = 0
        filtered = []
        for option in options:
            bid = option.putBid if put else option.callBid
            if bid == 0.:
                consecutive += 1
                if consecutive == 2:
                    break
            else:
                filtered.append(option)
                consecutive = 0
        return filtered

class VIXImplied(object):
    @classmethod
    def getiv(cls, fetch):
        ''' Get the most recent options surface for the given tradable symbol
        '''
        surface = fetch.values
        dtes = set(item.dte for item in fetch.values)
        neardte = min(i for i in dtes if i > 23)
        nextdte = max(i for i in dtes if i < 37)
        nearmin, nearvol = Helpers.volforladder(neardte, surface)
        nextmin, nextvol = Helpers.volforladder(nextdte, surface)

        # Take the weighted average of the two ladders around 30 days:
        year = 525600.
        month = 43200.
        nt1 = nearmin * year
        nt2 = nextmin * year
        t1 = nearmin * nearvol * ((nt2 - month) / (nt2 - nt1))
        t2 = nextmin * nextvol * ((month - nt1) / (nt2 - nt1))
        return math.sqrt((t1 + t2) * year / month) * 100.

    @classmethod
    def volume(cls, fetch):
        ''' Get total volume for the given options surface
        '''
        return sum([option.volume for option in fetch.values if option.volume])

    @classmethod
    def openinterest(cls, fetch):
        ''' Get total open interest for the given options surface
        '''
        return sum([option.openinterest for option in fetch.values if option.openinterest])
