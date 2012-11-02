import unittest2 as unittest
from zope.interface.verify import verifyClass
from occams.lab import model
from occams.lab import interfaces
from occams.lab.testing import OCCAMS_LAB_MODEL_FIXTURE
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import FlushError

import datetime

t1 = datetime.date(2012, 1, 1)
t2 = datetime.date(2012, 2, 1)
t3 = datetime.date(2012, 3, 1)
t4 = datetime.date(2012, 4, 1)
t5 = datetime.date(2012, 5, 1)
t6 = datetime.date(2012, 6, 1)
t7 = datetime.date(2012, 7, 1)
t8 = datetime.date(2012, 8, 1)
t9 = datetime.date(2012, 9, 1)
t10 = datetime.date(2012, 10, 1)
t11 = datetime.date(2012, 11, 1)
t12 = datetime.date(2012, 12, 1)

class SpecimenStateModelTestCase(unittest.TestCase):
    """
    Verifies entity model
    """

    layer = OCCAMS_LAB_MODEL_FIXTURE

    def testImplementation(self):
        self.assertTrue(verifyClass(interfaces.IOccamsVocabulary, model.SpecimenState))

    def testaddingSpecimenState(self):
        session = self.layer['session']
        specimenstate = model.SpecimenState(name="pending", title=u"Pending")
        session.add(specimenstate)
        session.flush()
        count = session.query(model.SpecimenState).count()
        self.assertEquals(1, count)

    def testNameUnique(self):
        session = self.layer['session']
        s1 = model.SpecimenState(name="pending", title=u"Pending")
        session.add(s1)
        session.flush()
        s2 =  model.SpecimenState(name="pending", title=u"Some State")
        with self.assertRaises(IntegrityError):
            session.add(s2)
            session.flush()

class AliquotStateModelTestCase(unittest.TestCase):
    """
    Verifies entity model
    """

    layer = OCCAMS_LAB_MODEL_FIXTURE

    def testImplementation(self):
        self.assertTrue(verifyClass(interfaces.IOccamsVocabulary, model.AliquotState))

    def testaddingAliquotState(self):
        session = self.layer['session']
        aliquotstate = model.AliquotState(name="pending", title=u"Pending")
        session.add(aliquotstate)
        session.flush()
        count = session.query(model.AliquotState).count()
        self.assertEquals(1, count)

    def testNameUnique(self):
        session = self.layer['session']
        s1 = model.AliquotState(name="pending", title=u"Pending")
        session.add(s1)
        session.flush()
        s2 =  model.AliquotState(name="pending", title=u"Some State")
        with self.assertRaises(IntegrityError):
            session.add(s2)
            session.flush()

class LocationModelTestCase(unittest.TestCase):
    """
    Verifies entity model
    """

    layer = OCCAMS_LAB_MODEL_FIXTURE

    def testImplementation(self):
        self.assertTrue(verifyClass(interfaces.IOccamsVocabulary, model.Location))

    def testaddingLocation(self):
        session = self.layer['session']
        location = model.Location(name="Location", title=u"Location")
        session.add(location)
        session.flush()
        count = session.query(model.Location).count()
        self.assertEquals(1, count)

    def testNameUnique(self):
        session = self.layer['session']
        s1 = model.Location(name="location", title=u"Location")
        session.add(s1)
        session.flush()
        s2 =  model.Location(name="location", title=u"Some Other Location")
        with self.assertRaises(IntegrityError):
            session.add(s2)
            session.flush()

class SpecialInstructionTestCase(unittest.TestCase):
    """
    Verifies entity model
    """
    layer = OCCAMS_LAB_MODEL_FIXTURE

    def testImplementation(self):
        self.assertTrue(verifyClass(interfaces.IOccamsVocabulary, model.SpecialInstruction))

    def testaddingSpecialInstruction(self):
        session = self.layer['session']
        sp_instruct = model.SpecialInstruction(name="Special Instruction", title=u"special Instruction")
        session.add(sp_instruct)
        session.flush()
        count = session.query(model.SpecialInstruction).count()
        self.assertEquals(1, count)

    def testNameUnique(self):
        session = self.layer['session']
        s1 = model.SpecialInstruction(name="special", title=u"Special Instruction")
        session.add(s1)
        session.flush()
        s2 =  model.SpecialInstruction(name="special", title=u"Not So Special Instruction")
        with self.assertRaises(IntegrityError):
            session.add(s2)
            session.flush()

