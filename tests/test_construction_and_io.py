import doctest
import filecmp
import os
import unittest

import trussme

TEST_TRUSS_FILENAME = os.path.join(os.path.dirname(__file__), "example.trs")


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(trussme))
    tests.addTests(doctest.DocTestSuite(trussme.truss))
    tests.addTests(doctest.DocTestSuite(trussme.components))
    tests.addTests(doctest.DocTestSuite(trussme.report))
    return tests


class TestSequenceFunctions(unittest.TestCase):
    def test_demo_report(self):
        # Build truss from file
        truss_from_file = trussme.read_trs(TEST_TRUSS_FILENAME)

        trussme.report_to_md("asdf.md", truss_from_file, trussme.Goals())

    def test_build_methods(self):
        goals = trussme.Goals(
            minimum_fos_buckling=1.5,
            minimum_fos_yielding=1.5,
            maximum_mass=5.0,
            maximum_deflection=6e-3,
        )

        # Build truss from scratch
        truss_from_commands = trussme.Truss()
        truss_from_commands.add_pinned_joint([0.0, 0.0, 0.0])
        truss_from_commands.add_free_joint([1.0, 0.0, 0.0])
        truss_from_commands.add_free_joint([2.0, 0.0, 0.0])
        truss_from_commands.add_free_joint([3.0, 0.0, 0.0])
        truss_from_commands.add_free_joint([4.0, 0.0, 0.0])
        truss_from_commands.add_pinned_joint([5.0, 0.0, 0.0])

        truss_from_commands.add_free_joint([0.5, 1.0, 0.0])
        truss_from_commands.add_free_joint([1.5, 1.0, 0.0])
        truss_from_commands.add_free_joint([2.5, 1.0, 0.0])
        truss_from_commands.add_free_joint([3.5, 1.0, 0.0])
        truss_from_commands.add_free_joint([4.5, 1.0, 0.0])

        truss_from_commands.add_out_of_plane_support("z")

        truss_from_commands.joints[7].loads[1] = -20000
        truss_from_commands.joints[8].loads[1] = -20000
        truss_from_commands.joints[9].loads[1] = -20000

        truss_from_commands.add_member(0, 1)
        truss_from_commands.add_member(1, 2)
        truss_from_commands.add_member(2, 3)
        truss_from_commands.add_member(3, 4)
        truss_from_commands.add_member(4, 5)

        truss_from_commands.add_member(6, 7)
        truss_from_commands.add_member(7, 8)
        truss_from_commands.add_member(8, 9)
        truss_from_commands.add_member(9, 10)

        truss_from_commands.add_member(0, 6)
        truss_from_commands.add_member(6, 1)
        truss_from_commands.add_member(1, 7)
        truss_from_commands.add_member(7, 2)
        truss_from_commands.add_member(2, 8)
        truss_from_commands.add_member(8, 3)
        truss_from_commands.add_member(3, 9)
        truss_from_commands.add_member(9, 4)
        truss_from_commands.add_member(4, 10)
        truss_from_commands.add_member(10, 5)

        # Build truss from file
        truss_from_file = trussme.read_trs(TEST_TRUSS_FILENAME)

        self.assertEqual(
            trussme.report_to_str(truss_from_file, goals),
            trussme.report_to_str(truss_from_commands, goals),
        )

    def test_save_to_trs_and_rebuild(self):
        goals = trussme.Goals(
            minimum_fos_buckling=1.5,
            minimum_fos_yielding=1.5,
            maximum_mass=5.0,
            maximum_deflection=6e-3,
        )

        # Build truss from file
        truss_from_file = trussme.read_trs(TEST_TRUSS_FILENAME)

        # Save the truss
        truss_from_file.to_trs(os.path.join(os.path.dirname(__file__), "asdf.trs"))

        # Rebuild
        truss_rebuilt_from_file = trussme.read_trs(
            os.path.join(os.path.dirname(__file__), "asdf.trs")
        )

        self.assertEqual(
            trussme.report_to_str(truss_from_file, goals),
            trussme.report_to_str(truss_rebuilt_from_file, goals),
        )

        # Cleanup
        os.remove(os.path.join(os.path.dirname(__file__), "asdf.trs"))

    def test_save_to_json_and_rebuild(self):
        goals = trussme.Goals(
            minimum_fos_buckling=1.5,
            minimum_fos_yielding=1.5,
            maximum_mass=5.0,
            maximum_deflection=6e-3,
        )

        # Build truss from file
        truss_from_file = trussme.read_trs(TEST_TRUSS_FILENAME)

        # Save the truss
        truss_from_file.to_json(os.path.join(os.path.dirname(__file__), "asdf.json"))

        # Rebuild
        truss_rebuilt_from_file = trussme.read_json(
            os.path.join(os.path.dirname(__file__), "asdf.json")
        )

        self.assertEqual(
            trussme.report_to_str(truss_from_file, goals),
            trussme.report_to_str(truss_rebuilt_from_file, goals),
        )

        # Cleanup
        os.remove(os.path.join(os.path.dirname(__file__), "asdf.json"))
