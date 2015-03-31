import numpy
from trussme import truss
import unittest


class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.T = truss.Truss()

    def test_truss(self):
        self.T.add_support(
            numpy.array([-2.0, 0.0, 0.0]), d=2)
        self.T.add_joint(
            numpy.array([0.0, 2.0, 0.0]), d=2)
        self.T.add_support(
            numpy.array([2.0, 0.0, 0.0]), d=2)

        self.T.joints[2].roller(d=2)

        self.T.joints[1].loads[1][0] = -40000.0

        self.T.add_member(0, 1)
        self.T.add_member(1, 2)
        self.T.add_member(2, 0)

        self.T.calc_fos()

        self.T.print_report()

if __name__ == "__main__":
    unittest.main()
