import numpy
import unittest
import os
import filecmp
from trussme import truss

TEST_TRUSS_FILENAME = os.path.join(os.path.dirname(__file__), 'example.trs')


class TestSequenceFunctions(unittest.TestCase):

    def test_build_methods(self):
        # Build truss from scratch
        t1 = truss.Truss()
        t1.add_support(numpy.array([0.0, 0.0, 0.0]), d=2)
        t1.add_joint(numpy.array([1.0, 0.0, 0.0]), d=2)
        t1.add_joint(numpy.array([2.0, 0.0, 0.0]), d=2)
        t1.add_joint(numpy.array([3.0, 0.0, 0.0]), d=2)
        t1.add_joint(numpy.array([4.0, 0.0, 0.0]), d=2)
        t1.add_support(numpy.array([5.0, 0.0, 0.0]), d=2)

        t1.add_joint(numpy.array([0.5, 1.0, 0.0]), d=2)
        t1.add_joint(numpy.array([1.5, 1.0, 0.0]), d=2)
        t1.add_joint(numpy.array([2.5, 1.0, 0.0]), d=2)
        t1.add_joint(numpy.array([3.5, 1.0, 0.0]), d=2)
        t1.add_joint(numpy.array([4.5, 1.0, 0.0]), d=2)

        t1.joints[7].loads[1] = -20000
        t1.joints[8].loads[1] = -20000
        t1.joints[9].loads[1] = -20000

        t1.add_member(0, 1)
        t1.add_member(1, 2)
        t1.add_member(2, 3)
        t1.add_member(3, 4)
        t1.add_member(4, 5)

        t1.add_member(6, 7)
        t1.add_member(7, 8)
        t1.add_member(8, 9)
        t1.add_member(9, 10)

        t1.add_member(0, 6)
        t1.add_member(6, 1)
        t1.add_member(1, 7)
        t1.add_member(7, 2)
        t1.add_member(2, 8)
        t1.add_member(8, 3)
        t1.add_member(3, 9)
        t1.add_member(9, 4)
        t1.add_member(4, 10)
        t1.add_member(10, 5)

        t1.set_goal(min_fos_buckling=1.5,
                    min_fos_yielding=1.5,
                    max_mass=5.0,
                    max_deflection=6e-3)

        # Build truss from file
        t2 = truss.Truss(TEST_TRUSS_FILENAME)
        t2.set_goal(min_fos_buckling=1.5,
                    min_fos_yielding=1.5,
                    max_mass=5.0,
                    max_deflection=6e-3)

        # Save reports
        t1.save_report(os.path.join(os.path.dirname(__file__), 'report_1.txt'))
        t2.save_report(os.path.join(os.path.dirname(__file__), 'report_2.txt'))

        # Test for sameness
        file_are_the_same = filecmp.cmp(
            os.path.join(os.path.dirname(__file__), 'report_1.txt'),
            os.path.join(os.path.dirname(__file__), 'report_2.txt'))
        self.assertTrue(file_are_the_same)

        # Clean up
        os.remove(os.path.join(os.path.dirname(__file__), 'report_1.txt'))
        os.remove(os.path.join(os.path.dirname(__file__), 'report_2.txt'))

    def test_save_and_rebuild(self):
        # Build truss from file
        t2 = truss.Truss(TEST_TRUSS_FILENAME)
        t2.set_goal(min_fos_buckling=1.5,
                    min_fos_yielding=1.5,
                    max_mass=5.0,
                    max_deflection=6e-3)

        # Save
        t2.save_report(os.path.join(os.path.dirname(__file__), 'report_2.txt'))
        t2.save_truss(os.path.join(os.path.dirname(__file__), 'asdf.trs'))

        # Rebuild
        t3 = truss.Truss(os.path.join(os.path.dirname(__file__), 'asdf.trs'))
        t3.set_goal(min_fos_buckling=1.5,
                    min_fos_yielding=1.5,
                    max_mass=5.0,
                    max_deflection=6e-3)
        t3.save_report(os.path.join(os.path.dirname(__file__), 'report_3.txt'))

        # Test for sameness
        file_are_the_same = filecmp.cmp(
            os.path.join(os.path.dirname(__file__), 'report_3.txt'),
            os.path.join(os.path.dirname(__file__), 'report_2.txt'))
        self.assertTrue(file_are_the_same)

        # Clean up
        os.remove(os.path.join(os.path.dirname(__file__), 'report_2.txt'))
        os.remove(os.path.join(os.path.dirname(__file__), 'report_3.txt'))
        os.remove(os.path.join(os.path.dirname(__file__), 'asdf.trs'))


if __name__ == "__main__":
    unittest.main()
