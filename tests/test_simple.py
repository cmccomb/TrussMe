from trussme import truss
import unittest

class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.T = truss.Truss(12)

    def testTrussInit(self):
        self.assertEqual(self.T.n, 12)

if __name__ == "__main__":
    unittest.main()
