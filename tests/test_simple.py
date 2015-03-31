import numpy
from trussme import truss
from trussme import old_truss
import unittest


class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.T = truss.Truss()

    def test_truss(self):
        self.T.add_support(numpy.array([-5.0, 0.0, 0.0]), d=2)
        self.T.add_joint(  numpy.array([-2.0, 0.0, 0.0]), d=2)
        self.T.add_support(numpy.array([ 1.0, 0.0, 0.0]), d=2)
        self.T.joints[2].roller()
        self.T.add_joint(  numpy.array([ 3.0, 0.0, 0.0]), d=2)
        self.T.add_support(numpy.array([ 5.0, 0.0, 0.0]), d=2)
        self.T.add_support(numpy.array([ 1.0, 1.0, 0.0]), d=2)

        self.T.add_member(0, 1)
        self.T.add_member(1, 2)
        self.T.add_member(2, 3)
        self.T.add_member(3, 4)
        self.T.add_member(0, 5)
        self.T.add_member(1, 5)
        self.T.add_member(2, 5)
        self.T.add_member(3, 5)
        self.T.add_member(4, 5)

        self.T.print_report()

if __name__ == "__main__":
    unittest.main()
