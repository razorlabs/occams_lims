from occams.datastore import upgrading

from avrc.aeh import Logger as logger
from occams.lab.upgrades import migrate as repository

from occams.lab import model
from occams.lab import Session
PROFILE = 'profile-occams.lab:default'


def import_(context):
    u"""
    Locks the site_id column.
    This upgrade assumes patient content has already been migrated.
    """
    logger.info(u'Finalizing new tables on %s' % Session.bind.url.database)
    upgrading.sync(model.LabModel.metadata, Session.bind, repository, 1)
    logger.info('Upgrade complete!')
