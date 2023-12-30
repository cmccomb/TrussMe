import filecmp
import os
import unittest

import trussme
import trussme.visualize

TEST_TRUSS_FILENAME = os.path.join(os.path.dirname(__file__), "example.trs")


class TestSequenceFunctions(unittest.TestCase):
    def test_build_methods(self):
        goals = trussme.Goals(
            minimum_fos_buckling=1.5,
            minimum_fos_yielding=1.5,
            maximum_mass=5.0,
            maximum_deflection=6e-3,
        )

        # Build truss from scratch
        t1 = trussme.Truss()
        t1.add_pinned_joint([0.0, 0.0, 0.0])
        t1.add_free_joint([1.0, 0.0, 0.0])
        t1.add_free_joint([2.0, 0.0, 0.0])
        t1.add_free_joint([3.0, 0.0, 0.0])
        t1.add_free_joint([4.0, 0.0, 0.0])
        t1.add_pinned_joint([5.0, 0.0, 0.0])

        t1.add_free_joint([0.5, 1.0, 0.0])
        t1.add_free_joint([1.5, 1.0, 0.0])
        t1.add_free_joint([2.5, 1.0, 0.0])
        t1.add_free_joint([3.5, 1.0, 0.0])
        t1.add_free_joint([4.5, 1.0, 0.0])

        t1.add_out_of_plane_support("z")

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

        # Build truss from file
        t2 = trussme.read_trs(TEST_TRUSS_FILENAME)

        # Save reports
        t1.report_to_md(os.path.join(os.path.dirname(__file__), "report_1.md"), goals)
        t2.report_to_md(os.path.join(os.path.dirname(__file__), "report_2.md"), goals)

        # Test for sameness
        file_are_the_same = filecmp.cmp(
            os.path.join(os.path.dirname(__file__), "report_1.md"),
            os.path.join(os.path.dirname(__file__), "report_2.md"),
        )
        self.assertTrue(file_are_the_same)

        # Clean up
        os.remove(os.path.join(os.path.dirname(__file__), "report_1.md"))
        os.remove(os.path.join(os.path.dirname(__file__), "report_2.md"))

    def test_save_to_trs_and_rebuild(self):
        goals = trussme.Goals(
            minimum_fos_buckling=1.5,
            minimum_fos_yielding=1.5,
            maximum_mass=5.0,
            maximum_deflection=6e-3,
        )

        # Build truss from file
        t2 = trussme.read_trs(TEST_TRUSS_FILENAME)

        # Save
        t2.report_to_md(os.path.join(os.path.dirname(__file__), "report_2.md"), goals)
        t2.to_trs(os.path.join(os.path.dirname(__file__), "asdf.trs"))

        # Rebuild
        t3 = trussme.read_trs(os.path.join(os.path.dirname(__file__), "asdf.trs"))
        t3.report_to_md(os.path.join(os.path.dirname(__file__), "report_3.md"), goals)

        # Test for sameness
        file_are_the_same = filecmp.cmp(
            os.path.join(os.path.dirname(__file__), "report_3.md"),
            os.path.join(os.path.dirname(__file__), "report_2.md"),
        )
        self.assertTrue(file_are_the_same)

    def test_save_to_json_and_rebuild(self):
        goals = trussme.Goals(
            minimum_fos_buckling=1.5,
            minimum_fos_yielding=1.5,
            maximum_mass=5.0,
            maximum_deflection=6e-3,
        )

        # Build truss from file
        t2 = trussme.read_trs(TEST_TRUSS_FILENAME)

        # Save
        t2.report_to_md(os.path.join(os.path.dirname(__file__), "report_4.md"), goals)
        t2.to_json(os.path.join(os.path.dirname(__file__), "asdf.json"))

        # Rebuild
        t3 = trussme.read_json(os.path.join(os.path.dirname(__file__), "asdf.json"))

        t3.report_to_md(os.path.join(os.path.dirname(__file__), "report_5.md"), goals)

        # Test for sameness
        file_are_the_same = filecmp.cmp(
            os.path.join(os.path.dirname(__file__), "report_5.md"),
            os.path.join(os.path.dirname(__file__), "report_4.md"),
        )
        self.assertTrue(file_are_the_same)
