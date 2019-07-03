import time
import datetime
import traceback
import matplotlib.pyplot as plt
from db.models import Tradable, Option, OptionData, session

def plotchain(chain, filename, title, ylower=0, yupper=40):
    plt.figure(figsize=(16, 8))
    # Sort the chain by delta:
    for (ctype, color) in [('CALL', (1.0, 0, 0)), ('PUT', (0, 0, 1.0))]:
        values = chain[ctype]

        # bin by DTE:
        expirations = {}
        for delta, vol, dte in values:
            expirations.setdefault(dte, []).append((delta, vol))
        for dte, ladder in expirations.iteritems():
            # Sort by delta:
            ladder.sort()
            deltas, vols = zip(*ladder)

            # Determine the Color and Line Width:
            alpha = (1. / (dte + 1)) ** 0.25
            colors = color + (alpha,)
            linewidth = 4 * alpha / 2

            # Plot the Line:
            plt.plot(deltas, vols, '-', color=colors, linewidth=linewidth)
    plt.xlim(-1, 1)
    plt.ylim(ylower, yupper)
    plt.axvline(x=0.5, color='black')
    plt.axvline(x=-0.5, color='black')

    plt.xlabel('Delta')
    plt.ylabel('IV')
    plt.title(title)
    plt.legend(['Calls', 'Puts'])
    # plt.show()
    plt.savefig(filename, edgecolor='black')
    print 'Saved New Skew Chart %s' % filename


def makechart(filename, title, name='SPY', yupper=40, maxspread=0.1):
    print 'Constructing Skew Chart for %s...' % name
    start = time.time()

    # Get the most recent options chain:
    chain = getchain(name=name, maxspread=maxspread)

    # Plot the most recent options chain:
    plotchain(chain, filename, title, ylower=0, yupper=yupper)
    print 'Finished makechart in %.2fs' % (time.time() - start)

def getchain(name='SPY', maxspread=0.1):
    ''' Get the most recent options chain for the given tradable, filtering by
        the given maximum bid/ask spread
    '''
    tradable = session.query(Tradable).filter_by(name=name).first()

    # Get All Option IDs for this Tradable:
    print 'Fetching %s Options...' % tradable.name
    query = session.execute("SELECT id FROM options WHERE tradable_id=%s;" % tradable.id)
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
    chain = {
        'PUT': [],
        'CALL': []
    }
    for value in values:
        if abs(value.bid - value.ask) <= maxspread and abs(value.volatility) < 100.0:
            chain[value.option.type].append((
                float(value.delta), # if delta >= 0 else delta * -5.,
                float(value.volatility),
                value.dte
            ))
    return chain


def getchains(name='SPY'):
    start = time.time()
    tradable = session.query(Tradable).filter_by(name=name).first()

    # Get a list of timestamps:
    query = session.execute('SELECT time, count(*) from options_data group by time;')
    timestamps = [str(timestamp) for timestamp, count in query if count > 500]

    chains = {
        timestamp: {
            'PUT': [],
            'CALL': []
        }
        for timestamp in timestamps
    }

    for ctype in ('CALL', 'PUT'):
        # Get all valid option ids for this tradable:
        query = session.execute(
            "SELECT id FROM options WHERE type='%s' AND tradable_id=%s;" % (
                ctype,
                tradable.id
            )
        )
        optionids = [str(id) for (id,) in query]

        for timestamp in timestamps:
            print 'Loading %s Options Data from %s...' % (ctype, timestamp)
            query = session.execute(
                "SELECT bid, ask, dte, delta, volatility FROM options_data WHERE time='%s' AND option_id IN (%s);" % (
                timestamp,
                ', '.join(optionids)
            ))
            for bid, ask, dte, delta, volatility in query:
                if abs(bid - ask) < 0.10:
                    chains[timestamp][ctype].append((
                        float(delta),
                        float(volatility),
                        float(dte)
                    ))

    # Delete any empty/incomplete timestamps:
    for timestamp in timestamps:
        calls = chains[timestamp]['CALL']
        puts = chains[timestamp]['PUT']
        if not calls or not puts:
            del chains[timestamp]

    print 'Loaded %s Options Chain Snapshots in %.2fs' % (len(chains), time.time() - start)
    return chains


def makegif(name='SPY', folder='skews/gifs'):
    chains = getchains(name=name)
    for timestamp, chain in chains.iteritems():
        try:
            dt = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
            filename = '%s/%s-%s.jpg' % (folder, name, dt.strftime('%s'))
            plotchain(
                chain=chain,
                filename=filename,
                title=dt.strftime('%a %b %d at %I:%M %p'),
                ylower=0,
                yupper=40
            )
        except:
            print traceback.format_exc()

if __name__ == '__main__':
    makegif()
