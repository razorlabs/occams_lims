from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting
from avrc.aeh.testing import CLINICAL_FIXTURE

from zope.configuration import xmlconfig

class LabLayer(PloneSandboxLayer):

    defaultBases = (CLINICAL_FIXTURE,)
    
    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import hive.lab
        xmlconfig.file('configure.zcml', hive.lab, context=configurationContext)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'hive.lab:default')

LAB_FIXTURE = LabLayer()
LAB_INTEGRATION_TESTING = IntegrationTesting(bases=(LAB_FIXTURE,), name="hive:Integration")
