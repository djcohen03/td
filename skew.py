import datetime
import matplotlib.pyplot as plt
from db.models import Tradable, Option, OptionData, session


spy = session.query(Tradable).filter_by(name='SPY').first()

# Bin options by expiration date:
options = {}
for option in spy.options:
    options.setdefault(option.expiration, []).append(option)


# today = datetime.date.today()
# maxdte = float(max([(k - today).days for k in options.keys()]))

for date in options:
    chain = {
        'PUT': [],
        'CALL': []
    }
    for option in options[date]:
        value = option.values[-1]
        point = (
            abs(float(value.delta)),
            float(value.volatility),
            value.dte
        )
        chain[option.type].append(point)


    # Sort the chain by delta:
    for (ctype, color) in [('CALL', (1.0, 0, 0)), ('PUT', (0, 0, 1.0))]:
        chain[ctype].sort()
        deltas, vols, dte = zip(*chain[ctype])

        alpha = (1. / (dte[0] + 1)) ** 0.25
        colors = color + (alpha,)

        linewidth = 4 * alpha / 2

        plt.plot(deltas, vols, '-', color=colors, linewidth=linewidth)

plt.xlim(0.05, 0.8)
plt.ylim(10, 30);
plt.axvline(x=0.5, color='black')
plt.show()
