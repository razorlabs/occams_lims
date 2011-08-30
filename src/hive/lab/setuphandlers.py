
from z3c.saconfig import named_scoped_session
from avrc.aeh import FIA_SCOPED_SESSION_KEY
import hive.lab.upgrades.migrate


def importVarious(context):
    """ 
    GenericSetup conventional handle for importing miscellaneous steps.
    """
    if context.readDataFile('hive-lab.txt') is None:
        return
    portal = context.getSite()
    setupSQLDatabase(portal)


def setupSQLDatabase(portal):
    session = named_scoped_session(FIA_SCOPED_SESSION_KEY)
    hive.lab.upgrades.migrate.install(session.bind)

