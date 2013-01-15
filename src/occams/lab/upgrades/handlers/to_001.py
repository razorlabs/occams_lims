from occams.datastore import upgrading

from avrc.aeh import Logger as logger
from occams.lab.upgrades import migrate as repository

from occams.lab import model
from occams.lab import Session
from avrc.aeh import PhiSession

PROFILE = 'profile-occams.lab:default'

def import_(context):
    u"""
    Locks the site_id column.
    This upgrade assumes patient content has already been migrated.
    """
    for session in (Session, PhiSession):
        logger.info(u'Finalizing new tables on %s' % session.bind.url.database)
        upgrading.sync(model.LabModel.metadata, session.bind, repository, 1)
        logger.info('Upgrade complete!')
