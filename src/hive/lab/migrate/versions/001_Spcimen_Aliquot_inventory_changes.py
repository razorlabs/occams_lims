from sqlalchemy import *
from migrate import *
import datetime
metadata = MetaData()

NOW = datetime.datetime.now()

specimen_blueprint_zid = Column('specimen_blueprint_zid', Integer, nullable=True)
aliquot_sent_notes = Column('sent_notes', Unicode)


terms = [
    dict(vocabulary_name='aliquot_state', title=u'Inaccurate Data', token=u'incorrect', value=u'incorrect', is_active=True, create_date=NOW, modify_date=NOW),
    dict(vocabulary_name='aliquot_state', title=u'Check Out', token=u'pending-checkout', value=u'pending-checkout', is_active=True, create_date=NOW, modify_date=NOW),
    dict(vocabulary_name='aliquot_state', title=u'Hold in Queue', token=u'queued', value=u'queued', is_active=True, create_date=NOW, modify_date=NOW),
    dict(vocabulary_name='aliquot_state', title=u'Missing', token=u'missing', value=u'missing', is_active=True, create_date=NOW, modify_date=NOW),
    dict(vocabulary_name='specimen_state', title=u'Batched', token=u'batched', value=u'batched', is_active=True, create_date=NOW, modify_date=NOW),
    dict(vocabulary_name='specimen_state', title=u'Draw Postponed', token=u'postponed', value=u'postponed', is_active=True, create_date=NOW, modify_date=NOW),
    ]

def upgrade(migrate_engine):
    """ Introduces new changes to the specimen/aliquot/terms table necessary
        for inventory processing.
    """
    metadata.bind = migrate_engine

    specimen_table = Table('specimen', metadata, autoload=True)
    aliquot_table = Table('aliquot', metadata, autoload=True)
    vocabulary_table = Table('specimen_aliquot_term', metadata, autoload=True)

    specimen_blueprint_zid.create(specimen_table)
    aliquot_sent_notes.create(aliquot_table)

    metadata.bind.execute(vocabulary_table.insert(), terms)


def downgrade(migrate_engine):
    """ Irreversable, too bad """

