import numpy
import unittest
import os
import filecmp
from trussme import truss

TEST_TRUSS_FILENAME = os.path.join(os.path.dirname(__file__), 'example.trs')


class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        # Build truss from scratch
        self.T1 = truss.Truss()
        self.T1.add_support(numpy.array([0.0, 0.0, 0.0]), d=2)
        self.T1.add_joint(numpy.array([1.0, 0.0, 0.0]), d=2)
        self.T1.add_joint(numpy.array([2.0, 0.0, 0.0]), d=2)
        self.T1.add_joint(numpy.array([3.0, 0.0, 0.0]), d=2)
        self.T1.add_joint(numpy.array([4.0, 0.0, 0.0]), d=2)
        self.T1.add_support(numpy.array([5.0, 0.0, 0.0]), d=2)

        self.T1.add_joint(numpy.array([0.5, 1.0, 0.0]), d=2)
        self.T1.add_joint(numpy.array([1.5, 1.0, 0.0]), d=2)
        self.T1.add_joint(numpy.array([2.5, 1.0, 0.0]), d=2)
        self.T1.add_joint(numpy.array([3.5, 1.0, 0.0]), d=2)
        self.T1.add_joint(numpy.array([4.5, 1.0, 0.0]), d=2)

        self.T1.joints[7].loads[1] = -20000
        self.T1.joints[8].loads[1] = -20000
        self.T1.joints[9].loads[1] = -20000

        self.T1.add_member(0, 1)
        self.T1.add_member(1, 2)
        self.T1.add_member(2, 3)
        self.T1.add_member(3, 4)
        self.T1.add_member(4, 5)

        self.T1.add_member(6, 7)
        self.T1.add_member(7, 8)
        self.T1.add_member(8, 9)
        self.T1.add_member(9, 10)

        self.T1.add_member(0, 6)
        self.T1.add_member(6, 1)
        self.T1.add_member(1, 7)
        self.T1.add_member(7, 2)
        self.T1.add_member(2, 8)
        self.T1.add_member(8, 3)
        self.T1.add_member(3, 9)
        self.T1.add_member(9, 4)
        self.T1.add_member(4, 10)
        self.T1.add_member(10, 5)

        self.T1.set_goal(min_fos_buckling=1.5,
                         min_fos_yielding=1.5,
                         max_mass=5.0,
                         max_deflection=6e-3)

        # Build truss from file
        self.T2 = truss.Truss(TEST_TRUSS_FILENAME)
        self.T2.set_goal(min_fos_buckling=1.5,
                         min_fos_yielding=1.5,
                         max_mass=5.0,
                         max_deflection=6e-3)

    def test_save_and_compare(self):
        # Save reports
        self.T1.report(
            os.path.join(os.path.dirname(__file__), 'report_1.txt'))
        self.T2.report(
            os.path.join(os.path.dirname(__file__), 'report_2.txt'))

        # Test for sameness
        file_are_the_same = filecmp.cmp(
            os.path.join(os.path.dirname(__file__), 'report_1.txt'),
            os.path.join(os.path.dirname(__file__), 'report_2.txt'))
        self.assertTrue(file_are_the_same)

    def test_save_and_rebuild(self):
        # Save
        self.T2.report(
            os.path.join(os.path.dirname(__file__), 'report_2.txt'))
        self.T2.save("asdf.trs")

        # Rebuild
        self.T3 = truss.Truss("asdf.trs")
        self.T3.set_goal(min_fos_buckling=1.5,
                         min_fos_yielding=1.5,
                         max_mass=5.0,
                         max_deflection=6e-3)
        self.T3.report("report_3.txt")

        # Test for sameness
        file_are_the_same = filecmp.cmp(
            os.path.join(os.path.dirname(__file__), 'report_3.txt'),
            os.path.join(os.path.dirname(__file__), 'report_2.txt'))
        self.assertTrue(file_are_the_same)

if __name__ == "__main__":
    unittest.main()
