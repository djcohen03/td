import time
from db.models import session, Tradable

class OptionsStats(object):
    def __init__(self, tradable):
        self.tradable = tradable
        self.load()

    def load(self):
        print 'Loading Options Data for %s...' % self.tradable
        start = time.time()
        self.options = self.tradable.options
        self.values = []
        for option in self.options:
            self.values.append(option.values)
        print 'Loaded %s Data Points for %s Options Contracts for %s In %.2fs' % (
            len(self.values),
            len(self.options),
            self.tradable,
            time.time() - start,
        )


if __name__ == '__main__':
    tradables = session.query(Tradable).filter_by(name='SPX').first()
