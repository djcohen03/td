import time
import datetime
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


def makechart(name='SPY'):
    print 'Constructing Skew Chart for %s...' % name

    #
    tradable = session.query(Tradable).filter_by(name=name).first()

    # Bin options by expiration date:
    options = {}
    for option in tradable.options:
        options.setdefault(option.expiration, []).append(option)


    # today = datetime.date.today()
    # maxdte = float(max([(k - today).days for k in options.keys()]))
    plt.figure(figsize=(16, 8))
    for date in options:
        chain = {
            'PUT': [],
            'CALL': []
        }
        for option in options[date]:
            value = option.values[-1]
            delta = float(value.delta)
            if abs(value.bid - value.ask) <= 0.10:
                point = (
                    delta, # if delta >= 0 else delta * -5.,
                    float(value.volatility),
                    value.dte
                )
                chain[option.type].append(point)


        # Sort the chain by delta:
        for (ctype, color) in [('CALL', (1.0, 0, 0)), ('PUT', (0, 0, 1.0))]:
            values = chain[ctype]
            if values:
                # Sort and Unpack the Delta/IV/DTE Values:
                values.sort()
                deltas, vols, dte = zip(*values)

                # Determine the Color and Line Width:
                alpha = (1. / (dte[0] + 1)) ** 0.25
                colors = color + (alpha,)
                linewidth = 4 * alpha / 2

                # Plot the Line:
                plt.plot(deltas, vols, '-', color=colors, linewidth=linewidth)

    plt.xlim(-1, 1)
    plt.ylim(10, 30)
    plt.axvline(x=0.5, color='black')
    plt.axvline(x=-0.5, color='black')

    plt.xlabel('Delta')
    plt.ylabel('IV')
    plt.title('%s Delta/IV Skew Across Various Expirations' % tradable.name)
    plt.legend(['Calls', 'Puts'])
    # plt.show()
    filename = 'skews/%s-CallPutSkew-%s' % (tradable.name, int(time.time()))
    plt.savefig(filename, edgecolor='black')

    print 'Saved New Skew Chart %s' % filename

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


def makegif(name='SPY'):
    chains = getchains(name=name)
    for timestamp, chain in chains.iteritems():
        dt = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f+00:00')
        filename = 'skews/gifs/SPY-%s.jpg' % dt.strftime('%s')
        plotchain(
            chain=chain,
            filename=filename,
            title=dt.strftime('%c'),
            ylower=0,
            yupper=40
        )

if __name__ == '__main__':
    makegif()
