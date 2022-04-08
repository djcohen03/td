from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.hybrid import hybrid_property
import pytz

et = pytz.timezone('America/New_York')

def _as_et(t):
    return t.astimezone(et)

class CreatedAtMixin(object):
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @hybrid_property
    def created_at_as_et(self):
        return _as_et(self.created_at.replace(tzinfo=pytz.UTC))

    @hybrid_property
    def updated_at_as_et(self):
        return _as_et(self.updated_at.replace(tzinfo=pytz.UTC))
