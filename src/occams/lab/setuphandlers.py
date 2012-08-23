
from z3c.saconfig import named_scoped_session
from occams.lab import SCOPED_SESSION_KEY
from occams.datastore.upgrading import install
from occams.lab import model
import occams.lab.upgrades.migrate as repository

def importVarious(context):
    """
    GenericSetup conventional handle for importing miscellaneous steps.
    """
    if context.readDataFile('occams-lab.txt') is None:
        return
    portal = context.getSite()
    setupSQLDatabase(portal)


def setupSQLDatabase(portal):
    session = named_scoped_session(SCOPED_SESSION_KEY)
    install(model.LabModel.metadata, session.bind, repository)

