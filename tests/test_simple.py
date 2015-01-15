from trussme import truss
import unittest

class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.n = 1

    def testTheThing(self):
        self.assertEqual(self.n, 1)

if __name__ == "__main__":
    unittest.main()
