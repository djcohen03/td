import sys
import traceback
from utils import session, Base, engine

def _getgroups(cutoff=1):
    ''' Get the
    '''
    query = session.execute(''' SELECT * FROM (
            SELECT options_data.time, opts.tradable_id, count(*) AS cnt
            FROM options_data JOIN (
                SELECT id, tradable_id FROM options
            ) AS opts ON options_data.option_id = opts.id
            GROUP BY options_data.time, opts.tradable_id
        )
        AS tmp WHERE tmp.cnt > %s ORDER BY tmp.cnt DESC;
    ''' % cutoff)
    return list(query)


def tradablesmapping():
    ''' Get a mapping from tradable id to a set of all options.id's
    '''
    mapping = {}

    tradables = list(session.execute('SELECT id FROM tradables;'))
    for tradableid, in tradables:
        query = session.execute('SELECT id FROM options where tradable_id = %s;' % tradableid)
        mapping[tradableid] = set(id for id, in query)

    return mapping

def _check():
    print 'Checking Migration Integrity...'
    query = session.execute('''
        SELECT * FROM (
            SELECT options.id, data.tradable_id AS t1, options.tradable_id AS t2
            FROM options JOIN (
                SELECT options_data.option_id, fetches.tradable_id
                FROM options_data JOIN (
                    SELECT id, tradable_id FROM options_fetch
                ) AS fetches
                ON fetches.id = options_data.fetch_id
            ) AS data
            ON options.id = data.option_id
        ) AS comp WHERE comp.t1 != t2;
    ''')
    results = list(query)
    assert len(results) == 0
    print 'Check passed.'




def upgrade():
    '''
    '''
    # Add OptionsData.fetch_id Foreign Key, and Create Index on the Column:
    try:
        # This should create the options_fetch table:
        print 'Creating Table options_data...'
        Base.metadata.create_all(engine)

        session.execute('''
            ALTER TABLE options_data
            ADD COLUMN fetch_id INTEGER
            REFERENCES options_fetch(id);
        ''')
        session.execute('''
            CREATE INDEX idx_options_data_fetch_id ON options_data(fetch_id);
        ''')

        fetches = _getgroups(cutoff=3)
        for time, tradableid, _ in fetches:
            print 'Adding OptionsFetch(%s, %s)...' % (time, tradableid)
            session.execute("INSERT INTO options_fetch (tradable_id, time) values (%s, '%s');" % (tradableid, time))
        session.flush()

        # Now that each of the options fetches has an id, we want to update the
        # FK's on the options data table:
        tradables = tradablesmapping()
        fetches = session.execute('SELECT id, tradable_id, time FROM options_fetch;')
        for id, tradableid, time in fetches:
            print 'Adding options_data.fetch_id FK For Fetch %s..' % id
            session.execute("UPDATE options_data SET fetch_id = %s WHERE time = '%s';" % (id, time))

        session.flush()

        _check()
        session.commit()

    except:
        print traceback.format_exc()
        session.rollback()

def downgrade():
    '''
    '''
    try:
        # Remove OptionsData.fetch_id Column:
        session.execute('ALTER TABLE options_data DROP COLUMN fetch_id;')
        session.execute('DROP TABLE options_fetch;')
        session.commit()
    except:
        print traceback.format_exc()
        session.rollback()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--down':
        downgrade()
    else:
        upgrade()
