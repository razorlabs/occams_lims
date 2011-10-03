import unittest2 as unittest
from hive.lab.testing import CLINICAL_INTEGRATION_TESTING

class TestSetup(unittest.TestCase):
    
    layer = CLINICAL_INTEGRATION_TESTING

    def test_should_fail(self):
        self.fail()