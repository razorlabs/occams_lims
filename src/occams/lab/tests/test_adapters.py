import unittest2 as unittest
from occams.lab import model
from occams.lab.testing import OCCAMS_LAB_INTEGRATION_TESTING

from zope.schema.interfaces import IVocabularyFactory
from zope.schema.interfaces import IVocabulary

from occams.lab import vocabularies
from z3c.saconfig import named_scoped_session
from occams.lab import SCOPED_SESSION_KEY
from zope.component import getUtility

from occams.lab import interfaces


class TestViewableSpecimen(unittest.TestCase):
    """
    Checks that the content types can be installed
    """

    layer = OCCAMS_LAB_INTEGRATION_TESTING

    def setUp(self):
        self.session = named_scoped_session(SCOPED_SESSION_KEY)
        dummy_specimen_type = model.SpecimenType(
            name="Dummy Specimen Type",
             title=u"Dummy Specimen Type",
             tube_type=u"A Tube",
             )
        self.session.add(dummy_specimen_type)
        self.session.flush()

        specimen_state= model.SpecimenState(
        name='pending-draw',
        title=unicode('pending draw')
        )
        self.session.add(specimen_state)
        self.session.flush()
        dummy_specimen = model.Specimen(
             specimen_type=dummy_specimen_type,
             patient = self.layer['dummy_patient'],
             cycle = self.layer['dummy_cycle'],
             state = specimen_state
             )
        self.session.add(dummy_specimen)
        self.session.flush()
        # setattr(self, state, dummy_specimen)

    def tearDown(self):
        self.session.rollback()

    def testViewableSpecimen(self):
       specimen = self.session.query(model.Specimen).first()
       viewablespecimen = interfaces.IViewableSpecimen(specimen)
       self.assertEquals(self.layer['dummy_patient'].our, viewablespecimen.patient_our)
       ## this breaks because the study has a detached session
       # self.assertIn(self.layer['dummy_study'].title, viewablespecimen.cycle_title)

       # self.assertEquals(self.layer['dummy_patient']
       # self.assertEquals(self.layer['dummy_patient']
       # self.assertEquals(self.layer['dummy_patient']
       # self.assertEquals(self.layer['dummy_patient']
       # self.assertEquals(self.layer['dummy_patient']
       # self.assertEquals(self.layer['dummy_patient']
       # self.assertEquals(self.layer['dummy_patient']
       # self.assertEquals(self.layer['dummy_patient']

       # self.assertEquals(self.layer['dummy_patient']





    # # patient_initials = zope.schema.TextLine(
    # #     title=_(u"Patient Initials"),
    # #     description=_(u"The source patient initials"),
    # #     readonly=True
    # #     )

    # cycle_title = zope.schema.TextLine(
    #     title=_(u"Study/Cycle"),
    #     description=_(u"The cycle for which this specimen was collected"),
    #     readonly=True
    #     )

    # visit_zid = zope.schema.Int(
    #     title=_(u"Visit Id"),
    #     description=_(u"The visit for which this specimen was collected"),
    #     readonly=True,
    #     )

    # visit_date = zope.schema.Date(
    #     title=_(u"Visit Date"),
    #     description=_(u"The visit for which this specimen was collected"),
    #     readonly=True,
    #     )

    # specimen_type_name = zope.schema.TextLine(
    #     title=_(u"Type name"),
    #     description=_(u"The Type specimen name"),
    #     readonly=True,
    #     )

    # specimen_type = zope.schema.Choice(
    #     title=_(u"Type"),
    #     description=_(u"The Type specimen"),
    #     readonly=True,
    #     vocabulary="occams.lab.specimentypevocabulary",
    #     )

    # state = zope.schema.Choice(
    #     title=_(u'State'),
    #     vocabulary="occams.lab.specimenstatevocabulary",
    #     default='pending-draw',
    #     )

    # collect_date = zope.schema.Date(
    #     title=_(u'Collect Date'),
    #     required=False,
    #     )

    # collect_time = zope.schema.Time(
    #     title=_(u'Collect Time'),
    #     required=False,
    #     )

    # location =  zope.schema.Choice(
    #     title=_(u"Location"),
    #     description=_(u"The location of the specimen"),
    #     vocabulary="occams.lab.locationvocabulary",
    #     required=False
    #     )

    # tube_type = zope.schema.TextLine(
    #     title=_(u"Tube Type"),
    #     description=_(u""),
    #     readonly=True
    #     )
    
    # tubes = zope.schema.TextLine(
    #     title=_(u"Tubes"),
    #     description=_(u"Number of Tubes drawn"),
    #     required=False
    #     )

    # notes = zope.schema.Text(
    #     title=_(u"Notes"),
    #     description=_("Notes about this specimen"),
    #     required=False
    #     )

    # study_cycle_label = zope.schema.TextLine(
    #     title=_(u"Study Cycle Label"),
    #     description=_(u"The label text for the specimen tube"),
    #     required=False
    #     )




