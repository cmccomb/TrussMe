import numpy
import unittest
import os
import filecmp
import trussme

TEST_TRUSS_FILENAME = os.path.join(os.path.dirname(__file__), 'example.trs')


class TestSequenceFunctions(unittest.TestCase):

    def test_build_methods(self):
        # Build truss from scratch
        t1 = trussme.Truss()
        t1.add_pinned_support([0.0, 0.0, 0.0])
        t1.add_joint([1.0, 0.0, 0.0], d=2)
        t1.add_joint([2.0, 0.0, 0.0], d=2)
        t1.add_joint([3.0, 0.0, 0.0], d=2)
        t1.add_joint([4.0, 0.0, 0.0], d=2)
        t1.add_pinned_support([5.0, 0.0, 0.0])

        t1.add_joint([0.5, 1.0, 0.0], d=2)
        t1.add_joint([1.5, 1.0, 0.0], d=2)
        t1.add_joint([2.5, 1.0, 0.0], d=2)
        t1.add_joint([3.5, 1.0, 0.0], d=2)
        t1.add_joint([4.5, 1.0, 0.0], d=2)

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

        t1.minimum_fos_buckling = 1.5
        t1.min_fos_yielding = 1.5
        t1.max_mass = 5.0
        t1.maximum_deflection = 6e-3

        # Build truss from file
        t2 = trussme.read_trs(TEST_TRUSS_FILENAME)
        t2.minimum_fos_buckling = 1.5
        t2.min_fos_yielding = 1.5
        t2.max_mass = 5.0
        t2.maximum_deflection = 6e-3

        # Save reports
        t1.save_report(os.path.join(os.path.dirname(__file__), 'report_1.md'))
        t2.save_report(os.path.join(os.path.dirname(__file__), 'report_2.md'))

        # Test for sameness
        file_are_the_same = filecmp.cmp(
            os.path.join(os.path.dirname(__file__), 'report_1.md'),
            os.path.join(os.path.dirname(__file__), 'report_2.md'))
        self.assertTrue(file_are_the_same)

        # Clean up
        os.remove(os.path.join(os.path.dirname(__file__), 'report_1.md'))
        os.remove(os.path.join(os.path.dirname(__file__), 'report_2.md'))

    def test_save_and_rebuild(self):
        # Build truss from file
        t2 = trussme.read_trs(TEST_TRUSS_FILENAME)
        t2.minimum_fos_buckling = 1.5
        t2.min_fos_yielding = 1.5
        t2.max_mass = 5.0
        t2.maximum_deflection = 6e-3

        # Save
        t2.save_report(os.path.join(os.path.dirname(__file__), 'report_2.md'))
        t2.save_truss(os.path.join(os.path.dirname(__file__), 'asdf.trs'))

        # Rebuild
        t3 = trussme.read_trs(os.path.join(os.path.dirname(__file__), 'asdf.trs'))
        t3.minimum_fos_buckling = 1.5
        t3.min_fos_yielding = 1.5
        t3.max_mass = 5.0
        t3.maximum_deflection = 6e-3

        t3.save_report(os.path.join(os.path.dirname(__file__), 'report_3.md'))

        with open(os.path.join(os.path.dirname(__file__), 'report_3.md')) as f:
            print(f.read())
        with open(os.path.join(os.path.dirname(__file__), 'report_2.md')) as f:
            print(f.read())

        # Test for sameness
        file_are_the_same = filecmp.cmp(
            os.path.join(os.path.dirname(__file__), 'report_3.md'),
            os.path.join(os.path.dirname(__file__), 'report_2.md'))
        self.assertTrue(file_are_the_same)


if __name__ == "__main__":
    unittest.main()
