import unittest
import os

import scipy.optimize
import numpy

import trussme


class TestCustomStuff(unittest.TestCase):
    def test_setup(self):
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

        truss_from_commands.joints[8].loads[1] = -20000

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

        goals = trussme.Goals()

        x0, obj, con, gen, bnds = trussme.make_optimization_functions(
            truss_from_commands, goals
        )

        self.assertEqual(
            trussme.report_to_str(gen(x0), goals),
            trussme.report_to_str(truss_from_commands, goals),
        )

    def test_joint_optimization(self):
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

        truss_from_commands.joints[8].loads[1] = -20000

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

        goals = trussme.Goals()

        x0, obj, con, gen, bnds = trussme.make_optimization_functions(
            truss_from_commands, goals, joint_coordinates=True, shape_parameters=False
        )

        results = scipy.optimize.minimize(
            obj,
            x0,
            constraints=[
                scipy.optimize.NonlinearConstraint(
                    con, -numpy.inf, 0.0, keep_feasible=True
                )
            ],
            method="trust-constr",
            options={"verbose": 2, "maxiter": 50},
        )

        result_truss = gen(results.x)
        result_truss.analyze()
        trussme.report_to_md(
            os.path.join(os.path.dirname(__file__), "joint_optim.md"),
            result_truss,
            goals,
        )

    def test_full_optimization(self):
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

        truss_from_commands.joints[8].loads[1] = -20000

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

        goals = trussme.Goals()

        x0, obj, con, gen, bnds = trussme.make_optimization_functions(
            truss_from_commands,
            goals,
            joint_coordinates=True,
            shape_parameters=True,
        )

        results = scipy.optimize.minimize(
            obj,
            x0,
            constraints=scipy.optimize.NonlinearConstraint(
                con, -numpy.inf, 0.0, keep_feasible=True
            ),
            bounds=scipy.optimize.Bounds(bnds[0], bnds[1], keep_feasible=True),
            method="trust-constr",
            options={"verbose": 2, "maxiter": 50},
        )

        result_truss = gen(results.x)
        result_truss.analyze()
        trussme.report_to_md(
            os.path.join(os.path.dirname(__file__), "full_optim.md"),
            result_truss,
            goals,
        )
