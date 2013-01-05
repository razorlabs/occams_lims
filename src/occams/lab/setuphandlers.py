from occams.datastore.upgrading import install
from occams.lab import model
import occams.lab.upgrades.migrate as repository
from occams.lab import Session

def importVarious(context):
    """
    GenericSetup conventional handle for importing miscellaneous steps.
    """
    if context.readDataFile('occams-lab.txt') is None:
        return
    portal = context.getSite()
    setupSQLDatabase(portal)


def setupSQLDatabase(portal):
    install(model.LabModel.metadata, Session.bind, repository)

