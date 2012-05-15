import unittest2 as unittest
from zope.interface.verify import verifyClass
from hive.lab import model
from hive.lab import interfaces
from hive.lab.testing import OCCAMS_LAB_MODEL_FIXTURE
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import FlushError

class ModelTestCase(unittest.TestCase):
    """
    Verifies entity model
    """

    layer = OCCAMS_LAB_MODEL_FIXTURE

    def testFails(self):
        self.assertTrue(False)