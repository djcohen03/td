import math
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import ListedColormap
from db.models import *

def addalpha(cmap):
    my_cmap = cmap(np.arange(cmap.N))
    my_cmap[:,-1] = np.linspace(0, 1, cmap.N)
    return ListedColormap(my_cmap)


def plotsurface(surface, mindte=0, maxdte=1000, miniv=0., maxiv=1000., maxspread=1.):
    '''
    '''
    ctypes = ['CALL', 'PUT']
    spot = float(surface[0].underlying)
    getmoneyness = lambda o: round((float(o.option.strike) - spot) / spot * 100., 3)
    spread = lambda o: abs(float(o.bid) - float(o.ask))
    mapping = {ctype: {} for ctype in ctypes}

    for option in surface:
        # Check DTE Range:
        if mindte <= option.dte <= maxdte:
            # Check Bid/Ask Spread:
            if spread(option) <= maxspread:
                # Check Vol Range:
                if miniv <= float(option.volatility) <= maxiv:
                    # All checks passed, add item to mapping:
                    moneyness = getmoneyness(option)
                    dte = option.dte
                    iv = float(option.volatility)
                    key = (moneyness, dte)
                    otype = option.option.type
                    mapping[otype][key] = iv


    # Plot the Calls and Puts surfaces:
    for ctype in ctypes:

        # Get sorted list of strikes and dtes:
        points = mapping[ctype].keys()
        strikes, dtes = zip(*points)
        strikes = sorted(set(strikes))
        dtes = sorted(set(dtes))

        def closest(point, count=1):
            distance = lambda p: math.sqrt((point[0] - p[0]) ** 2 + (point[1] - p[1]) ** 2)
            return sorted(points, key=distance)[:count]


        # plot a 3D surface like in the example mplot3d/surface3d_demo
        X, Y = np.meshgrid(strikes, dtes)
        Z = np.full(X.shape, np.nan)

        for i, strike in enumerate(strikes):
            for j, dte in enumerate(dtes):
                iv = mapping[ctype].get((strike, dte))
                if iv:
                    Z[j, i] = iv
                else:
                    # Take the average of the three closest points as the IV:
                    closestpnts = closest((strike, dte), count=10)
                    closestivs = [mapping[ctype][item] for item in closestpnts]
                    iv = sum(closestivs) / float(len(closestivs))
                    Z[j, i] = iv


        # Set up and plot figure:
        fig = plt.figure(figsize=(15, 8))
        ax = fig.add_subplot(1, 1, 1, projection='3d')
        ax.set_xlabel('Moneyness')
        ax.set_ylabel('DTE')
        ax.set_zlabel('IV')
        ax.set_title('%s Implied Volatility Surface' % ctype.title())
        ax.plot_surface(X, Y, Z, cmap=addalpha(plt.cm.RdYlGn))
        plt.show()



if __name__ == '__main__':
    spy = session.query(Tradable).filter_by(name='SPY').first()
    surface = spy.fetches[-1].values
    plotsurface(surface, maxdte=100, miniv=5., maxiv=100., maxspread=0.5)
