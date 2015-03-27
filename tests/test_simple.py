from trussme import truss
from trussme import member
import unittest

class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.T = truss.Truss(12)

    def testTrussInit(self):
        self.assertEqual(self.T.n, 12)

    def testMemberError(self):
        m = member.Member()
        m.set_shape("bar")

if __name__ == "__main__":
    unittest.main()
