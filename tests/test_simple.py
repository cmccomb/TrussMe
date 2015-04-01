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
            numpy.array([0.0, 1.0, 0.0]), d=2)
        self.T.add_support(
            numpy.array([2.0, 0.0, 0.0]), d=2)

        self.T.joints[2].roller(d=2)

        self.T.joints[1].loads[1][0] = -10000.0

        self.T.add_member(0, 1)
        self.T.add_member(1, 2)
        self.T.add_member(2, 0)

        self.T.set_goal(min_fos_total=1.0, min_fos_buckling=1.0, max_mass=5.0)

        self.T.print_report()

if __name__ == "__main__":
    unittest.main()
