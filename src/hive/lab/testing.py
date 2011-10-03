from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting

from zope.configuration import xmlconfig

class ClinicalLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)
    
    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import hive.lab
        xmlconfig.file('configure.zcml', hive.lab, context=configurationContext)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'hive.lab:default')

CLINICAL_FIXTURE = ClinicalLayer()
CLINICAL_INTEGRATION_TESTING = IntegrationTesting(bases=(CLINICAL_FIXTURE,), name="hive:Integration")
