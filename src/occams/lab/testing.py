import plone.testing

from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting
from zope.configuration import xmlconfig
from datetime import date

from occams.lab import Session
from occams.lab import model

from avrc.aeh.testing import OCCAMS_CLINICAL_FIXTURE, OCCAMS_CLINICAL_MODEL_FIXTURE


class OccamsLabLayer(PloneSandboxLayer):

    defaultBases = (OCCAMS_CLINICAL_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import occams.lab as package
        xmlconfig.file('configure.zcml', package, context=configurationContext)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'occams.lab:default')

        session = Session
        site = model.Site(
            name="location",
            title="",
            zid=56483
            )

        dummy_patient = model.Patient(
            our="XXX-XXX",
             zid=234567890,
             site=site
             )
        session.add(dummy_patient)
        session.flush()
        self['dummy_patient'] = dummy_patient

        dummy_study = model.Study(
            name="Dummy Study",
             title=u"Dummy Study",
             short_title=u"DS",
             code=u"2",
             consent_date=date.today(),
             zid=2222
             )
        session.add(dummy_study)
        session.flush()
        self['dummy_study'] = dummy_study

        dummy_cycle = model.Cycle(
            name="Dummy Cycle",
             title=u"Dummy Cycle",
             week=u"0",
             study=dummy_study,
             zid=3333
             )
        session.add(dummy_cycle)
        session.flush()
        self['dummy_cycle'] = dummy_cycle

        dummy_visit = model.Visit(
             patient = dummy_patient,
             cycles = [dummy_cycle, ],
             visit_date = date(2000,1,1) ,
             zid=4444
             )

        session.add(dummy_visit)
        session.flush()
        self['dummy_visit'] = dummy_visit

class OccamsLabModelLayer(plone.testing.Layer):
    """
    DataBase application layer for tests.
    """
    defaultBases = (OCCAMS_CLINICAL_MODEL_FIXTURE,)

    def setUp(self):
        # clinical.ClinicalModel.metadata.create_all(self[u'session'].bind, checkfirst=True)
        model.LabModel.metadata.create_all(self[u'session'].bind, checkfirst=True)

    def testSetUp(self):
        """
        Set up the dummy items that will be used in all of the tests
        """
        session = self['session']
        dummy_site = model.Site(
            name="location",
            title="",
            zid=56483
            )

        dummy_patient = model.Patient(
            our="XXX-XXX",
             zid=234567890,
             site=dummy_site
             )
        session.add(dummy_patient)
        session.flush()
        self['dummy_patient'] = dummy_patient

        dummy_study = model.Study(
            name="Dummy Study",
             title=u"Dummy Study",
             short_title=u"DS",
             code=u"000",
             consent_date=date.today(),
             zid=345678901
             )
        session.add(dummy_study)
        session.flush()
        self['dummy_study'] = dummy_study

        dummy_cycle = model.Cycle(
            name="Dummy Cycle",
             title=u"Dummy Cycle",
             week=u"0",
             study=dummy_study,
             zid=456789012
             )
        session.add(dummy_cycle)
        session.flush()
        self['dummy_cycle'] = dummy_cycle


OCCAMS_LAB_MODEL_FIXTURE = OccamsLabModelLayer()

OCCAMS_LAB_FIXTURE= OccamsLabLayer()

OCCAMS_LAB_INTEGRATION_TESTING = IntegrationTesting(
    bases=(OCCAMS_LAB_FIXTURE,),
    name="OccamsLab:Integration"
    )

OCCAMS_LAB_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(OCCAMS_LAB_FIXTURE,),
    name='OccamsLab:Functional'
    )