class SpecimenTypeTestCase(unittest.TestCase):
    """
    Verifies entity model
    """

    layer = OCCAMS_LAB_MODEL_FIXTURE

    def testImplementation(self):
        self.assertTrue(verifyClass(interfaces.ISpecimenType, model.SpecimenType))

    def testaddingSpecimenType(self):
        session = self.layer['session']
        specimen_type = model.SpecimenType(
            name="Specimen Type 1",
             title=u"Some Specimen Type",
             tube_type=u"A Tube that will hold it",
             )
        session.add(specimen_type)
        session.flush()
        count = session.query(model.SpecimenType).count()
        self.assertEquals(1, count)

    def testLocation(self):
        self.fail()

    def testLocationNullOnDelete(self):
        self.fail()

    def testNameUnique(self):
        session = self.layer['session']
        s1 = model.SpecimenType(
            name="Specimen Type 1",
             title=u"Some Specimen Type",
             tube_type=u"A Tube that will hold it",
             )
        session.add(s1)
        session.flush()
        s2 = model.SpecimenType(
            name="Specimen Type 1",
             title=u"A different specimen type",
             tube_type=u"A Tube that will hold it",
             )
        session.add(s2)
        with self.assertRaises(IntegrityError):
            session.add(s2)
            session.flush()

    def testAliquotTypes(self):
        ## The Types are?? maybe dictionaryish? think on this
        #also, if you're confused, its in the AliquotType definition
        self.fail()


class AliquotTypeTestCase(unittest.TestCase):
    """
    Verifies entity model
    """
    layer = OCCAMS_LAB_MODEL_FIXTURE

    def setUp(self):
        session = self.layer['session']
        dummy_specimen = model.SpecimenType(
            name="Dummy Specimen Type",
             title=u"Dummy Specimen Type",
             tube_type=u"A Tube",
             )
        session.add(dummy_specimen)
        session.flush()
        self.dummy_specimen_type = dummy_specimen

    def testImplementation(self):
        self.assertTrue(verifyClass(interfaces.IAliquotType, model.AliquotType))

    def testaddingAliquotType(self):
        session = self.layer['session']
        aliquot_type = model.AliquotType(
            name="Aliquot Type 1",
             title=u"Some Aliquot Type",
             specimen_type=self.dummy_specimen_type,
             )
        session.add(aliquot_type)
        session.flush()
        count = session.query(model.AliquotType).count()
        self.assertEquals(1, count)



class SpecimenTestCase(unittest.TestCase):
    """
    Verifies entity model
    """
    layer = OCCAMS_LAB_MODEL_FIXTURE

    def setUp(self):
        session = self.layer['session']
        dummy_specimen_state = model.SpecimenState(
            name="pending",
            title=u"Pending"
            )
        session.add(dummy_specimen_state)
        session.flush()
        self.dummy_specimen_state = dummy_specimen_state
        dummy_specimen_type = model.SpecimenType(
            name="Dummy Specimen Type",
             title=u"Dummy Specimen Type",
             tube_type=u"A Tube",
             )
        session.add(dummy_specimen_type)
        session.flush()
        self.dummy_specimen_type = dummy_specimen_type

    def testImplementation(self):
        self.assertTrue(verifyClass(interfaces.ISpecimen, model.Specimen))

    def testaddingSpecimen(self):
        session = self.layer['session']
        specimen = model.Specimen(
             specimen_type=self.dummy_specimen_type,
             patient = self.layer['dummy_patient'],
             cycle = self.layer['dummy_cycle'],
             state = self.dummy_specimen_state
             )
        session.add(specimen)
        session.flush()
        count = session.query(model.Specimen).count()
        self.assertEquals(1, count)

class AliquotTestCase(unittest.TestCase):
    """
    Verifies entity model
    """

    layer = OCCAMS_LAB_MODEL_FIXTURE

    def setUp(self):
        session = self.layer['session']
        dummy_specimen_state = model.SpecimenState(
            name="pending",
            title=u"Pending"
            )
        session.add(dummy_specimen_state)
        session.flush()
        dummy_aliquot_state = model.AliquotState(
            name="pending",
            title=u"Pending"
            )
        session.add(dummy_aliquot_state)
        session.flush()
        self.dummy_aliquot_state = dummy_aliquot_state
        dummy_specimen_type = model.SpecimenType(
            name="Dummy Specimen Type",
             title=u"Dummy Specimen Type",
             tube_type=u"A Tube",
             )
        session.add(dummy_specimen_type)
        session.flush()
        dummy_aliquot_type = model.AliquotType(
            name="Aliquot Type 1",
             title=u"Some Aliquot Type",
             specimen_type=dummy_specimen_type,
             )
        session.add(dummy_aliquot_type)
        session.flush()
        self.dummy_aliquot_type = dummy_aliquot_type
        dummy_specimen = model.Specimen(
             specimen_type=dummy_specimen_type,
             patient = self.layer['dummy_patient'],
             cycle = self.layer['dummy_cycle'],
             state = dummy_specimen_state
             )
        session.add(dummy_specimen)
        session.flush()
        self.dummy_specimen = dummy_specimen


    def testImplementation(self):
        self.assertTrue(verifyClass(interfaces.IAliquot, model.Aliquot))

    def testaddingAliquot(self):
        session = self.layer['session']

        aliquot = model.Aliquot(
            specimen = self.dummy_specimen,
            aliquot_type = self.dummy_aliquot_type,
            state = self.dummy_aliquot_state
            )
        session.add(aliquot)
        session.flush()
        count = session.query(model.Aliquot).count()
        self.assertEquals(1, count)


