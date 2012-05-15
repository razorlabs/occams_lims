from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
import plone.testing
from z3c.saconfig.utility import EngineFactory
from z3c.saconfig import named_scoped_session
from zope.configuration import xmlconfig
from zope.component import provideUtility
from plone.app.testing import TEST_USER_ID
from plone.app.testing import SITE_OWNER_NAME

from hive.lab import SCOPED_SESSION_KEY
from hive.lab.model import Model
from occams.datastore.model.session import DataStoreSession
from occams.datastore.model.metadata import User
from hive.lab import model
from occams.form.saconfig import EventAwareScopedSession
from occams.datastore.testing import OCCAMS_DATASTORE_FIXTURE


try:
    # Prefer the future naming convention 
    from avrc.aeh.testing import OCCAMS_CLINICAL_FIXTURE
except ImportError:
    # Still not up-to-date, use the original
    from avrc.aeh.testing import CLINICAL_FIXTURE as OCCAMS_CLINICAL_FIXTURE


class OccamsLabModelLayer(plone.testing.Layer):
    """
    DataBase application layer for tests.
    """
    defaultBases = (OCCAMS_DATASTORE_FIXTURE,)

#### I think these are set up by our base
    # def setUp(self):
    #     """
    #     Creates the database structures.
    #     """
    #     engine = create_engine('sqlite://', echo=True)
    #     Model.metadata.drop_all(engine, checkfirst=True)
    #     Model.metadata.create_all(engine, checkfirst=False)
    #     self['session'] = scoped_session(sessionmaker(
    #         bind=engine,
    #         class_=DataStoreSession,
    #         user=lambda: TEST_USER_ID
    #         ))

    # def tearDown(self):
    #     """
    #     Destroys the database structures.
    #     """
    #     self['session'].close()
    #     del self['session']

    # def testSetUp(self):
    #     """
    #     """
    #     session = self['session']
    #     user = User(key=TEST_USER_ID)
    #     session.add(user)
    #     session.flush()
    #     self['user'] = user

    # def testTearDown(self):
    #     """
    #     Cancels the transaction after each test case method.
    #     """
    #     self['session'].rollback()


OCCAMS_LAB_MODEL_FIXTURE = OccamsLabModelLayer()


class OccamsLabLayer(PloneSandboxLayer):

    defaultBases = (OCCAMS_CLINICAL_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import hive.lab as package
        xmlconfig.file('configure.zcml', package, context=configurationContext)
        ## Set up by our base? 
        
        # engineUtility = EngineFactory('sqlite://', echo=True)
        # Model.metadata.drop_all(engineUtility(), checkfirst=True)
        # Model.metadata.create_all(engineUtility(), checkfirst=False)

        # provideUtility(engineUtility, name='occams.FiaEngine')
        # sessionUtility = EventAwareScopedSession(engine='occams.FiaEngine')

        # provideUtility(sessionUtility, name=SCOPED_SESSION_KEY)
        # session = named_scoped_session(SCOPED_SESSION_KEY)

        # user = User(key=TEST_USER_ID)
        # user2 = User(key=SITE_OWNER_NAME)
        # session.add(user)
        # session.add(user2)
        # session.flush()

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'hive.lab:default')


OCCAMS_LAB_FIXTURE= OccamsLabLayer()

OCCAMS_LAB_INTEGRATION_TESTING = IntegrationTesting(
    bases=(OCCAMS_LAB_FIXTURE,),
    name="OccamsLab:Integration"
    )

OCCAMS_LAB_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(OCCAMS_LAB_FIXTURE,),
    name='OccamsLab:Functional'
    )
